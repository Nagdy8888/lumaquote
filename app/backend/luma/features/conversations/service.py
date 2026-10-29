from uuid import uuid4

from luma.core.admission import enqueue
from luma.core.audit import audit

from .repository import conversation
from .schemas import Intake


def intake(conn, member, user, body: Intake):
    """Create a local-test customer request, initial message, and durable agent job in one transaction."""
    company = member["company_id"]
    cid = uuid4()
    conn.execute(
        """insert into luma.conversations(id,company_id,customer_name,customer_company,recipient,channel)
        values(%s,%s,%s,%s,%s,'local_test')""",
        (cid, company, body.customer_name.strip(), body.customer_company.strip(), f"local:{cid}"),
    )
    add_message(conn, company, cid, "customer", body.text)
    enqueue(conn, company, cid)
    audit(conn, company, user, "request.created", cid)
    return conversation(conn, company, cid)


def add_message(conn, company, cid, actor, body, kind="text", object_path=None, provider_id=None):
    """Persist a scoped message and advance the conversation version; provider message IDs deduplicate ingress."""
    inserted = conn.execute(
        """insert into luma.messages(id,company_id,conversation_id,actor,body,kind,object_path,provider_id)
        values(%s,%s,%s,%s,%s,%s,%s,%s) on conflict(provider_id) do nothing returning id""",
        (uuid4(), company, cid, actor, body, kind, object_path, provider_id),
    ).fetchone()
    if inserted is None:
        return None
    conn.execute(
        "update luma.conversations set updated_at=now(),version=version+1 where id=%s and company_id=%s",
        (cid, company),
    )
    return inserted["id"]
