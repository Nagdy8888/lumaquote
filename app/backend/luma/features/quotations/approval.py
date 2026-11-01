from datetime import UTC, datetime
from uuid import uuid4

from psycopg.types.json import Jsonb

from luma.core.admission import enqueue
from luma.core.audit import audit
from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation

from .freshness import check_snapshot
from .repository import latest_quote
from .schemas import Decision


def decide(conn, member, user, cid, body: Decision):
    """Record a staff decision on the still-current immutable revision.

    Conversation-before-quote locking serializes edits/takeover. Reject stale or
    expired review; rejection records needs-staff state without approving a send.
    Approval additionally requires agent ownership and fresh commercial evidence,
    then writes the approver/hash/recipient binding, quotation outbox intent and
    review-only job atomically. Return decision/quote identity, not a delivery
    receipt. Final dispatch reauthorizes the approver and current evidence again.
    """
    company = member["company_id"]
    current = conversation(conn, company, cid, lock=True)
    quote = latest_quote(conn, company, cid, lock=True)
    if not quote or quote["revision"] != body.expected_revision or quote["status"] != "review":
        raise DomainError("This revision is no longer awaiting review.")
    if quote["valid_until"] <= datetime.now(UTC):
        raise DomainError("This quotation has expired. Create a new revision.")
    if body.decision == "reject":
        conn.execute("update luma.quotes set status='rejected' where id=%s", (quote["id"],))
        conn.execute(
            "update luma.conversations set status='needs_staff',version=version+1,updated_at=now() where id=%s",
            (cid,),
        )
        enqueue(conn, company, cid, payload={"review_only": True})
        audit(conn, company, user, "quotation.rejected", quote["id"])
        return {"status": "rejected", "quote_id": quote["id"]}
    if current["owner"] != "agent":
        raise DomainError("Automation is paused. Resume it before approving automated delivery.")
    check_snapshot(conn, quote, current)
    conn.execute(
        """insert into luma.approvals(id,company_id,quote_id,approver,content_hash,recipient)
        values(%s,%s,%s,%s,%s,%s)""",
        (uuid4(), company, quote["id"], user, quote["content_hash"], quote["recipient"]),
    )
    conn.execute("update luma.quotes set status='approved' where id=%s", (quote["id"],))
    conn.execute(
        "update luma.conversations set status='delivery_queued',version=version+1,updated_at=now() where id=%s",
        (cid,),
    )
    conn.execute(
        """insert into luma.outbox(id,company_id,conversation_id,quote_id,kind,payload,action_key)
        values(%s,%s,%s,%s,'quotation',%s,%s)""",
        (
            uuid4(),
            company,
            cid,
            quote["id"],
            Jsonb({"revision": quote["revision"]}),
            f"quotation:{quote['id']}",
        ),
    )
    enqueue(conn, company, cid, payload={"review_only": True})
    audit(conn, company, user, "quotation.approved", quote["id"], revision=quote["revision"])
    return {"status": "approved", "quote_id": quote["id"], "delivery": "queued"}
