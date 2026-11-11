"""Pull-based Google Sheets stock export for Google Apps Script (decision D49, task T5).

A staff member presses "Export to Google Sheets" in the web app, which queues one
`luma.sheet_exports` row (`inventory/sheet_queue.py`). Apps Script cannot be called by the backend
(no public web app is deployed, D10), so its minute timer polls: it claims the queued export, writes
the `Stock`, `Customer Orders` and `Purchase Orders` tabs of the configured workbook, and posts a
receipt with the row counts. This is the same signed protocol as the Drive export in `exports.py`
and reuses its envelope, signature, nonce, five-minute window, company and workbook binding.

Trust model: a signed request can only claim or complete exports of the one configured company.
The claim response carries read-only table values already passed through `safe_text`; the receipt
carries counts and a short error code, never cell contents. Neither endpoint can change stock,
orders, quotations or approvals.
"""

from typing import Annotated, Literal
from uuid import UUID, uuid4

import psycopg
from psycopg.types.json import Jsonb
from pydantic import Field, model_validator

from luma.core.audit import audit
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.inventory import exports as stock_tables

from .exports import ACTOR, LEASE_SECONDS, MAX_ATTEMPTS, ExportEnvelope, record_nonce, verify_envelope

TabName = Literal["Stock", "Customer Orders", "Purchase Orders"]
RowCount = Annotated[int, Field(strict=True, ge=0, le=stock_tables.SHEET_ROW_CAP)]


class StockClaimRequest(ExportEnvelope):
    """Ask for the next queued stock export; carries no export identity of its own."""

    event: Literal["stock_export_claim"]


class StockReceiptRequest(ExportEnvelope):
    """Report the outcome of one claimed stock export, bound by the opaque claim token issued with it."""

    event: Literal["stock_export_receipt"]
    export_id: UUID
    claim_token: UUID
    outcome: Literal["stored", "failed"]
    row_counts: dict[TabName, RowCount] | None = None
    error_code: str | None = Field(default=None, max_length=40, pattern=r"^[a-z0-9_]+$")

    @model_validator(mode="after")
    def outcome_fields(self):
        """Require data rows counts for every tab on a stored receipt and an error code on a failure."""
        if self.outcome == "stored" and (not self.row_counts or set(self.row_counts) != set(stock_tables.SHEET_TABS)):
            raise ValueError("A stored receipt needs a row count for each of the three tabs.")
        if self.outcome == "failed" and not self.error_code:
            raise ValueError("A failed receipt needs an error_code.")
        return self


def claim_stock_export(body: bytes, signature: str) -> dict:
    """Lease the oldest queued stock export to Apps Script, or return `{"status": "idle"}` when none is due.

    Eligible rows are queued, or claimed with an expired lease (a crashed or silent client), and
    have used fewer than `MAX_ATTEMPTS` attempts. A claimed row whose lease expired at the limit
    is set to `failed` (`attempts_exhausted`) here. A claim increments attempts, issues a fresh
    claim token and a five-minute lease, so the previous holder's receipt is rejected as stale.
    The response is `{"status": "claimed", "export_id", "claim_token", "tabs": {name: [header_row,
    *rows]}, "truncated": [tab names cut at 5000 rows]}`; the tab values are guarded text, ints
    and floats only. A lost response just lets the lease expire for the next poll. A replayed
    claim nonce is refused with 409 so a captured request cannot lease another export.
    """
    claim = verify_envelope(StockClaimRequest, body, signature)
    try:
        with database(worker=True) as conn:
            conn.execute("set local statement_timeout='20s'")
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (str(claim.company_id),))
            if not record_nonce(conn, claim, body):
                raise DomainError("This export claim was already used.", 409)
            expired = conn.execute(
                """update luma.sheet_exports set status='failed',error_code='attempts_exhausted',
                claim_token=null,lease_until=null,completed_at=now()
                where company_id=%s and status='claimed' and lease_until < now() and attempts >= %s
                returning id""",
                (claim.company_id, MAX_ATTEMPTS),
            ).fetchall()
            for row in expired:
                audit(conn, claim.company_id, ACTOR, "inventory.sheet_export_failed", row["id"], reason="attempts_exhausted")
            row = conn.execute(
                """select id from luma.sheet_exports where company_id=%s and attempts < %s
                and (status='queued' or (status='claimed' and lease_until < now()))
                order by created_at for update skip locked limit 1""",
                (claim.company_id, MAX_ATTEMPTS),
            ).fetchone()
            if not row:
                return {"status": "idle"}
            tables = stock_tables.collect(
                conn, claim.company_id, stock_tables.SHEET_TABS, stock_tables.SHEET_ROW_CAP
            )
            token = uuid4()
            conn.execute(
                """update luma.sheet_exports set status='claimed',attempts=attempts+1,claim_token=%s,
                lease_until=now()+make_interval(secs => %s),error_code=null where id=%s""",
                (token, LEASE_SECONDS, row["id"]),
            )
            return {
                "status": "claimed",
                "export_id": str(row["id"]),
                "claim_token": str(token),
                "tabs": stock_tables.sheet_payload(tables),
                "truncated": [name for name, table in tables.items() if table.truncated],
            }
    except psycopg.Error:
        raise DomainError("Export storage is unavailable.", 503) from None


def record_stock_receipt(body: bytes, signature: str) -> dict:
    """Finish or retry one claimed stock export from Apps Script's signed outcome; replays are idempotent.

    Only the current claim token may report. `stored` marks the export `done` with its row counts
    and a completion time. `failed` records the error code and requeues the export for another
    poll, or sets it to `failed` once `MAX_ATTEMPTS` attempts are used. An identical `stored`
    receipt for an already `done` export returns `{"status": "done"}`; any other receipt for a
    finished or re-leased export is a 409. Side effects: one update and one audit event
    (`inventory.sheet_exported` or `inventory.sheet_export_failed`, counts and codes only).
    """
    receipt = verify_envelope(StockReceiptRequest, body, signature)
    try:
        with database(worker=True) as conn:
            conn.execute("set local statement_timeout='5s'")
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (str(receipt.company_id),))
            record_nonce(conn, receipt, body)
            row = conn.execute(
                "select * from luma.sheet_exports where company_id=%s and id=%s for update",
                (receipt.company_id, receipt.export_id),
            ).fetchone()
            if not row:
                raise DomainError("Export not found.", 404)
            if row["status"] == "done":
                if receipt.outcome == "stored" and row["row_counts"] == receipt.row_counts:
                    return {"status": "done"}
                raise DomainError("This export is already complete.", 409)
            if row["status"] != "claimed" or row["claim_token"] != receipt.claim_token:
                raise DomainError("This export claim is no longer current.", 409)
            if receipt.outcome == "stored":
                conn.execute(
                    """update luma.sheet_exports set status='done',row_counts=%s,completed_at=now(),
                    error_code=null,claim_token=null,lease_until=null where id=%s""",
                    (Jsonb(receipt.row_counts), row["id"]),
                )
                audit(conn, receipt.company_id, ACTOR, "inventory.sheet_exported", row["id"], rows=receipt.row_counts)
                return {"status": "done"}
            exhausted = row["attempts"] >= MAX_ATTEMPTS
            status = "failed" if exhausted else "queued"
            conn.execute(
                """update luma.sheet_exports set status=%s,error_code=%s,claim_token=null,lease_until=null,
                completed_at=case when %s then now() else null end where id=%s""",
                (status, receipt.error_code, exhausted, row["id"]),
            )
            audit(
                conn,
                receipt.company_id,
                ACTOR,
                "inventory.sheet_export_failed",
                row["id"],
                reason=receipt.error_code,
                status=status,
            )
            return {"status": status}
    except psycopg.Error:
        raise DomainError("Export storage is unavailable.", 503) from None
