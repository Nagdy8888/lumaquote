from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import Response

from luma.core.admission import rate_limit
from luma.core.database import database
from luma.core.errors import DomainError
from luma.core.http import OperationKey, Staff
from luma.core.idempotency import operation
from luma.core.identity import membership
from luma.core.storage import get_file, put_file
from luma.features.conversations.repository import conversation

from .approval import decide
from .documents import quotation_pdf
from .drafting import draft as create_draft
from .schemas import Decision, DraftInput

router = APIRouter()


@router.post("/api/conversations/{cid}/draft")
def draft(cid: UUID, body: DraftInput, user: Staff, key: OperationKey):
    """Validate an expected conversation version and authoritative products, then create a new immutable quotation revision."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn,
            member,
            user,
            f"draft:{cid}",
            key,
            body.model_dump(mode="json"),
            lambda: create_draft(conn, member, user, cid, body),
        )


@router.post("/api/conversations/{cid}/decision")
def decision(cid: UUID, body: Decision, user: Staff, key: OperationKey):
    """Authorize and idempotently record the exact-revision staff decision under the stricter approval admission limit."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:approval", 10)
        return operation(
            conn,
            member,
            user,
            f"decision:{cid}",
            key,
            body.model_dump(),
            lambda: decide(conn, member, user, cid, body),
        )


@router.get("/api/quotes/{qid}/pdf")
def pdf(qid: UUID, user: Staff):
    """Authorize a quotation and stream its canonical private PDF, creating it once from the stored revision if absent."""
    with database(user) as conn:
        member = membership(conn, user)
        row = conn.execute(
            "select * from luma.quotes where company_id=%s and id=%s", (member["company_id"], qid)
        ).fetchone()
        if not row:
            raise DomainError("Quotation not found.", 404)
        current = conversation(conn, member["company_id"], row["conversation_id"])
        path = f"{member['company_id']}/quotes/{qid}.pdf"
        content = get_file(path)
        if content is None:
            content = quotation_pdf(row, current)
            put_file(path, content, "application/pdf")
            content = get_file(path) or content
        return Response(
            content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{row["number"]}-r{row["revision"]}.pdf"'},
        )
