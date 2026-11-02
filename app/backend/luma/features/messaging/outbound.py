"""Live WhatsApp submission in three phases so no database lock is held across the network.

1. `begin` (inside the dispatcher's authorized transaction): the live gate, recipient allowlist
   and 24-hour service window are checked and the intent moves to `submitting`, then the
   transaction commits. Whatever is not permitted is `blocked` with a code, never queued again.
2. `submit` (no transaction): one Graph call (a text message, or a PDF upload then a document
   message). There is no provider idempotency key, so the `submitting` marker is the only
   guard against a second submission, and an uncertain outcome is never retried.
3. `record` (new transaction): the outcome is stored as `submitted` (accepted, with the WhatsApp
   message id), `failed` (definitely not sent) or `unknown` (may have been sent). HTTP success is
   only acceptance; delivery and read state arrive later as receipts (`inbound.apply_status`).

Boundary: ownership, approval, revision and freshness were rechecked in `begin`'s transaction.
A takeover after the `submitting` commit cannot recall a call already in flight; the message
may still reach the customer, which the audit trail and status make visible.
"""

import re

from luma.core.audit import audit
from luma.core.config import settings
from luma.features.conversations.service import add_message
from luma.features.quotations.documents import stored_quotation_pdf

from .allowlist import allowed_senders
from .whatsapp_client import GraphError, send_document, send_text, upload_pdf

SAFE = re.compile(r"[^A-Za-z0-9._-]")


def block(conn, item, code: str) -> None:
    """Mark an intent blocked with an opaque code and audit it; a blocked intent is never retried."""
    conn.execute(
        "update luma.outbox set status='blocked',error_code=%s,updated_at=now() where id=%s", (code, item["id"])
    )
    audit(conn, item["company_id"], "worker", "delivery.blocked", item["id"])


def begin(conn, item, current, quote) -> dict | None:
    """Apply the live-send gates and mark the intent `submitting`; return the submission plan or None if blocked."""
    config = settings()
    if not (
        config.enable_live_whatsapp and config.whatsapp_token.get_secret_value() and config.whatsapp_phone_id
    ):
        block(conn, item, "live_adapter_not_enabled")
        return None
    recipient = current["recipient"]
    if recipient not in allowed_senders():
        block(conn, item, "recipient_not_allowed")
        return None
    window = conn.execute(
        "select now() - last_customer_at > interval '24 hours' as closed from luma.conversations where id=%s",
        (current["id"],),
    ).fetchone()
    if window["closed"]:
        block(conn, item, "outside_service_window")
        return None
    conn.execute("update luma.outbox set status='submitting',updated_at=now() where id=%s", (item["id"],))
    audit(conn, item["company_id"], "worker", "delivery.submitting", item["id"])
    text = item["payload"].get("text")
    if quote:
        text = (
            f"Quotation {quote['number']}, revision {quote['revision']}. "
            f"Total USD {quote['content']['total']} (tax excluded). Staff-approved; valid until "
            f"{quote['valid_until'].strftime('%d %b %Y')}."
        )
    return {"item": item, "to": recipient, "quote": quote, "text": text}


def submit(plan: dict) -> dict:
    """Perform the single network submission and classify the result without raising."""
    quote = plan["quote"]
    try:
        if quote:
            filename = SAFE.sub("-", f"{quote['number']}-r{quote['revision']}")[:80] + ".pdf"
            try:
                media = upload_pdf(stored_quotation_pdf(quote), filename)
            except GraphError as error:
                return {"status": "failed", "code": f"upload_{error.code}"[:40]}
            except Exception:
                return {"status": "failed", "code": "document_unavailable"}
            wamid = send_document(plan["to"], media, filename, plan["text"])
        else:
            wamid = send_text(plan["to"], plan["text"])
        return {"status": "submitted", "provider_id": wamid}
    except GraphError as error:
        return {"status": "unknown" if error.kind == "unknown" else "failed", "code": error.code}
    except Exception:
        return {"status": "unknown", "code": "internal_error"}


def record(conn, plan: dict, result: dict) -> None:
    """Persist the classified outcome; an accepted send also records the assistant/staff message once."""
    item, quote = plan["item"], plan["quote"]
    updated = conn.execute(
        """update luma.outbox set status=%s,provider_id=%s,error_code=%s,updated_at=now()
        where id=%s and status in ('submitting','unknown') returning id""",
        (result["status"], result.get("provider_id"), result.get("code"), item["id"]),
    ).fetchone()
    if updated and result["status"] == "submitted":
        add_message(
            conn,
            item["company_id"],
            item["conversation_id"],
            "staff" if item["payload"].get("origin") == "staff" else "assistant",
            plan["text"],
            kind="document" if quote else "text",
            provider_id=result["provider_id"],
        )
        if quote:
            conn.execute(
                "update luma.conversations set status='quoted',updated_at=now() where id=%s",
                (item["conversation_id"],),
            )
    audit(conn, item["company_id"], "worker", f"delivery.{result['status']}", item["id"])
