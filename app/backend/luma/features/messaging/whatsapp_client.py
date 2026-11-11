"""Restricted WhatsApp Cloud (Graph) API adapter.

Only fixed endpoints on the fixed Graph host are called, with the bearer token kept in
memory and never logged. Redirects are never followed. Media downloads are accepted
only from Meta-owned HTTPS hosts and are bounded in size. Every failure is classified
so the caller never retries an uncertain submission blindly:

- `rejected`: Meta answered with a definite 4xx; nothing was delivered.
- `unreachable`: the connection could not be made, so the request was not sent.
- `unknown`: a timeout, dropped connection or 5xx after the request left; the message
  may or may not have been accepted and must be reconciled from provider receipts.

No function here decides whether a send is permitted; that authority is checked by the
caller immediately before submission.
"""

import re
from urllib.parse import urlparse

import httpx

from luma.core.config import settings

from .errors import ProviderError

GRAPH_HOST = "https://graph.facebook.com"
MEDIA_HOST_SUFFIXES = (".fbsbx.com", ".facebook.com", ".fbcdn.net")
TIMEOUT = httpx.Timeout(20.0, connect=5.0)


class GraphError(ProviderError):
    """A classified Graph API failure; same `kind`/`code` contract as every provider error."""


def make_client() -> httpx.Client:
    """Create the HTTP client; tests replace this seam with a mock transport instead of the network."""
    return httpx.Client(timeout=TIMEOUT, follow_redirects=False)


def endpoint(path: str) -> str:
    """Build a versioned Graph URL for a configured phone number or media id."""
    return f"{GRAPH_HOST}/{settings().whatsapp_graph_version}/{path}"


def headers() -> dict:
    """Return the bearer header; the token never leaves this module's request calls."""
    return {"Authorization": f"Bearer {settings().whatsapp_token.get_secret_value()}"}


def call(method: str, url: str, **kwargs) -> httpx.Response:
    """Perform one request and map transport/HTTP failures onto the three classifications."""
    try:
        with make_client() as client:
            response = client.request(method, url, headers=headers(), **kwargs)
    except (httpx.ConnectError, httpx.ConnectTimeout):
        raise GraphError("unreachable", "connect_error") from None
    except httpx.HTTPError:
        raise GraphError("unknown", "transport_error") from None
    if response.status_code >= 500:
        raise GraphError("unknown", f"http_{response.status_code}")
    if response.status_code >= 400:
        code = "http_" + str(response.status_code)
        try:
            code = str(response.json()["error"]["code"])
        except (ValueError, KeyError, TypeError):
            pass
        raise GraphError("rejected", code)
    return response


def message_id(response: httpx.Response) -> str:
    """Extract the accepted message id; a 2xx without one is an unknown outcome, not a success."""
    try:
        value = response.json()["messages"][0]["id"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise GraphError("unknown", "no_message_id") from None
    if not isinstance(value, str) or not 0 < len(value) <= 200:
        raise GraphError("unknown", "no_message_id")
    return value


def send_text(to: str, body: str) -> str:
    """Submit one text message to a recipient and return its WhatsApp message id."""
    response = call(
        "POST",
        endpoint(f"{settings().whatsapp_phone_id}/messages"),
        json={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        },
    )
    return message_id(response)


def upload_pdf(data: bytes, filename: str) -> str:
    """Upload the canonical PDF bytes as WhatsApp media and return the media id (not itself a send)."""
    response = call(
        "POST",
        endpoint(f"{settings().whatsapp_phone_id}/media"),
        data={"messaging_product": "whatsapp", "type": "application/pdf"},
        files={"file": (filename, data, "application/pdf")},
    )
    try:
        value = response.json()["id"]
    except (ValueError, KeyError, TypeError):
        raise GraphError("unknown", "no_media_id") from None
    return str(value)


def send_document(to: str, media_id: str, filename: str, caption: str) -> str:
    """Submit one document message that references an uploaded media id and return its message id."""
    response = call(
        "POST",
        endpoint(f"{settings().whatsapp_phone_id}/messages"),
        json={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {"id": media_id, "filename": filename, "caption": caption},
        },
    )
    return message_id(response)


def ready() -> bool:
    """True when the Graph token and phone id needed for a live send are configured."""
    config = settings()
    return bool(config.whatsapp_token.get_secret_value() and config.whatsapp_phone_id)


def send_pdf(to: str, data: bytes, filename: str, caption: str, reference: str, buttons=None) -> str:
    """Upload the PDF, then send it as a document; an upload failure is a definite non-send.

    `buttons` is ignored (only Telegram attaches inline buttons). `reference` (the outbox id) is unused by Graph, which accepts uploaded bytes; it exists so
    both providers share one signature. Upload errors are re-raised as `rejected` with an
    `upload_` code because no message can have reached the customer before the send call.
    """
    try:
        media = upload_pdf(data, filename)
    except GraphError as error:
        raise GraphError("rejected", f"upload_{error.code}") from None
    return send_document(to, media, filename, caption)


def media_host_allowed(url: str) -> bool:
    """Accept only HTTPS URLs on Meta-owned hosts, so an attacker-chosen URL is never fetched with the token."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme == "https" and (host == "graph.facebook.com" or host.endswith(MEDIA_HOST_SUFFIXES))


def download(url: str, maximum: int) -> bytes:
    """Stream a pre-validated media URL, aborting as soon as the body would exceed `maximum` bytes."""
    received = bytearray()
    try:
        with make_client() as client, client.stream("GET", url, headers=headers()) as response:
            if response.status_code != 200:
                raise GraphError("rejected", f"http_{response.status_code}")
            for chunk in response.iter_bytes():
                received.extend(chunk)
                if len(received) > maximum:
                    raise GraphError("rejected", "media_too_large")
    except (httpx.ConnectError, httpx.ConnectTimeout):
        raise GraphError("unreachable", "connect_error") from None
    except httpx.HTTPError:
        raise GraphError("unknown", "transport_error") from None
    return bytes(received)


def fetch_media(media_id: str, maximum: int, allowed_mime: tuple[str, ...]) -> tuple[bytes, str]:
    """Resolve a media id to bytes with host, redirect, type and size limits; raises GraphError on any violation.

    The metadata response supplies a short-lived URL. It is checked against the Meta host
    allowlist before the bearer token is attached, redirects are refused, the declared and
    actual sizes must not exceed `maximum`, and the MIME type must be one the caller accepts.
    The returned bytes are untrusted: they still pass the sandboxed decoder.
    """
    if not re.fullmatch(r"[0-9]{1,40}", media_id):
        raise GraphError("rejected", "bad_media_id")
    meta = call("GET", endpoint(media_id)).json()
    url, mime, size = meta.get("url", ""), str(meta.get("mime_type", "")).split(";")[0], meta.get("file_size")
    if not media_host_allowed(url):
        raise GraphError("rejected", "media_host_denied")
    if mime not in allowed_mime:
        raise GraphError("rejected", "media_type_denied")
    if isinstance(size, int) and size > maximum:
        raise GraphError("rejected", "media_too_large")
    data = download(url, maximum)
    if not data:
        raise GraphError("rejected", "media_empty")
    return data, mime
