import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

from luma.core.admission import rate_limit
from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError
from luma.core.http import Staff
from luma.core.identity import membership

from .queries import workspace as get_workspace
from .schemas import WorkspaceView

router = APIRouter()


@router.get("/api/workspace", response_model=WorkspaceView)
def workspace(user: Staff):
    """Read company-scoped workspace collections and actual stored aggregates for the authorized staff view."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:read", 120)
        result = get_workspace(conn, member)
        config = settings()
        result["integrations"] = {
            "ai": "enabled"
            if config.enable_paid_ai and config.openai_api_key.get_secret_value()
            else "disabled",
            "whatsapp": "configured_unverified"
            if config.whatsapp_token.get_secret_value()
            else "not_connected",
            "google": "configured_unverified"
            if config.google_refresh_token.get_secret_value()
            else "not_connected",
            "langsmith": "configured_unverified"
            if config.langsmith_tracing and config.langsmith_api_key.get_secret_value()
            else "disabled",
        }
        return jsonable_encoder(result, exclude={"embedding"})


@router.get("/api/events")
async def events(user: Staff, request: Request):
    """Stream bounded authenticated refresh notifications; membership is rechecked before every event."""

    async def stream():
        """Emit revision notifications until disconnected, revoked, or the bounded stream lifetime ends."""
        for _ in range(30):
            if await request.is_disconnected():
                break

            def inspect():
                """Read the current company audit revision under a fresh membership check for the next refresh notification."""
                with database(user) as conn:
                    member = membership(conn, user)
                    value = conn.execute(
                        "select coalesce(max(id),0) revision from luma.audit where company_id=%s",
                        (member["company_id"],),
                    ).fetchone()
                    return value

            try:
                value = await asyncio.to_thread(inspect)
            except DomainError:
                yield "event: revoked\ndata: {}\n\n"
                break
            yield f"event: refresh\ndata: {json.dumps(value)}\n\n"
            await asyncio.sleep(3)

    return StreamingResponse(stream(), media_type="text/event-stream")
