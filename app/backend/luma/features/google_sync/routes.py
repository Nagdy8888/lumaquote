"""Bounded HTTP ingress for signed Google invalidation hints."""

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from luma.core.errors import DomainError

from .callbacks import accept_hint, verify_hint
from .exports import claim_export, record_receipt
from .snapshots import receive_snapshot

router = APIRouter()


@router.post("/callbacks/google/snapshot", status_code=202)
async def supplier_snapshot(request: Request):
    """Accept at most 512 KiB of signed complete supplier tables; no OAuth credential crosses this boundary."""
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 524288:
            raise DomainError("Supplier snapshot is too large.", 413)
    signature = request.headers.get("X-Luma-Signature", "")
    if len(signature) != 64 or any(c not in "0123456789abcdef" for c in signature):
        raise DomainError("Invalid Google callback signature.", 401)
    return await run_in_threadpool(receive_snapshot, bytes(body), signature)


@router.post("/callbacks/google", status_code=202)
async def google_callback(request: Request):
    """Read at most 4096 bytes, verify origin and persist before acknowledging receipt."""
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 4096:
            raise DomainError("Google callback is too large.", 413)
    signature = request.headers.get("X-Luma-Signature", "")
    if len(signature) != 64 or any(c not in "0123456789abcdef" for c in signature):
        raise DomainError("Invalid Google callback signature.", 401)
    hint = verify_hint(bytes(body), signature)
    await run_in_threadpool(accept_hint, hint, bytes(body))
    return {"status": "accepted", "sync_status": "pending"}


async def signed_body(request: Request, limit: int) -> tuple[bytes, str]:
    """Read a bounded request body and a well-formed hex signature header before any verification work."""
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > limit:
            raise DomainError("Google export request is too large.", 413)
    signature = request.headers.get("X-Luma-Signature", "")
    if len(signature) != 64 or any(c not in "0123456789abcdef" for c in signature):
        raise DomainError("Invalid Google callback signature.", 401)
    return bytes(body), signature


@router.post("/callbacks/google/exports/claim")
async def drive_export_claim(request: Request):
    """Lease the next approved quotation PDF to the signed Apps Script poller (body at most 1 KiB)."""
    body, signature = await signed_body(request, 1024)
    return await run_in_threadpool(claim_export, body, signature)


@router.post("/callbacks/google/exports/receipt")
async def drive_export_receipt(request: Request):
    """Record the signed outcome of one claimed export; the digest must equal the canonical PDF's (body at most 2 KiB)."""
    body, signature = await signed_body(request, 2048)
    return await run_in_threadpool(record_receipt, body, signature)
