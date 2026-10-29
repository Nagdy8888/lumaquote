from uuid import UUID

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from luma.core.admission import rate_limit
from luma.core.database import database
from luma.core.http import OperationKey, Staff
from luma.core.idempotency import operation
from luma.core.identity import membership
from luma.features.workspace.queries import detail as get_detail
from luma.features.workspace.schemas import ConversationDetail

from .participation import change_ownership, queue_staff_reply, record_customer_reply, record_note
from .schemas import Intake, Ownership, StaffReply, TextInput
from .service import intake as create_intake

router = APIRouter()


@router.post("/api/conversations/{cid}/reply", response_model=ConversationDetail)
def staff_reply(cid: UUID, body: StaffReply, user: Staff, key: OperationKey):
    """Authorize and idempotently queue a human customer reply; takeover and current authorship are enforced server-side."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        rate_limit(conn, f"{user}:reply", 10)
        return operation(
            conn,
            member,
            user,
            f"reply:{cid}",
            key,
            body.model_dump(),
            lambda: queue_staff_reply(conn, member, user, cid, body),
        )


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
            """Delegate the authorized participation change and return its canonical detail for idempotent replay."""
            return record_note(conn, member, user, cid, body)

        return operation(conn, member, user, f"note:{cid}", key, body.model_dump(), execute)


@router.post("/api/conversations/{cid}/customer-reply")
def customer_reply(cid: UUID, body: TextInput, user: Staff, key: OperationKey):
    """Accept a staff-operated local-test customer reply, invalidate old decisions, and enqueue permitted automation."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)

        def execute():
            """Delegate the authorized participation change and return its canonical detail for idempotent replay."""
            return record_customer_reply(conn, member, user, cid, body)

        return operation(conn, member, user, f"customer:{cid}", key, body.model_dump(), execute)


@router.post("/api/conversations/{cid}/ownership")
def ownership(cid: UUID, body: Ownership, user: Staff, key: OperationKey):
    """Version-check a staff ownership change and block queued automation on takeover in the same transaction."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)

        def execute():
            """Delegate the authorized participation change and return its canonical detail for idempotent replay."""
            return change_ownership(conn, member, user, cid, body)

        return operation(conn, member, user, f"ownership:{cid}", key, body.model_dump(), execute)
