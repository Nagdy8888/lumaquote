"""Short-lived signed links that let Twilio fetch one approved quotation PDF from the gateway.

Twilio sends media only by URL, so the canonical PDF must be reachable through the tunnel for
the moment Twilio fetches it. The link names an outbox intent, not a quote or storage path,
and is valid only when all of these hold:

- the HMAC-SHA256 signature over `<outbox id>.<expiry>` matches (key derived from the Twilio
  Auth Token, so only this server and the account owner can mint one);
- the expiry (Unix seconds, at most `TTL_SECONDS` ahead) has not passed;
- the outbox intent belongs to the configured company, references a quote, and has already
  passed the dispatcher's authorization (`submitting` or a later submitted/delivered state).

The response is the stored canonical PDF (`stored_quotation_pdf`), byte-identical to staff
preview and Drive export. Failures return 404 without saying which check failed. No customer
data appears in the URL; the PDF itself is the customer-visible document.
"""

import hashlib
import hmac
import time
from uuid import UUID

import psycopg
from fastapi import APIRouter, Response
from starlette.concurrency import run_in_threadpool

from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.quotations.documents import stored_quotation_pdf

router = APIRouter()
TTL_SECONDS = 15 * 60
SENDABLE = ("submitting", "submitted", "unknown", "delivered", "read")


def key() -> bytes:
    """Derive the link-signing key from the Auth Token; refuses to sign or verify without one."""
    token = settings().twilio_auth_token.get_secret_value()
    if not token:
        raise DomainError("Media links are not configured.", 503)
    return hmac.new(token.encode(), b"luma-media-link-v1", hashlib.sha256).digest()


def signature(outbox_id: str, expires: int) -> str:
    """Hex HMAC over the canonical `<uuid>.<expiry>` string."""
    return hmac.new(key(), f"{outbox_id}.{expires}".encode(), hashlib.sha256).hexdigest()


def quotation_url(outbox_id: str, now: float | None = None) -> str:
    """Mint the public URL Twilio fetches for one outbox intent's PDF; expires after `TTL_SECONDS`."""
    canonical = str(UUID(str(outbox_id)))
    expires = int(now if now is not None else time.time()) + TTL_SECONDS
    base = settings().public_gateway_url
    return f"{base}/media/quotations/{canonical}/{expires}/{signature(canonical, expires)}/quotation.pdf"


def load_pdf(outbox_id: UUID) -> bytes | None:
    """Return the canonical PDF for an authorized, quote-bearing outbox intent of the configured company."""
    company = UUID(settings().whatsapp_company_id)
    try:
        with database(worker=True) as conn:
            quote = conn.execute(
                """select q.* from luma.outbox o join luma.quotes q on q.id=o.quote_id and q.company_id=o.company_id
                where o.id=%s and o.company_id=%s and o.status = any(%s)""",
                (outbox_id, company, list(SENDABLE)),
            ).fetchone()
    except psycopg.Error:
        raise DomainError("Media storage is unavailable.", 503) from None
    return stored_quotation_pdf(quote) if quote else None


@router.get("/media/quotations/{outbox_id}/{expires}/{supplied}/quotation.pdf")
async def quotation_pdf(outbox_id: UUID, expires: int, supplied: str):
    """Serve one PDF for a valid, unexpired signed link; every failed check is an opaque 404."""
    if not settings().whatsapp_company_id:
        raise DomainError("Not found.", 404)
    now = int(time.time())
    expected = signature(str(outbox_id), expires)
    if not (now <= expires <= now + TTL_SECONDS and hmac.compare_digest(expected, supplied)):
        raise DomainError("Not found.", 404)
    data = await run_in_threadpool(load_pdf, outbox_id)
    if data is None:
        raise DomainError("Not found.", 404)
    return Response(data, media_type="application/pdf", headers={"Cache-Control": "no-store"})
