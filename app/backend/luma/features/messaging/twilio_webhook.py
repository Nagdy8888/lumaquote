"""Twilio WhatsApp webhook ingress: signed inbound messages and delivery receipts (D43).

Authority model: the only credential is the Twilio Auth Token. Each POST carries
`X-Twilio-Signature`, the base64 HMAC-SHA1 of the exact public URL Twilio called followed by
every form parameter name and value in sorted order (algorithm from Twilio's
`RequestValidator`). The URL is rebuilt from `PUBLIC_GATEWAY_URL`, never from request headers,
so a forwarded Host cannot change what is verified. The tenant is resolved server-side: the
`AccountSid` and the receiving `To` number must equal configuration, which maps to
`WHATSAPP_COMPANY_ID`; nothing else in the payload selects a company.

Accepted events are reduced to the same shapes the Meta ingress stores (with `provider:
"twilio"`) and written to `luma.inbox` with the shared idempotent `persist` before the 200, so
`inbound.process_next` handles both providers identically. Inbound replies with empty TwiML
(no automatic answer); receipts reply with an empty 200.
"""

import base64
import hashlib
import hmac
import re
from urllib.parse import parse_qs, urlsplit

from fastapi import APIRouter, Request, Response
from starlette.concurrency import run_in_threadpool

from luma.core.config import settings
from luma.core.errors import DomainError

from .twilio_client import ACCOUNT_SID, DIGITS, MESSAGE_SID
from .webhook import persist, read_limited

router = APIRouter()
MEDIA_URL = re.compile(
    r"https://api\.twilio\.com/2010-04-01/Accounts/(?P<account>AC[0-9a-fA-F]{32})"
    r"/Messages/(?P<message>(SM|MM)[0-9a-fA-F]{32})/Media/(?P<media>ME[0-9a-fA-F]{32})"
)
RECEIPTS = {"sent": "sent", "delivered": "delivered", "read": "read", "failed": "failed", "undelivered": "failed"}
EMPTY_TWIML = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


def configured() -> None:
    """Refuse every request unless Twilio is the active provider and fully configured."""
    config = settings()
    if not (
        config.whatsapp_provider == "twilio"
        and ACCOUNT_SID.fullmatch(config.twilio_account_sid)
        and config.twilio_auth_token.get_secret_value()
        and DIGITS.fullmatch(config.twilio_whatsapp_from)
        and config.public_gateway_url.startswith("https://")
        and config.whatsapp_company_id
    ):
        raise DomainError("Twilio webhook is not configured.", 503)


def expected_signature(url: str, params: dict[str, list[str]]) -> str:
    """Compute Twilio's signature: URL + sorted(name + sorted values), HMAC-SHA1, base64."""
    data = url
    for name in sorted(params):
        for value in sorted(set(params[name])):
            data += name + value
    token = settings().twilio_auth_token.get_secret_value().encode()
    return base64.b64encode(hmac.new(token, data.encode(), hashlib.sha1).digest()).decode()


def url_variants(url: str) -> tuple[str, ...]:
    """The URL as configured plus its explicit-default-port form, matching Twilio's validator."""
    parts = urlsplit(url)
    if parts.port:
        return (url, parts._replace(netloc=parts.hostname or "").geturl())
    port = 443 if parts.scheme == "https" else 80
    return (url, parts._replace(netloc=f"{parts.netloc}:{port}").geturl())


def verified_form(body: bytes, header: str, path: str) -> dict[str, list[str]]:
    """Parse the form body and verify its signature against the public URL for `path`; 401 on mismatch."""
    try:
        params = parse_qs(body.decode("utf-8"), keep_blank_values=True, strict_parsing=False)
    except UnicodeDecodeError:
        raise DomainError("Invalid webhook payload.", 422) from None
    url = f"{settings().public_gateway_url}{path}"
    if not header or not any(
        hmac.compare_digest(expected_signature(candidate, params).encode(), header.encode())
        for candidate in url_variants(url)
    ):
        raise DomainError("Invalid webhook signature.", 401)
    return params


def first(params: dict[str, list[str]], name: str) -> str:
    """Return the first value of a form field, or an empty string."""
    values = params.get(name) or [""]
    return values[0]


def addressed_to_us(params: dict[str, list[str]], field: str) -> bool:
    """True when the account and our sandbox number (`To` inbound, `From` on receipts) match configuration."""
    config = settings()
    return (
        first(params, "AccountSid") == config.twilio_account_sid
        and first(params, field) == f"whatsapp:+{config.twilio_whatsapp_from}"
    )


def message_event(params: dict[str, list[str]]) -> dict | None:
    """Reduce one inbound message to the Meta-compatible event shape; None when it lacks a usable identity."""
    identity = first(params, "MessageSid")
    sender = first(params, "From").removeprefix("whatsapp:+")
    if not (MESSAGE_SID.fullmatch(identity) and DIGITS.fullmatch(sender)):
        return None
    event = {"id": identity, "from": sender, "name": first(params, "ProfileName")[:120], "provider": "twilio"}
    try:
        media_count = int(first(params, "NumMedia") or 0)
    except ValueError:
        return None
    if media_count <= 0:
        event.update(type="text", text=first(params, "Body")[:4000])
        return event
    match = MEDIA_URL.fullmatch(first(params, "MediaUrl0"))
    if not match or match["account"] != settings().twilio_account_sid or match["message"] != identity:
        return None
    mime = first(params, "MediaContentType0")[:80]
    kind = mime.split("/")[0] if mime.startswith(("audio/", "image/")) else "document"
    event.update(type=kind, media_id=f"{match['message']}/{match['media']}", mime=mime)
    return event


def status_event(params: dict[str, list[str]]) -> dict | None:
    """Reduce one status callback to `{id, status, code}`; intermediate states (queued, sending) yield None."""
    identity, state = first(params, "MessageSid"), RECEIPTS.get(first(params, "MessageStatus"))
    if not (MESSAGE_SID.fullmatch(identity) and state):
        return None
    code = re.sub(r"[^0-9]", "", first(params, "ErrorCode"))[:12]
    return {"id": identity, "status": state, "code": f"twilio_{code}" if code else ""}


@router.post("/webhooks/twilio")
async def receive_message(request: Request):
    """Verify, persist and acknowledge one inbound message with empty TwiML (no automatic reply)."""
    configured()
    body = await read_limited(request)
    params = verified_form(body, request.headers.get("X-Twilio-Signature", ""), "/webhooks/twilio")
    event = message_event(params) if addressed_to_us(params, "To") else None
    events = [(event["id"], "message", event)] if event else []
    await run_in_threadpool(persist, events)
    return Response(EMPTY_TWIML, media_type="text/xml")


@router.post("/webhooks/twilio/status")
async def receive_status(request: Request):
    """Verify, persist and acknowledge one delivery receipt; unknown or intermediate states are acknowledged only."""
    configured()
    body = await read_limited(request)
    params = verified_form(body, request.headers.get("X-Twilio-Signature", ""), "/webhooks/twilio/status")
    event = status_event(params) if addressed_to_us(params, "From") else None
    events = [(f"status:{event['id']}:{event['status']}", "status", event)] if event else []
    await run_in_threadpool(persist, events)
    return Response(status_code=200)
