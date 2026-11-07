"""Outbox dispatch; uncertain external submissions never receive a blind retry."""

from luma.core.audit import audit
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation
from luma.features.conversations.service import add_message
from luma.features.messaging.authorization import authorize_outbound
from luma.features.messaging.outbound import begin, record, submit


def deliver_one(company_id=None):
    """Resolve one queued intent and apply only the implemented local-channel effect.

    The optional company scope is trusted test control, not client authority.
    Reclassify old submitting outcomes as unknown, then lock conversation before
    outbox and reauthorize origin/ownership/approval/freshness. Ineligible or
    nonlocal work is visibly blocked. Local message identity derives from the
    intent, and message plus local_delivered status commit together. Return True
    when an intent was handled (including blocked), False when none was selected;
    neither value is a live provider receipt or an instruction to retry unknowns.
    """
    with database(worker=True) as conn:
        conn.execute(
            """update luma.outbox set status='unknown',error_code='submission_interrupted',updated_at=now()
            where status='submitting' and updated_at<now()-interval '2 minutes'
            and (%s::uuid is null or company_id=%s)""",
            (company_id, company_id),
        )
        candidate = conn.execute(
            "select id,company_id,conversation_id from luma.outbox where status='queued' and (%s::uuid is null or company_id=%s) order by created_at limit 1",
            (company_id, company_id),
        ).fetchone()
        if not candidate:
            return False
        # Every edit/approval/takeover takes the conversation lock first. The
        # dispatcher follows that same order to avoid C->O / O->C deadlocks.
        conversation(conn, candidate["company_id"], candidate["conversation_id"], lock=True)
        item = conn.execute(
            "select * from luma.outbox where id=%s and status='queued' for update skip locked",
            (candidate["id"],),
        ).fetchone()
        if item is None:
            return False
        plan = None
        try:
            current, quote = authorize_outbound(conn, item)
            if current["channel"] in ("whatsapp", "telegram"):
                # Authorized and gated under the conversation lock; the network call
                # happens after this transaction commits (see messaging.outbound).
                plan = begin(conn, item, current, quote)
                if plan is None:
                    return True
            elif current["channel"] != "local_test":
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
        if plan is None:
            return _deliver_local(conn, item, quote)
    result = submit(plan)
    with database(worker=True) as conn:
        conversation(conn, item["company_id"], item["conversation_id"], lock=True)
        record(conn, plan, result)
    return True


def _deliver_local(conn, item, quote):
    """Apply the local-test channel effect and completion in the caller's transaction; True when handled."""
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
        "staff" if item["payload"].get("origin") == "staff" else "assistant",
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
