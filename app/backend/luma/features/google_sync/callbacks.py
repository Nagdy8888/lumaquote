"""Verify bounded signed hints before durably recording a pending refresh."""

import hashlib
import hmac
import time
from typing import Literal
from uuid import UUID

import psycopg
from pydantic import BaseModel, ConfigDict, ValidationError

from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError


class EditHint(BaseModel):
    """Versioned invalidation only; no supplied cell data can change commercial records."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    company_id: UUID
    spreadsheet_id: str
    timestamp: int
    nonce: UUID
    event: Literal["supplier_records_changed"]


def verify_signature(body: bytes, signature: str) -> None:
    """Authenticate exact bytes using the private company integration key; reject unconfigured receivers."""
    config = settings()
    secret = config.google_callback_secret.get_secret_value()
    if len(secret) < 32 or not config.google_company_id or not config.google_sheet_id:
        raise DomainError("Google callback is not configured.", 503)
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise DomainError("Invalid Google callback signature.", 401)


def verify_mapping(hint) -> None:
    """Bind a validated signed envelope to configured company/workbook and a five-minute timestamp window."""
    config = settings()
    if str(hint.company_id) != config.google_company_id or hint.spreadsheet_id != config.google_sheet_id:
        raise DomainError("Google callback mapping mismatch.", 403)
    if abs(time.time() - hint.timestamp) > 300:
        raise DomainError("Expired Google callback.", 401)


def verify_hint(body: bytes, signature: str) -> EditHint:
    """Authenticate and validate an invalidation envelope without trusting its company identity."""
    verify_signature(body, signature)
    try:
        hint = EditHint.model_validate_json(body)
    except ValidationError:
        raise DomainError("Invalid Google callback payload.", 422) from None
    verify_mapping(hint)
    return hint


def accept_hint(hint: EditHint, body: bytes) -> None:
    """Commit replay-safe receipts and one coalesced refresh signal; cap at 120 new hints/minute.

    A receipt acknowledges invalidation, never a completed Sheet import. Database
    failure denies acceptance. The company lock serializes duplicate/rate decisions.
    """
    fingerprint = hashlib.sha256(body).hexdigest()
    try:
        with database(worker=True) as conn:
            conn.execute("set local statement_timeout='5s'")
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (str(hint.company_id),))
            conn.execute(
                "delete from luma.google_edit_receipts where received_at < now()-interval '10 minutes'"
            )
            old = conn.execute(
                "select fingerprint from luma.google_edit_receipts where company_id=%s and nonce=%s",
                (hint.company_id, hint.nonce),
            ).fetchone()
            if old:
                if old["fingerprint"] != fingerprint:
                    raise DomainError("Callback nonce already used with different content.", 409)
                return
            count = conn.execute(
                "select count(*) n from luma.google_edit_receipts where company_id=%s "
                "and received_at > now()-interval '1 minute'",
                (hint.company_id,),
            ).fetchone()["n"]
            if count >= 120:
                raise DomainError("Google callback rate exceeded.", 429)
            conn.execute(
                "insert into luma.google_edit_receipts(company_id,nonce,fingerprint) values(%s,%s,%s)",
                (hint.company_id, hint.nonce, fingerprint),
            )
            conn.execute(
                "insert into luma.google_refresh_signals(company_id,spreadsheet_id) values(%s,%s) "
                "on conflict(company_id) do update set requested_at=now(),spreadsheet_id=excluded.spreadsheet_id",
                (hint.company_id, hint.spreadsheet_id),
            )
    except psycopg.Error:
        raise DomainError("Google callback storage is unavailable.", 503) from None
