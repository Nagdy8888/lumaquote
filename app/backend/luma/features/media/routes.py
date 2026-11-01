"""Authenticated bounded binary voice/photo intake and private normalized previews."""

import asyncio
from hashlib import sha256
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from luma.core.admission import rate_limit
from luma.core.database import database
from luma.core.errors import DomainError
from luma.core.http import OperationKey, Staff
from luma.core.idempotency import operation
from luma.core.identity import membership
from luma.core.storage import get_file

from .intake import accept_media, authorize_upload

router = APIRouter()


def admit_upload(user, cid, kind="audio"):
    """Authorize and persist cheap admission before accepting the bounded request stream."""
    with database(user) as conn:
        member = membership(conn, user)
        authorize_upload(conn, member["company_id"], cid)
        rate_limit(conn, f"{user}:mutation", 30)
        rate_limit(conn, f"{user}:{kind}", 6)


def persist_upload(user, cid, key, expected_version, data, kind="audio"):
    """Reauthorize after streaming and bind operation replay to bytes, target and expected version."""
    with database(user) as conn:
        member = membership(conn, user)
        return operation(
            conn,
            member,
            user,
            f"{kind}:{cid}",
            key,
            {"digest": sha256(data).hexdigest(), "expected_version": expected_version},
            lambda: accept_media(conn, member, user, cid, expected_version, data, kind=kind),
        )


@router.post("/api/conversations/{cid}/audio")
async def upload_audio(
    cid: UUID,
    request: Request,
    user: Staff,
    key: OperationKey,
    expected_version: Annotated[int, Header(alias="Expected-Version", ge=1)],
):
    """Accept at most 10 MB of actual streamed bytes within 30 seconds; filenames/MIME never establish trusted audio content."""
    return await receive_upload(cid, request, user, key, expected_version, kind="audio")


@router.post("/api/conversations/{cid}/image")
async def upload_image(
    cid: UUID,
    request: Request,
    user: Staff,
    key: OperationKey,
    expected_version: Annotated[int, Header(alias="Expected-Version", ge=1)],
):
    """Accept at most 5 MB of actual bytes; decoding and label reading run later in a durable bounded job."""
    return await receive_upload(cid, request, user, key, expected_version, kind="image")


async def receive_upload(cid, request, user, key, expected_version, *, kind):
    """Stream an authorized, fixed-kind attachment under a byte cap and a 30-second absolute deadline."""
    await run_in_threadpool(admit_upload, user, cid, kind)
    maximum = 10 if kind == "audio" else 5
    data = bytearray()
    try:
        async with asyncio.timeout(30):
            async for chunk in request.stream():
                if len(data) + len(chunk) > maximum * 1024 * 1024:
                    raise DomainError(f"The attachment must be no larger than {maximum} MB.", 413)
                data.extend(chunk)
    except TimeoutError:
        raise DomainError("The upload timed out. Reconnect and retry the same recording.", 408) from None
    return await run_in_threadpool(persist_upload, user, cid, key, expected_version, bytes(data), kind)


@router.get("/api/media/{mid}/audio")
def audio_playback(mid: UUID, user: Staff):
    """Stream only the authorized sandbox-normalized WAV; never disclose a private Storage URL or arbitrary original."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:read", 120)
        row = conn.execute(
            "select normalized_path from luma.media where message_id=%s and company_id=%s and kind='audio'",
            (mid, member["company_id"]),
        ).fetchone()
        if not row or not row["normalized_path"]:
            raise DomainError("Processed audio is not available.", 404)
        path = row["normalized_path"]
    data = get_file(path)
    if data is None:
        raise DomainError("This audio is no longer available.", 404)
    return Response(
        data, media_type="audio/wav", headers={"Content-Disposition": 'inline; filename="voice-note.wav"'}
    )


@router.get("/api/media/{mid}/image")
def image_preview(mid: UUID, user: Staff):
    """Stream only an authorized sandbox-normalized JPEG; original metadata and private Storage paths stay server-side."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:read", 120)
        row = conn.execute(
            "select normalized_path from luma.media where message_id=%s and company_id=%s and kind='image'",
            (mid, member["company_id"]),
        ).fetchone()
        if not row or not row["normalized_path"]:
            raise DomainError("Processed photo is not available.", 404)
        path = row["normalized_path"]
    data = get_file(path)
    if data is None:
        raise DomainError("This photo is no longer available.", 404)
    return Response(
        data, media_type="image/jpeg", headers={"Content-Disposition": 'inline; filename="product-label.jpg"'}
    )
