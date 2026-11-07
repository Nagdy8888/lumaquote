"""Restricted Twilio WhatsApp (Sandbox) adapter: send text, send a PDF by signed link, fetch media.

Chosen in D43 because Meta refused app creation for the user's restricted business portfolio.
Same failure contract as the Graph adapter (`ProviderError` kinds `rejected`, `unreachable`,
`unknown`), so the outbox never retries an uncertain submission.

Authority and secrets: the Account SID and Auth Token authenticate every API call with HTTP
Basic auth and are never logged. Only fixed paths under the configured account on
`api.twilio.com` are called. Twilio has no upload endpoint for outbound media, so a quotation
PDF is offered at a short-lived HMAC-signed gateway URL (`media_links`) that Twilio fetches.

Media fetch: inbound media is addressed by message and media SID (never by a URL from the
payload), fetched with Basic auth from `api.twilio.com`; at most one redirect is followed, only
to HTTPS, and credentials are never sent to the redirect target. Bodies are size-bounded and
the declared MIME type must be one the caller accepts. Returned bytes remain untrusted.

Limits from Twilio's docs (read 2026-11-07, re-check before relying on them): non-image media
up to 500 KB, sandbox sends one message per three seconds, sandbox joins expire after three
days, free-form messages only inside the 24-hour customer service window.
"""

import re

import httpx

from luma.core.config import settings

from .errors import ProviderError
from .media_links import quotation_url

API_HOST = "https://api.twilio.com"
TIMEOUT = httpx.Timeout(20.0, connect=5.0)
ACCOUNT_SID = re.compile(r"AC[0-9a-fA-F]{32}")
MESSAGE_SID = re.compile(r"(SM|MM)[0-9a-fA-F]{32}")
MEDIA_REF = re.compile(r"(?P<message>(SM|MM)[0-9a-fA-F]{32})/(?P<media>ME[0-9a-fA-F]{32})")
DIGITS = re.compile(r"[0-9]{5,20}")
MAX_PDF_BYTES = 500 * 1024


def make_client() -> httpx.Client:
    """Create the HTTP client; tests replace this seam with a mock transport instead of the network."""
    return httpx.Client(timeout=TIMEOUT, follow_redirects=False)


def account_base() -> str:
    """Return the fixed REST base for the configured account; refuses an invalid SID instead of building a URL."""
    sid = settings().twilio_account_sid
    if not ACCOUNT_SID.fullmatch(sid):
        raise ProviderError("rejected", "bad_account_sid")
    return f"{API_HOST}/2010-04-01/Accounts/{sid}"


def auth() -> tuple[str, str]:
    """Return the Basic-auth pair; the token never leaves this module's request calls."""
    config = settings()
    return config.twilio_account_sid, config.twilio_auth_token.get_secret_value()


def ready() -> bool:
    """True when account, token, sender digits and an HTTPS public gateway are configured."""
    config = settings()
    return bool(
        ACCOUNT_SID.fullmatch(config.twilio_account_sid)
        and config.twilio_auth_token.get_secret_value()
        and DIGITS.fullmatch(config.twilio_whatsapp_from)
        and config.public_gateway_url.startswith("https://")
    )


def status_callback() -> str:
    """The exact public URL Twilio posts delivery receipts to (and signs)."""
    return f"{settings().public_gateway_url}/webhooks/twilio/status"


def call(method: str, url: str, **kwargs) -> httpx.Response:
    """Perform one authenticated request and map transport/HTTP failures onto the three kinds."""
    try:
        with make_client() as client:
            response = client.request(method, url, auth=auth(), **kwargs)
    except (httpx.ConnectError, httpx.ConnectTimeout):
        raise ProviderError("unreachable", "connect_error") from None
    except httpx.HTTPError:
        raise ProviderError("unknown", "transport_error") from None
    if response.status_code >= 500:
        raise ProviderError("unknown", f"http_{response.status_code}")
    if response.status_code >= 400:
        code = f"http_{response.status_code}"
        try:
            code = f"twilio_{int(response.json()['code'])}"
        except (ValueError, KeyError, TypeError):
            pass
        raise ProviderError("rejected", code)
    return response


def message_sid(response: httpx.Response) -> str:
    """Extract the accepted message SID; a 2xx without a valid one is an unknown outcome, not a success."""
    try:
        value = response.json()["sid"]
    except (ValueError, KeyError, TypeError):
        raise ProviderError("unknown", "no_message_id") from None
    if not isinstance(value, str) or not MESSAGE_SID.fullmatch(value):
        raise ProviderError("unknown", "no_message_id")
    return value


def create_message(to: str, fields: dict) -> str:
    """POST one WhatsApp message from the configured sender to an E.164-digit recipient; return its SID."""
    if not DIGITS.fullmatch(to):
        raise ProviderError("rejected", "bad_recipient")
    data = {
        "From": f"whatsapp:+{settings().twilio_whatsapp_from}",
        "To": f"whatsapp:+{to}",
        "StatusCallback": status_callback(),
        **fields,
    }
    return message_sid(call("POST", f"{account_base()}/Messages.json", data=data))


def send_text(to: str, body: str) -> str:
    """Submit one free-form text (valid only inside the 24-hour window) and return its message SID."""
    return create_message(to, {"Body": body})


def send_pdf(to: str, data: bytes, filename: str, caption: str, reference: str) -> str:
    """Send the PDF as media fetched by Twilio from a signed, expiring gateway URL for outbox `reference`.

    The bytes are not transmitted here; they are used only to refuse a document above Twilio's
    documented non-image limit before any send. `filename` is unused because Twilio names the
    document from the URL path.
    """
    if len(data) > MAX_PDF_BYTES:
        raise ProviderError("rejected", "document_too_large")
    return create_message(to, {"Body": caption, "MediaUrl": quotation_url(reference)})


def stream(client: httpx.Client, url: str, maximum: int, credentials) -> httpx.Response | bytes:
    """GET `url`, returning a redirect response unread or the bounded body bytes of a 200."""
    with client.stream("GET", url, auth=credentials) as response:
        if response.status_code in (301, 302, 303, 307, 308):
            return response
        if response.status_code != 200:
            raise ProviderError("rejected", f"http_{response.status_code}")
        received = bytearray()
        for chunk in response.iter_bytes():
            received.extend(chunk)
            if len(received) > maximum:
                raise ProviderError("rejected", "media_too_large")
        return bytes(received)


def fetch_media(reference: str, maximum: int, allowed_mime: tuple[str, ...], declared_mime: str) -> tuple[bytes, str]:
    """Fetch one inbound media item by `MessageSid/MediaSid` with type, size and redirect limits.

    `declared_mime` comes from the signed webhook (`MediaContentType0`) and must be allowed
    before any request. Raises `ProviderError` on every violation.
    """
    match = MEDIA_REF.fullmatch(reference)
    if not match:
        raise ProviderError("rejected", "bad_media_id")
    mime = declared_mime.split(";")[0].strip().lower()
    if mime not in allowed_mime:
        raise ProviderError("rejected", "media_type_denied")
    url = f"{account_base()}/Messages/{match['message']}/Media/{match['media']}"
    try:
        with make_client() as client:
            result = stream(client, url, maximum, auth())
            if isinstance(result, httpx.Response):
                target = result.headers.get("location", "")
                if not target.startswith("https://"):
                    raise ProviderError("rejected", "media_redirect_denied")
                result = stream(client, target, maximum, None)
                if isinstance(result, httpx.Response):
                    raise ProviderError("rejected", "media_redirect_denied")
    except (httpx.ConnectError, httpx.ConnectTimeout):
        raise ProviderError("unreachable", "connect_error") from None
    except httpx.HTTPError:
        raise ProviderError("unknown", "transport_error") from None
    if not result:
        raise ProviderError("rejected", "media_empty")
    return result, mime
