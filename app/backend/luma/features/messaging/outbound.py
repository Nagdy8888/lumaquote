"""Live WhatsApp and Telegram submission in three phases so no database lock is held across the network.

1. `begin` (inside the dispatcher's authorized transaction): the channel's live gate, recipient
   allowlist and, for WhatsApp only, the 24-hour service window are checked and the intent moves
   to `submitting`, then the transaction commits. Whatever is not permitted is `blocked` with a
   code, never queued again. Telegram has no service window; the bot can only reach users who
   started it, and the allowlist limits that further.
2. `submit` (no transaction): one submission through the channel's adapter (`provider.adapter`):
   Meta uploads the PDF then sends a document; Twilio sends a signed, expiring gateway link to the
   PDF; Telegram uploads the PDF with `sendDocument`. No provider offers an idempotency key, so the
   `submitting` marker is the only guard against a second submission, and an uncertain outcome is
   never retried.
3. `record` (new transaction): the outcome is stored as `submitted` (accepted, with the provider
   message id), `failed` (definitely not sent) or `unknown` (may have been sent). HTTP success is
   only acceptance; WhatsApp delivery and read state arrive later as receipts
   (`inbound.apply_status`). Telegram's Bot API has no receipts, so its sends stay `submitted`.

Boundary: ownership, approval, revision and freshness were rechecked in `begin`'s transaction.
A takeover after the `submitting` commit cannot recall a call already in flight; the message
may still reach the customer, which the audit trail and status make visible.
"""

import re

from luma.core.audit import audit
from luma.features.conversations.service import add_message
from luma.features.inventory import ledger
from luma.features.quotations.documents import stored_quotation_pdf

from . import provider
from .allowlist import allowed
from .errors import ProviderError

SAFE = re.compile(r"[^A-Za-z0-9._-]")


def release_hold(conn, item, reason: str) -> int:
    """Release the stock reservation of the quotation an outbox intent carries; return lines released.

    Does nothing for an intent without a quotation (a plain reply). The quotation row is locked
    first (lock order conversation, quote, stock levels, decision D49), then
    `ledger.release_quote` runs, which is idempotent. Call it only for a terminal outcome that
    proves the customer did not get the offer (`blocked`, definite `failed`), never for `unknown`,
    where the message may have been sent. The caller holds the conversation lock.
    """
    if not item["quote_id"]:
        return 0
    conn.execute(
        "select id from luma.quotes where company_id=%s and id=%s for update", (item["company_id"], item["quote_id"])
    )
    return ledger.release_quote(conn, item["company_id"], item["quote_id"], reason)


def block(conn, item, code: str) -> None:
    """Mark an intent blocked with an opaque code and audit it; a blocked intent is never retried.

    A blocked quotation also releases its stock reservation (reason `delivery_blocked`), because
    it can no longer reach the customer.
    """
    conn.execute(
        "update luma.outbox set status='blocked',error_code=%s,updated_at=now() where id=%s", (code, item["id"])
    )
    release_hold(conn, item, "delivery_blocked")
    audit(conn, item["company_id"], "worker", "delivery.blocked", item["id"])


def begin(conn, item, current, quote) -> dict | None:
    """Apply the live-send gates and mark the intent `submitting`; return the submission plan or None if blocked."""
    channel = current["channel"]
    if not (provider.live_enabled(channel) and provider.ready(channel)):
        block(conn, item, "live_adapter_not_enabled")
        return None
    recipient = current["recipient"]
    if recipient not in allowed(channel):
        block(conn, item, "recipient_not_allowed")
        return None
    if channel == "whatsapp":
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
    return {"item": item, "to": recipient, "quote": quote, "text": text, "channel": channel}


def submit(plan: dict) -> dict:
    """Perform the single network submission and classify the result without raising."""
    quote, sender = plan["quote"], provider.adapter(plan["channel"])
    try:
        if quote:
            filename = SAFE.sub("-", f"{quote['number']}-r{quote['revision']}")[:80] + ".pdf"
            try:
                document = stored_quotation_pdf(quote)
            except Exception:
                return {"status": "failed", "code": "document_unavailable"}
            sent = sender.send_pdf(plan["to"], document, filename, plan["text"], str(plan["item"]["id"]))
        else:
            sent = sender.send_text(plan["to"], plan["text"])
        return {"status": "submitted", "provider_id": sent}
    except ProviderError as error:
        return {"status": "unknown" if error.kind == "unknown" else "failed", "code": error.code}
    except Exception:
        return {"status": "unknown", "code": "internal_error"}


def record(conn, plan: dict, result: dict) -> None:
    """Persist the classified outcome; an accepted send also records the assistant/staff message once.

    A definite `failed` outcome of a quotation releases its stock reservation (reason
    `delivery_failed`) in the same transaction. `unknown` never does: the customer may have the
    offer, so the hold stays until the quotation expires or staff decide.
    """
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
    if updated and result["status"] == "failed":
        release_hold(conn, item, "delivery_failed")
    audit(conn, item["company_id"], "worker", f"delivery.{result['status']}", item["id"])
