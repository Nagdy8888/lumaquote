"""Pull-based email replies through Apps Script (decision D47).

The backend cannot send Gmail itself (D10: no backend Google login), so sending is pulled:

1. The dispatcher authorizes and gates an email outbox intent like any channel (`outbound.begin`:
   live switch, readiness, allowlisted recipient), marks it `submitting` and calls `queue`, which
   adds one `luma.email_dispatch` row (`waiting`) with the exact text, subject and the Gmail
   message to reply to, in the same transaction.
2. Apps Script calls `claim_mail` (signed). The oldest waiting row is leased for five minutes with
   a fresh claim token and returned with the text and, for a quotation, the canonical PDF.
3. Apps Script sends from Gmail and calls `record_mail_receipt` (signed) with `sent` (plus the Gmail
   message id when it can see it), or `failed` with a code. The outbox moves to `submitted` or `failed` through the
   shared `outbound.record`, which also records the assistant message once.

Duplicates: a row is claimed at most once (`attempts` 0..1). A claimed row whose lease expires
without a receipt becomes `unknown` (outbox `unknown`) and is never offered again, because the mail
may already have left Gmail. A row nobody claims within 24 hours becomes `failed` (`not_collected`).
A takeover after step 1 cannot recall the row, as with other channels.
"""

import base64
import hashlib
from typing import Literal
from uuid import UUID, uuid4

import psycopg
from pydantic import Field, model_validator

from luma.core.audit import audit
from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation
from luma.features.google_sync.exports import ExportEnvelope, drive_filename, record_nonce, verify_envelope
from luma.features.quotations.documents import stored_quotation_pdf

from .errors import ProviderError

LEASE_SECONDS = 300
MAX_PDF_BYTES = 5 * 1024 * 1024
ACTOR = "google-apps-script"


class MailClaim(ExportEnvelope):
    """Ask for the next reply to send; carries no dispatch identity of its own."""

    event: Literal["gmail_send_claim"]


class MailReceipt(ExportEnvelope):
    """Report the outcome of one claimed reply, bound by the opaque claim token issued with it."""

    event: Literal["gmail_send_receipt"]
    dispatch_id: UUID
    claim_token: UUID
    outcome: Literal["sent", "failed"]
    gmail_message_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{10,32}$")
    error_code: str | None = Field(default=None, max_length=30, pattern=r"^[a-z0-9_]+$")

    @model_validator(mode="after")
    def outcome_fields(self):
        """A failed receipt needs an error code; the Gmail id of a sent reply is optional (Gmail may not show it yet)."""
        if self.outcome == "failed" and not self.error_code:
            raise ValueError("A failed receipt needs error_code.")
        return self


def ready() -> bool:
    """True when the signed Apps Script connection is configured (secret, company and workbook)."""
    config = settings()
    return bool(
        len(config.google_callback_secret.get_secret_value()) >= 32
        and config.google_company_id
        and config.google_sheet_id
    )


def send_text(to: str, body: str) -> str:
    """Email is pulled by Apps Script; a direct send is a programming error, reported as a refusal."""
    raise ProviderError("rejected", "email_is_pulled")


def send_pdf(to: str, data: bytes, filename: str, caption: str, reference: str, buttons=None) -> str:
    """Email is pulled by Apps Script; a direct send is a programming error, reported as a refusal."""
    raise ProviderError("rejected", "email_is_pulled")


def reply_subject(subject: str) -> str:
    """Prefix `Re: ` once; an empty subject becomes a fixed one."""
    subject = subject.strip() or "Your lighting request"
    return subject if subject.lower().startswith("re:") else f"Re: {subject}"[:300]


def queue(conn, plan: dict) -> None:
    """Add the waiting dispatch row for a gated plan, replying to the customer's latest mail.

    Runs inside the dispatcher transaction that marked the outbox `submitting`. The subject and
    the Gmail message to reply to come from the newest stored mail from this recipient (also when
    it only produced a notice); without one the reply is a new mail with a fixed subject.
    """
    item = plan["item"]
    latest = conn.execute(
        """select payload from luma.inbox where company_id=%s and provider_id like 'gm:%%'
        and payload->>'from'=%s order by created_at desc limit 1""",
        (item["company_id"], plan["to"]),
    ).fetchone()
    payload = latest["payload"] if latest else {}
    conn.execute(
        """insert into luma.email_dispatch(outbox_id,company_id,recipient,subject,body,reply_message_id)
        values(%s,%s,%s,%s,%s,%s)""",
        (
            item["id"],
            item["company_id"],
            plan["to"],
            reply_subject(payload.get("subject", "")),
            plan["text"][:20000],
            payload.get("message_id"),
        ),
    )
    audit(conn, item["company_id"], "worker", "delivery.email_queued", item["id"])


def sweep(conn, company) -> None:
    """Expire leases (claimed -> unknown) and uncollected rows (24 h -> failed) and mirror them on the outbox.

    An uncollected quotation mail (`failed`) never left Gmail, so its stock reservation is released
    (reason `delivery_failed`, D49). An expired lease (`unknown`) may have been sent and keeps the hold.
    """
    from .outbound import release_hold  # outbound imports provider, which imports this module

    for status, code, condition in (
        ("unknown", "mail_receipt_missing", "status='claimed' and lease_until < now()"),
        ("failed", "mail_not_collected", "status='waiting' and created_at < now() - interval '24 hours'"),
    ):
        rows = conn.execute(
            f"""update luma.email_dispatch set status=%s,error_code=%s,claim_token=null,lease_until=null,
            updated_at=now() where company_id=%s and {condition} returning outbox_id""",
            (status, code, company),
        ).fetchall()
        for row in rows:
            item = conn.execute(
                """update luma.outbox set status=%s,error_code=%s,updated_at=now()
                where id=%s and status='submitting' returning id,company_id,quote_id""",
                (status, code, row["outbox_id"]),
            ).fetchone()
            if item and status == "failed":
                release_hold(conn, item, "delivery_failed")
            audit(conn, company, ACTOR, f"delivery.{status}", row["outbox_id"])


def claim_mail(body: bytes, signature: str) -> dict:
    """Lease the next waiting reply to Apps Script, or return `{"mail": None}` when nothing is due.

    The outbox must still be `submitting`; otherwise the row is failed (`outbox_changed`) and
    skipped. A quotation reply carries the canonical stored PDF (at most 5 MiB) and its SHA-256;
    a larger one fails the intent and releases the quotation's stock reservation (D49).
    """
    from .outbound import release_hold  # outbound imports provider, which imports this module

    claim = verify_envelope(MailClaim, body, signature)
    try:
        with database(worker=True) as conn:
            conn.execute("set local statement_timeout='20s'")
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (str(claim.company_id),))
            if not record_nonce(conn, claim, body):
                raise DomainError("This mail claim was already used.", 409)
            sweep(conn, claim.company_id)
            while True:
                row = conn.execute(
                    """select d.*, o.status as outbox_status, o.quote_id from luma.email_dispatch d
                    join luma.outbox o on o.id=d.outbox_id where d.company_id=%s and d.status='waiting'
                    order by d.created_at for update of d skip locked limit 1""",
                    (claim.company_id,),
                ).fetchone()
                if not row:
                    return {"mail": None}
                if row["outbox_status"] == "submitting":
                    break
                conn.execute(
                    """update luma.email_dispatch set status='failed',error_code='outbox_changed',updated_at=now()
                    where outbox_id=%s""",
                    (row["outbox_id"],),
                )
            attachment = None
            if row["quote_id"]:
                quote = conn.execute(
                    "select * from luma.quotes where company_id=%s and id=%s", (claim.company_id, row["quote_id"])
                ).fetchone()
                pdf = stored_quotation_pdf(quote)
                if len(pdf) > MAX_PDF_BYTES:
                    conn.execute(
                        """update luma.email_dispatch set status='failed',error_code='pdf_too_large',updated_at=now()
                        where outbox_id=%s""",
                        (row["outbox_id"],),
                    )
                    conn.execute(
                        "update luma.outbox set status='failed',error_code='pdf_too_large',updated_at=now() where id=%s",
                        (row["outbox_id"],),
                    )
                    release_hold(conn, {"company_id": claim.company_id, "quote_id": row["quote_id"]}, "delivery_failed")
                    return {"mail": None}
                attachment = {
                    "filename": drive_filename(quote),
                    "sha256": hashlib.sha256(pdf).hexdigest(),
                    "size": len(pdf),
                    "pdf_base64": base64.b64encode(pdf).decode("ascii"),
                }
            token = uuid4()
            conn.execute(
                """update luma.email_dispatch set status='claimed',attempts=attempts+1,claim_token=%s,
                lease_until=now()+make_interval(secs => %s),updated_at=now() where outbox_id=%s""",
                (token, LEASE_SECONDS, row["outbox_id"]),
            )
            return {
                "mail": {
                    "dispatch_id": str(row["outbox_id"]),
                    "claim_token": str(token),
                    "to": row["recipient"],
                    "subject": row["subject"],
                    "body": row["body"],
                    "reply_message_id": row["reply_message_id"],
                    "attachment": attachment,
                }
            }
    except psycopg.Error:
        raise DomainError("Mail dispatch storage is unavailable.", 503) from None


def record_mail_receipt(body: bytes, signature: str) -> dict:
    """Finish one claimed reply from Apps Script's signed outcome; an identical replay is idempotent.

    Only the current claim token may report. The outbox outcome is written through
    `outbound.record` under the conversation lock, as for every other channel.
    """
    from .outbound import record  # outbound imports provider, which imports this module

    receipt = verify_envelope(MailReceipt, body, signature)
    try:
        with database(worker=True) as conn:
            conn.execute("set local statement_timeout='10s'")
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (str(receipt.company_id),))
            record_nonce(conn, receipt, body)
            row = conn.execute(
                "select * from luma.email_dispatch where company_id=%s and outbox_id=%s for update",
                (receipt.company_id, receipt.dispatch_id),
            ).fetchone()
            if not row:
                raise DomainError("Mail dispatch not found.", 404)
            if row["status"] == "sent":
                if receipt.outcome == "sent" and row["claim_token"] is None:
                    return {"status": "sent"}
                raise DomainError("This mail was already reported.", 409)
            if row["status"] != "claimed" or row["claim_token"] != receipt.claim_token:
                raise DomainError("This mail claim is no longer current.", 409)
            item = conn.execute("select * from luma.outbox where id=%s", (row["outbox_id"],)).fetchone()
            conversation(conn, item["company_id"], item["conversation_id"], lock=True)
            quote = (
                conn.execute(
                    "select * from luma.quotes where company_id=%s and id=%s", (item["company_id"], item["quote_id"])
                ).fetchone()
                if item["quote_id"]
                else None
            )
            if receipt.outcome == "sent":
                # One provider id per reply, independent of what Gmail reported (ids may repeat or be absent).
                status, result = "sent", {"status": "submitted", "provider_id": f"gm-out:{row['outbox_id']}"}
            else:
                status, result = "failed", {"status": "failed", "code": f"gmail_{receipt.error_code}"[:40]}
            conn.execute(
                """update luma.email_dispatch set status=%s,gmail_message_id=%s,error_code=%s,claim_token=null,
                lease_until=null,updated_at=now() where outbox_id=%s""",
                (status, receipt.gmail_message_id, result.get("code"), row["outbox_id"]),
            )
            record(conn, {"item": item, "quote": quote, "text": row["body"]}, result)
            return {"status": status}
    except psycopg.Error:
        raise DomainError("Mail dispatch storage is unavailable.", 503) from None
