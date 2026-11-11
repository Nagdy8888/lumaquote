from uuid import uuid4

from psycopg.types.json import Jsonb

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


ORDER_NOTICE = "order"


def queue_notice(conn, company, current, text: str, key: str, *, order: bool = False) -> None:
    """Queue one fixed, customer-visible notice, only while the agent (not staff) owns the conversation.

    `key` is the outbox `action_key` (unique); a repeated key is ignored, so a redelivered inbound
    message queues its notice once, and an order notice can never be queued twice. The text must
    be fixed product wording, never customer content. The notice goes through the normal
    dispatcher gates (allowlist, live switch).

    `order=True` marks a fixed order notice (acceptance, decline, refusal, order waiting, order
    confirmed): payload `{"notice": "order"}`. It states a fact a later customer message cannot
    change, so a new customer text or attachment does not block it (`error_code customer_revision`,
    see `participation.accept_customer_text` and `media.intake.accept_media`). Only staff takeover
    still blocks it. Greeting and refusal-of-attachment notices stay unmarked and are blocked.
    """
    if current["owner"] != "agent":
        return
    payload = {"text": text, "notice": ORDER_NOTICE} if order else {"text": text}
    conn.execute(
        """insert into luma.outbox(id,company_id,conversation_id,kind,payload,action_key)
        values(%s,%s,%s,'reply',%s,%s) on conflict(action_key) do nothing""",
        (uuid4(), company, current["id"], Jsonb(payload), key),
    )
