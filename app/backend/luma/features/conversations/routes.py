from uuid import UUID

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from luma.core.admission import enqueue, rate_limit
from luma.core.audit import audit
from luma.core.database import database
from luma.core.errors import DomainError
from luma.core.http import OperationKey, Staff
from luma.core.idempotency import operation
from luma.core.identity import membership
from luma.features.workspace.queries import detail as get_detail
from luma.features.workspace.schemas import ConversationDetail

from .repository import conversation
from .schemas import Intake, Ownership, TextInput
from .service import add_message
from .service import intake as create_intake

router = APIRouter()


@router.get("/api/conversations/{cid}", response_model=ConversationDetail)
def detail(cid: UUID, user: Staff):
    """Return scoped conversation, ordered messages, latest quotation, and delivery records for the working inbox."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:read", 120)
        return jsonable_encoder(get_detail(conn, member["company_id"], cid))


@router.post("/api/conversations")
def intake(body: Intake, user: Staff, key: OperationKey):
    """Create a local-test customer request, initial message, and durable agent job in one transaction."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn,
            member,
            user,
            "intake",
            key,
            body.model_dump(mode="json"),
            lambda: create_intake(conn, member, user, body),
        )


@router.post("/api/conversations/{cid}/messages")
def message(cid: UUID, body: TextInput, user: Staff, key: OperationKey):
    """Persist an authenticated staff note idempotently; this endpoint does not impersonate a customer or send externally."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)

        def execute():
            """Apply this route's authorized mutation atomically and return canonical persisted detail for idempotent replay."""
            conversation(conn, member["company_id"], cid, lock=True)
            add_message(conn, member["company_id"], cid, "staff", body.text)
            audit(conn, member["company_id"], user, "staff.note_added", cid)
            return get_detail(conn, member["company_id"], cid)

        return operation(conn, member, user, f"note:{cid}", key, body.model_dump(), execute)


@router.post("/api/conversations/{cid}/customer-reply")
def customer_reply(cid: UUID, body: TextInput, user: Staff, key: OperationKey):
    """Accept a staff-operated local-test customer reply, invalidate old decisions, and enqueue permitted automation."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)

        def execute():
            """Apply this route's authorized mutation atomically and return canonical persisted detail for idempotent replay."""
            current = conversation(conn, member["company_id"], cid, lock=True)
            if current["channel"] != "local_test":
                raise DomainError(
                    "Simulated customer replies are only available in the local test channel.", 403
                )
            rate_limit(conn, f"conversation:{cid}", 6)
            add_message(conn, member["company_id"], cid, "customer", body.text)
            conn.execute("update luma.conversations set last_customer_at=now() where id=%s", (cid,))
            conn.execute(
                "update luma.quotes set status='superseded' where conversation_id=%s and status in ('review','approved')",
                (cid,),
            )
            conn.execute(
                "update luma.outbox set status='blocked',error_code='customer_revision' where conversation_id=%s and status='queued'",
                (cid,),
            )
            if current["owner"] == "agent":
                enqueue(conn, member["company_id"], cid)
            return get_detail(conn, member["company_id"], cid)

        return operation(conn, member, user, f"customer:{cid}", key, body.model_dump(), execute)


@router.post("/api/conversations/{cid}/ownership")
def ownership(cid: UUID, body: Ownership, user: Staff, key: OperationKey):
    """Version-check a staff ownership change and block queued automation on takeover in the same transaction."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)

        def execute():
            """Apply this route's authorized mutation atomically and return canonical persisted detail for idempotent replay."""
            current = conversation(conn, member["company_id"], cid, lock=True)
            if current["version"] != body.expected_version:
                raise DomainError("Conversation changed. Refresh before changing ownership.")
            conn.execute(
                "update luma.conversations set owner=%s,version=version+1 where id=%s", (body.owner, cid)
            )
            if body.owner == "staff":
                conn.execute(
                    "update luma.outbox set status='blocked',error_code='staff_takeover' where conversation_id=%s and status='queued'",
                    (cid,),
                )
            audit(conn, member["company_id"], user, f"ownership.{body.owner}", cid)
            return get_detail(conn, member["company_id"], cid)

        return operation(conn, member, user, f"ownership:{cid}", key, body.model_dump(), execute)
