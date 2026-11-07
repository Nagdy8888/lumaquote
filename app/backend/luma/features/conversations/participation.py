"""Staff/customer participation and ownership transitions, independent of HTTP transport."""

from uuid import uuid4

from psycopg.types.json import Jsonb

from luma.core.admission import enqueue, rate_limit
from luma.core.audit import audit
from luma.core.errors import DomainError
from luma.features.inventory import ledger
from luma.features.workspace.queries import detail

from .repository import conversation
from .schemas import Ownership, StaffReply, TextInput
from .service import add_message


def record_note(conn, member, user, cid, body: TextInput):
    """Persist a scoped staff-only note; it cannot impersonate the customer or create external dispatch intent."""
    conversation(conn, member["company_id"], cid, lock=True)
    add_message(conn, member["company_id"], cid, "staff", body.text)
    audit(conn, member["company_id"], user, "staff.note_added", cid)
    return detail(conn, member["company_id"], cid)


def accept_customer_text(conn, company, current, text, *, provider_id=None):
    """Append one customer text to a locked conversation, supersede affected offers and enqueue permitted automation.

    Shared by the staff-operated local-test reply and the verified WhatsApp ingress, so both
    invalidate old approvals/queued sends identically. The caller holds the conversation lock
    and has authorized the sender. A `provider_id` already seen returns False with no effect
    (provider redelivery); otherwise True. Under staff ownership the message is recorded and
    the conversation marked for staff, but no agent job is queued. Every quotation this
    supersedes releases its stock reservation (reason `superseded`, decision D49) in the same
    transaction, under the caller's conversation lock.
    """
    cid = current["id"]
    rate_limit(conn, f"conversation:{cid}", 6)
    if add_message(conn, company, cid, "customer", text, provider_id=provider_id) is None:
        return False
    conn.execute(
        "update luma.conversations set last_customer_at=now(),status=%s where id=%s",
        ("new" if current["owner"] == "agent" else "needs_staff", cid),
    )
    superseded = conn.execute(
        "update luma.quotes set status='superseded' where conversation_id=%s and status in ('review','approved') returning id",
        (cid,),
    ).fetchall()
    for row in superseded:
        ledger.release_quote(conn, company, row["id"], "superseded")
    conn.execute(
        "update luma.outbox set status='blocked',error_code='customer_revision',updated_at=now() where conversation_id=%s and status='queued'",
        (cid,),
    )
    if current["owner"] == "agent":
        enqueue(conn, company, cid)
    return True


def record_customer_reply(conn, member, user, cid, body: TextInput):
    """Accept only a staff-operated local-test reply, supersede affected offers, and enqueue permitted preparation atomically."""
    company = member["company_id"]
    current = conversation(conn, company, cid, lock=True)
    if current["channel"] != "local_test":
        raise DomainError("Simulated customer replies are only available in the local test channel.", 403)
    accept_customer_text(conn, company, current, body.text)
    audit(conn, company, user, "customer.test_reply_added", cid)
    return detail(conn, company, cid)


def change_ownership(conn, member, user, cid, body: Ownership):
    """Version-check human takeover/resume, blocking queued automation before releasing the conversation lock.

    Takeover also releases the stock reservation of every quotation whose queued send it blocked
    (reason `staff_takeover`, decision D49): that offer can no longer reach the customer, and
    the hold must not outlive it. An already-submitted send is untouched and keeps its hold.
    """
    company = member["company_id"]
    current = conversation(conn, company, cid, lock=True)
    if current["version"] != body.expected_version:
        raise DomainError("Conversation changed. Refresh before changing ownership.")
    conn.execute(
        "update luma.conversations set owner=%s,version=version+1,updated_at=now() where id=%s",
        (body.owner, cid),
    )
    if body.owner == "staff":
        blocked = conn.execute(
            "update luma.outbox set status='blocked',error_code='staff_takeover',updated_at=now() where conversation_id=%s and status='queued' and (payload->>'origin') is distinct from 'staff' returning quote_id",
            (cid,),
        ).fetchall()
        # A quotation whose queued send was just blocked will never go out, so its hold is freed
        # now instead of waiting for the worker's reconcile. Quote ids are released in sorted order.
        for quote_id in sorted({row["quote_id"] for row in blocked if row["quote_id"]}, key=str):
            ledger.release_quote(conn, company, quote_id, "staff_takeover")
    else:
        conn.execute(
            "update luma.outbox set status='blocked',error_code='ownership_changed',updated_at=now() where conversation_id=%s and status='queued' and payload->>'origin'='staff'",
            (cid,),
        )
    if body.owner == "agent" and current["owner"] == "staff":
        enqueue(conn, company, cid)
    audit(conn, company, user, f"ownership.{body.owner}", cid)
    return detail(conn, company, cid)


def queue_staff_reply(conn, member, user, cid, body: StaffReply):
    """Queue an authenticated human clarification only during staff takeover; its author is reauthorized at dispatch."""
    company = member["company_id"]
    current = conversation(conn, company, cid, lock=True)
    if current["owner"] != "staff":
        raise DomainError("Take over the conversation before replying as a salesperson.")
    if current["version"] != body.expected_version:
        raise DomainError("The conversation changed. Review the latest messages before replying.")
    text = body.text.strip()
    if not text:
        raise DomainError("Enter a message before queuing a reply.", 422)
    identity = uuid4()
    conn.execute(
        """insert into luma.outbox(id,company_id,conversation_id,kind,payload,action_key)
        values(%s,%s,%s,'reply',%s,%s)""",
        (
            identity,
            company,
            cid,
            Jsonb({"origin": "staff", "author_id": str(user), "text": text}),
            f"staff-reply:{identity}",
        ),
    )
    conn.execute("update luma.conversations set version=version+1,updated_at=now() where id=%s", (cid,))
    audit(conn, company, user, "staff.reply_queued", identity)
    return detail(conn, company, cid)
