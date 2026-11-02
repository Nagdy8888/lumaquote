"""Pull-based Drive export protocol for Google Apps Script.

Apps Script cannot be called by the backend (no public web app is deployed), so it
polls: it claims the next approved quotation PDF, files it in a private Drive folder,
reads the Drive copy back and reports the SHA-256 it observed. The backend marks an
export done only when that digest equals the digest of the canonical stored PDF.

Trust model: every request is an HMAC-signed, five-minute, nonce-protected envelope
bound to the configured company and workbook (the same envelope rules as supplier
callbacks). A signed request can only claim or confirm exports of that one company;
it cannot read other records, change a quotation, or approve or send anything.
"""

import base64
import hashlib
import re
from typing import Literal
from uuid import UUID, uuid4

import psycopg
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from luma.core.audit import audit
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.quotations.documents import stored_quotation_pdf

from .callbacks import verify_mapping, verify_signature

MAX_ATTEMPTS = 5
LEASE_SECONDS = 300
MAX_PDF_BYTES = 5 * 1024 * 1024
ACTOR = "google-apps-script"
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")


class ExportEnvelope(BaseModel):
    """Common signed envelope fields; unknown fields are rejected so nothing unreviewed is accepted."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    company_id: UUID
    spreadsheet_id: str = Field(min_length=1, max_length=128)
    timestamp: int
    nonce: UUID


class ClaimRequest(ExportEnvelope):
    """Ask for the next exportable quotation PDF; carries no export identity of its own."""

    event: Literal["drive_export_claim"]


class ReceiptRequest(ExportEnvelope):
    """Report the outcome of one claimed export, bound by the opaque claim token issued with it."""

    event: Literal["drive_export_receipt"]
    export_id: UUID
    claim_token: UUID
    outcome: Literal["stored", "failed"]
    drive_file_id: str | None = Field(default=None, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    size: int | None = Field(default=None, gt=0, le=MAX_PDF_BYTES)
    error_code: str | None = Field(default=None, max_length=40, pattern=r"^[a-z0-9_]+$")

    @model_validator(mode="after")
    def outcome_fields(self):
        """Require Drive identity and digest for a stored copy and an error code for a failure."""
        if self.outcome == "stored" and not (self.drive_file_id and self.sha256 and self.size):
            raise ValueError("A stored receipt needs drive_file_id, sha256 and size.")
        if self.outcome == "failed" and not self.error_code:
            raise ValueError("A failed receipt needs an error_code.")
        return self


def verify_envelope(model, body: bytes, signature: str):
    """Authenticate exact bytes, validate the schema, then bind company, workbook and timestamp."""
    verify_signature(body, signature)
    try:
        envelope = model.model_validate_json(body)
    except ValidationError:
        raise DomainError("Invalid Google export payload.", 422) from None
    verify_mapping(envelope)
    return envelope


def record_nonce(conn, envelope, body: bytes) -> bool:
    """Persist the nonce once per company; return False for an identical replay, raise on a changed body.

    The caller holds the company advisory lock. Rows older than ten minutes are
    pruned, which is longer than the five-minute timestamp window, so a replay
    inside the window is always detected. At most 120 new envelopes per minute
    are accepted per company, bounding export polling and abuse.
    """
    fingerprint = hashlib.sha256(body).hexdigest()
    conn.execute("delete from luma.google_edit_receipts where received_at < now()-interval '10 minutes'")
    old = conn.execute(
        "select fingerprint from luma.google_edit_receipts where company_id=%s and nonce=%s",
        (envelope.company_id, envelope.nonce),
    ).fetchone()
    if old:
        if old["fingerprint"] != fingerprint:
            raise DomainError("Callback nonce already used with different content.", 409)
        return False
    count = conn.execute(
        "select count(*) n from luma.google_edit_receipts where company_id=%s and received_at > now()-interval '1 minute'",
        (envelope.company_id,),
    ).fetchone()["n"]
    if count >= 120:
        raise DomainError("Google callback rate exceeded.", 429)
    conn.execute(
        "insert into luma.google_edit_receipts(company_id,nonce,fingerprint) values(%s,%s,%s)",
        (envelope.company_id, envelope.nonce, fingerprint),
    )
    return True


def drive_filename(quote: dict) -> str:
    """Build a Drive-safe name from the quote number and revision; the export id travels separately."""
    return SAFE_NAME.sub("-", f"{quote['number']}-r{quote['revision']}")[:80] + ".pdf"


def claim_export(body: bytes, signature: str) -> dict:
    """Lease the next exportable PDF to Apps Script, or return `{"export": None}` when nothing is due.

    Eligible rows are queued, or claimed with an expired lease (a crashed or silent
    client), and have used fewer than five attempts. Expired rows already at the
    limit are blocked here. A claim increments attempts, issues a fresh claim token
    and a five-minute lease, so the previous holder's receipt is rejected as stale.
    The canonical stored PDF is read (or created once) from the immutable quote; its
    digest is pinned on first claim and a later difference blocks the export instead
    of shipping changed bytes. A claimed row is returned in the response only; a lost
    response simply lets the lease expire and the next poll reclaim it.
    """
    claim = verify_envelope(ClaimRequest, body, signature)
    try:
        with database(worker=True) as conn:
            conn.execute("set local statement_timeout='20s'")
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (str(claim.company_id),))
            if not record_nonce(conn, claim, body):
                raise DomainError("This export claim was already used.", 409)
            conn.execute(
                """update luma.drive_exports set status='blocked',error_code='attempts_exhausted',updated_at=now()
                where company_id=%s and status='claimed' and lease_until < now() and attempts >= %s""",
                (claim.company_id, MAX_ATTEMPTS),
            )
            row = conn.execute(
                """select * from luma.drive_exports where company_id=%s and attempts < %s
                and (status='queued' or (status='claimed' and lease_until < now()))
                order by created_at for update skip locked limit 1""",
                (claim.company_id, MAX_ATTEMPTS),
            ).fetchone()
            if not row:
                return {"export": None}
            quote = conn.execute(
                "select * from luma.quotes where company_id=%s and id=%s", (claim.company_id, row["quote_id"])
            ).fetchone()
            pdf = stored_quotation_pdf(quote)
            digest = hashlib.sha256(pdf).hexdigest()
            if len(pdf) > MAX_PDF_BYTES or (row["pdf_sha256"] and row["pdf_sha256"] != digest):
                reason = "pdf_too_large" if len(pdf) > MAX_PDF_BYTES else "pdf_changed"
                conn.execute(
                    "update luma.drive_exports set status='blocked',error_code=%s,updated_at=now() where id=%s",
                    (reason, row["id"]),
                )
                audit(conn, claim.company_id, ACTOR, "drive_export.blocked", row["quote_id"], reason=reason)
                return {"export": None}
            token = uuid4()
            conn.execute(
                """update luma.drive_exports set status='claimed',attempts=attempts+1,claim_token=%s,
                lease_until=now()+make_interval(secs => %s),pdf_sha256=%s,pdf_size=%s,error_code=null,updated_at=now()
                where id=%s""",
                (token, LEASE_SECONDS, digest, len(pdf), row["id"]),
            )
            return {
                "export": {
                    "export_id": str(row["id"]),
                    "claim_token": str(token),
                    "filename": drive_filename(quote),
                    "sha256": digest,
                    "size": len(pdf),
                    "pdf_base64": base64.b64encode(pdf).decode("ascii"),
                }
            }
    except psycopg.Error:
        raise DomainError("Export storage is unavailable.", 503) from None


def record_receipt(body: bytes, signature: str) -> dict:
    """Finish or retry one claimed export from Apps Script's signed outcome; replays are idempotent.

    Only the current claim token may report. A `stored` outcome is accepted solely
    when the Drive file's digest and size equal the canonical PDF pinned at claim
    time; otherwise the Drive copy is not identical, the attempt is recorded as
    failed and the same bounded retry path applies (queued, then blocked after five
    attempts). A failed outcome follows that retry path directly. Receipt
    acceptance is not delivery: it never touches the quotation, approval or outbox.
    """
    receipt = verify_envelope(ReceiptRequest, body, signature)
    try:
        with database(worker=True) as conn:
            conn.execute("set local statement_timeout='5s'")
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (str(receipt.company_id),))
            record_nonce(conn, receipt, body)
            row = conn.execute(
                "select * from luma.drive_exports where company_id=%s and id=%s for update",
                (receipt.company_id, receipt.export_id),
            ).fetchone()
            if not row:
                raise DomainError("Export not found.", 404)
            if row["status"] == "done":
                if receipt.outcome == "stored" and row["drive_file_id"] == receipt.drive_file_id:
                    return {"status": "done"}
                raise DomainError("This export is already complete.", 409)
            if row["status"] != "claimed" or row["claim_token"] != receipt.claim_token:
                raise DomainError("This export claim is no longer current.", 409)
            reason = receipt.error_code if receipt.outcome == "failed" else None
            if receipt.outcome == "stored" and (
                receipt.sha256 != row["pdf_sha256"] or receipt.size != row["pdf_size"]
            ):
                reason = "digest_mismatch"
            if reason:
                status = "blocked" if row["attempts"] >= MAX_ATTEMPTS else "queued"
                conn.execute(
                    """update luma.drive_exports set status=%s,error_code=%s,claim_token=null,lease_until=null,
                    updated_at=now() where id=%s""",
                    (status, reason, row["id"]),
                )
                audit(
                    conn,
                    receipt.company_id,
                    ACTOR,
                    "drive_export.failed",
                    row["quote_id"],
                    reason=reason,
                    status=status,
                )
                mismatch = reason == "digest_mismatch"
                result = {"status": status}
            else:
                conn.execute(
                    """update luma.drive_exports set status='done',drive_file_id=%s,completed_at=now(),
                    error_code=null,claim_token=null,lease_until=null,updated_at=now() where id=%s""",
                    (receipt.drive_file_id, row["id"]),
                )
                audit(
                    conn,
                    receipt.company_id,
                    ACTOR,
                    "drive_export.done",
                    row["quote_id"],
                    revision=row["revision"],
                )
                mismatch, result = False, {"status": "done"}
    except psycopg.Error:
        raise DomainError("Export storage is unavailable.", 503) from None
    # Raised after the transaction commits so the recorded failure and retry state persist.
    if mismatch:
        raise DomainError("The Drive copy differs from the canonical PDF.", 422)
    return result
