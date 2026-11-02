"""Meta WhatsApp webhook ingress: GET handshake and signed POST events, persisted before acknowledgement.

Authority model: the only credentials are Meta's app secret (signature over the exact raw
bytes) and the configured verify token. The receiving business account is resolved
server-side from configuration (`WHATSAPP_PHONE_ID` -> `WHATSAPP_COMPANY_ID`); nothing in
the payload selects a tenant. An event for any other phone number is ignored. Accepted
events are written to `luma.inbox` (deduplicated by provider identity) and acknowledged;
all business effects happen later in the worker, so a slow or failing downstream step can
never lose an event or make Meta retry a delivery that was already stored.
"""

import hashlib
import hmac
import json
import re
from uuid import UUID

import psycopg
from fastapi import APIRouter, Request, Response
from psycopg.types.json import Jsonb
from starlette.concurrency import run_in_threadpool

from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError

router = APIRouter()
MAX_BODY = 1_048_576
MAX_EVENTS = 100
DIGITS = re.compile(r"[0-9]{5,20}")
MEDIA_ID = re.compile(r"[0-9]{1,40}")


def configured() -> None:
    """Refuse every request unless the secret, verify token, phone id and company are all configured."""
    config = settings()
    if not (
        config.whatsapp_app_secret.get_secret_value()
        and config.whatsapp_verify_token.get_secret_value()
        and config.whatsapp_phone_id
        and config.whatsapp_company_id
    ):
        raise DomainError("WhatsApp webhook is not configured.", 503)


def valid_signature(body: bytes, header: str) -> bool:
    """Compare the HMAC-SHA256 of the raw body with the `sha256=<hex>` header in constant time."""
    algorithm, _, supplied = header.partition("=")
    if algorithm != "sha256" or not re.fullmatch(r"[0-9a-f]{64}", supplied):
        return False
    secret = settings().whatsapp_app_secret.get_secret_value().encode()
    return hmac.compare_digest(hmac.new(secret, body, hashlib.sha256).hexdigest(), supplied)


@router.get("/webhooks/whatsapp")
def handshake(request: Request):
    """Complete Meta's subscription handshake by echoing the challenge only for the configured verify token."""
    configured()
    params = request.query_params
    token = params.get("hub.verify_token", "")
    expected = settings().whatsapp_verify_token.get_secret_value()
    challenge = params.get("hub.challenge", "")
    if (
        params.get("hub.mode") != "subscribe"
        or not hmac.compare_digest(token.encode(), expected.encode())
        or not re.fullmatch(r"[0-9A-Za-z_-]{1,200}", challenge)
    ):
        raise DomainError("Webhook verification failed.", 403)
    return Response(challenge, media_type="text/plain")


def message_event(message: dict, names: dict) -> dict | None:
    """Reduce one inbound message to the minimum fields the worker needs; None when it has no usable identity."""
    identity, sender = message.get("id"), message.get("from")
    if not (isinstance(identity, str) and 0 < len(identity) <= 200 and isinstance(sender, str)):
        return None
    if not DIGITS.fullmatch(sender):
        return None
    kind = message.get("type") if isinstance(message.get("type"), str) else "unknown"
    event = {"id": identity, "from": sender, "type": kind[:30], "name": names.get(sender, "")[:120]}
    if kind == "text" and isinstance(message.get("text"), dict):
        event["text"] = str(message["text"].get("body", ""))[:4000]
    elif kind in ("audio", "image") and isinstance(message.get(kind), dict):
        media_id = str(message[kind].get("id", ""))
        if not MEDIA_ID.fullmatch(media_id):
            return None
        event["media_id"], event["mime"] = media_id, str(message[kind].get("mime_type", ""))[:80]
    return event


def status_event(status: dict) -> dict | None:
    """Reduce one delivery receipt to its message id, state and first error code."""
    identity, state = status.get("id"), status.get("status")
    if not (isinstance(identity, str) and 0 < len(identity) <= 200 and state in ("sent", "delivered", "read", "failed")):
        return None
    errors = status.get("errors") if isinstance(status.get("errors"), list) else []
    code = str(errors[0].get("code", "")) if errors and isinstance(errors[0], dict) else ""
    return {"id": identity, "status": state, "code": re.sub(r"[^0-9a-z_]", "", code.lower())[:40]}


def extract_events(payload: dict) -> list[tuple[str, str, dict]]:
    """Return `(provider_id, kind, event)` for every valid message/receipt addressed to the configured number."""
    events = []
    config = settings()
    if payload.get("object") != "whatsapp_business_account" or not isinstance(payload.get("entry"), list):
        return events
    for entry in payload["entry"]:
        for change in entry.get("changes", []) if isinstance(entry, dict) else []:
            value = change.get("value") if isinstance(change, dict) and change.get("field") == "messages" else None
            if not isinstance(value, dict) or value.get("metadata", {}).get("phone_number_id") != config.whatsapp_phone_id:
                continue
            names = {
                str(c.get("wa_id")): str(c.get("profile", {}).get("name", ""))
                for c in value.get("contacts", [])
                if isinstance(c, dict)
            }
            for message in value.get("messages", []):
                event = message_event(message, names) if isinstance(message, dict) else None
                if event:
                    events.append((event["id"], "message", event))
            for status in value.get("statuses", []):
                event = status_event(status) if isinstance(status, dict) else None
                if event:
                    events.append((f"status:{event['id']}:{event['status']}", "status", event))
    return events


def persist(events: list[tuple[str, str, dict]]) -> int:
    """Store events idempotently under the configured company; return how many were new."""
    company = UUID(settings().whatsapp_company_id)
    new = 0
    try:
        with database(worker=True) as conn:
            for provider_id, kind, event in events:
                inserted = conn.execute(
                    """insert into luma.inbox(provider_id,company_id,payload,kind) values(%s,%s,%s,%s)
                    on conflict(provider_id) do nothing returning provider_id""",
                    (provider_id, company, Jsonb(event), kind),
                ).fetchone()
                new += bool(inserted)
    except psycopg.Error:
        raise DomainError("Webhook storage is unavailable.", 503) from None
    return new


@router.post("/webhooks/whatsapp")
async def receive(request: Request):
    """Verify the raw-body signature, persist valid events and acknowledge only after the commit."""
    configured()
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_BODY:
            raise DomainError("Webhook body is too large.", 413)
    if not valid_signature(bytes(body), request.headers.get("X-Hub-Signature-256", "")):
        raise DomainError("Invalid webhook signature.", 401)
    try:
        payload = json.loads(bytes(body))
    except ValueError:
        raise DomainError("Invalid webhook payload.", 422) from None
    events = extract_events(payload) if isinstance(payload, dict) else []
    if len(events) > MAX_EVENTS:
        raise DomainError("Too many events in one webhook.", 413)
    new = await run_in_threadpool(persist, events)
    return {"status": "accepted", "events": len(events), "new": new}
