"""Signed Apps Script endpoints for the Gmail channel (decision D47), mounted only on the gateway.

All three take the HMAC-signed Google envelope (`X-Luma-Signature`) and refuse with 503 until the
Google connection is configured. They can store mail for the configured company and send or
report replies the backend already queued; they cannot read conversations, approve or price.
"""

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from luma.features.google_sync.routes import signed_body

from .email_dispatch import claim_mail, record_mail_receipt
from .email_ingress import receive_mail

router = APIRouter()


@router.post("/callbacks/google/mail/inbound")
async def gmail_inbound(request: Request):
    """Store up to ten signed mails (body at most 256 KiB) before answering with their ids."""
    body, signature = await signed_body(request, 262144)
    return await run_in_threadpool(receive_mail, body, signature)


@router.post("/callbacks/google/mail/claim")
async def gmail_claim(request: Request):
    """Lease the next queued reply to the signed Apps Script sender (body at most 1 KiB)."""
    body, signature = await signed_body(request, 1024)
    return await run_in_threadpool(claim_mail, body, signature)


@router.post("/callbacks/google/mail/receipt")
async def gmail_receipt(request: Request):
    """Record the signed outcome of one claimed reply (body at most 2 KiB)."""
    body, signature = await signed_body(request, 2048)
    return await run_in_threadpool(record_mail_receipt, body, signature)
