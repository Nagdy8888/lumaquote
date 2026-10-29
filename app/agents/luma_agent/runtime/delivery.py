"""Outbox dispatch; uncertain external submissions never receive a blind retry."""

from luma.core.audit import audit
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.conversations.service import add_message
from luma.features.quotations.dispatch import dispatch_check


def deliver_one():
    """Deliver one local-test intent after final authorization, recording honest local-channel status."""
    with database(worker=True) as conn:
        conn.execute("""update luma.outbox set status='unknown',error_code='submission_interrupted'
            where status='submitting' and updated_at<now()-interval '2 minutes'""")
        item = conn.execute(
            "select * from luma.outbox where status='queued' order by created_at for update skip locked limit 1"
        ).fetchone()
        if not item:
            return False
        try:
            current, quote = dispatch_check(conn, item)
            if current["channel"] != "local_test":
                conn.execute(
                    "update luma.outbox set status='blocked',error_code='live_adapter_not_enabled',updated_at=now() where id=%s",
                    (item["id"],),
                )
                audit(conn, item["company_id"], "worker", "delivery.blocked", item["id"])
                return True
        except DomainError:
            conn.execute(
                "update luma.outbox set status='blocked',error_code='dispatch_revalidation',updated_at=now() where id=%s",
                (item["id"],),
            )
            audit(conn, item["company_id"], "worker", "delivery.blocked", item["id"])
            return True
        text = (
            item["payload"].get("text")
            if not quote
            else f"{quote['number']}, revision {quote['revision']}, is available in the local test channel. Total USD {quote['content']['total']}."
        )
        # Message identity is tied to the outbox intent; one database transaction
        # contains the local-channel effect and completion.
        provider_id = f"local:{item['id']}"
        add_message(
            conn,
            item["company_id"],
            item["conversation_id"],
            "assistant",
            text,
            kind="document" if quote else "text",
            provider_id=provider_id,
        )
        conn.execute(
            "update luma.outbox set status='local_delivered',provider_id=%s,updated_at=now() where id=%s",
            (provider_id, item["id"]),
        )
        if quote:
            conn.execute(
                "update luma.conversations set status='quoted',updated_at=now() where id=%s",
                (item["conversation_id"],),
            )
        audit(conn, item["company_id"], "worker", "delivery.local_delivered", item["id"])
        return True
