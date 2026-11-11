"""Restricted Telegram Bot API adapter: long-poll updates, send text and PDF documents, fetch media.

Chosen in D44 because WhatsApp test access was blocked (Meta portfolio restriction) and Twilio
is not free in Egypt. The Bot API is free and needs only a bot token from @BotFather.

Secrets: the bot token is part of every Bot API URL (`/bot<token>/<method>` and
`/file/bot<token>/<path>`), so URLs are never logged, exceptions are converted to opaque codes
`from None`, and the `httpx` request logger is held at WARNING so its INFO line (which prints the
URL) cannot leak the token. Only fixed methods on `api.telegram.org` are called; redirects are
never followed.

Failure contract (shared `ProviderError`): `rejected` for a definite refusal (`ok: false` with a
4xx, including 429 flood control and 403 when the user blocked the bot), `unreachable` when no
connection was made, `unknown` for timeouts, 5xx or a success without a message id. The Bot API
has no idempotency key and no delivery or read receipts, so an accepted send stays `submitted`.

Limits from the Bot API page (version 10.3, read 2026-11-07): text 1-4096 characters, captions
up to 1024, uploads up to 50 MB, downloads up to 20 MB, file links valid at least one hour,
unconfirmed updates kept up to 24 hours, about 30 messages per second per bot.
"""

import json
import logging
import re

import httpx

from luma.core.config import settings

from .errors import ProviderError

API_HOST = "https://api.telegram.org"
TIMEOUT = httpx.Timeout(20.0, connect=5.0)
POLL_SECONDS = 25
FILE_PATH = re.compile(r"[A-Za-z0-9_-]+(/[A-Za-z0-9_.-]+)*")
FILE_ID = re.compile(r"[A-Za-z0-9_-]{10,200}")
CHAT_ID = re.compile(r"[0-9]{1,20}")
MAX_TEXT = 4096
MAX_CAPTION = 1024
MAX_CALLBACK_DATA = 64
MAX_CALLBACK_ANSWER = 200

logger = logging.getLogger("luma.telegram")
logging.getLogger("httpx").setLevel(logging.WARNING)


def make_client(timeout: httpx.Timeout = TIMEOUT) -> httpx.Client:
    """Create the HTTP client; tests replace this seam with a mock transport instead of the network."""
    return httpx.Client(timeout=timeout, follow_redirects=False)


def token() -> str:
    """Return the bot token; refuses to build any URL without one."""
    value = settings().telegram_bot_token.get_secret_value()
    if not value:
        raise ProviderError("rejected", "not_configured")
    return value


def ready() -> bool:
    """True when a bot token and a receiving company are configured."""
    config = settings()
    return bool(config.telegram_bot_token.get_secret_value() and config.telegram_company_id)


def call(method: str, *, timeout: httpx.Timeout = TIMEOUT, **kwargs):
    """POST one Bot API method and return `result`; maps every failure onto the three kinds."""
    url = f"{API_HOST}/bot{token()}/{method}"
    try:
        with make_client(timeout) as client:
            response = client.post(url, **kwargs)
    except (httpx.ConnectError, httpx.ConnectTimeout):
        raise ProviderError("unreachable", "connect_error") from None
    except httpx.HTTPError:
        raise ProviderError("unknown", "transport_error") from None
    if response.status_code >= 500:
        raise ProviderError("unknown", f"http_{response.status_code}")
    try:
        body = response.json()
    except ValueError:
        raise ProviderError("unknown" if response.status_code < 400 else "rejected", "bad_response") from None
    if not isinstance(body, dict) or body.get("ok") is not True:
        code = body.get("error_code") if isinstance(body, dict) else None
        raise ProviderError("rejected", f"telegram_{code}" if isinstance(code, int) else f"http_{response.status_code}")
    return body.get("result")


def message_ref(chat_id: str, result) -> str:
    """Build the provider id `tg:<chat>:<message>` from a sent Message; a missing id is an unknown outcome."""
    message = result.get("message_id") if isinstance(result, dict) else None
    if not isinstance(message, int) or message <= 0:
        raise ProviderError("unknown", "no_message_id")
    return f"tg:{chat_id}:{message}"


def send_text(to: str, body: str) -> str:
    """Send one plain-text message to a private chat and return its provider id."""
    if not CHAT_ID.fullmatch(to):
        raise ProviderError("rejected", "bad_recipient")
    return message_ref(to, call("sendMessage", json={"chat_id": int(to), "text": body[:MAX_TEXT]}))


def send_pdf(
    to: str, data: bytes, filename: str, caption: str, reference: str, buttons: list[tuple[str, str]] | None = None
) -> str:
    """Upload the canonical PDF bytes as a document with a caption; `reference` is unused (shared signature).

    `buttons` is an optional row of `(label, callback_data)` pairs sent as one inline keyboard row
    (`reply_markup`). In a multipart upload `reply_markup` must be a JSON-serialized string field.
    Callback data is 1-64 bytes (checked here); a longer value is refused before any request.
    """
    if not CHAT_ID.fullmatch(to):
        raise ProviderError("rejected", "bad_recipient")
    fields = {"chat_id": to, "caption": caption[:MAX_CAPTION]}
    if buttons:
        if any(not 1 <= len(value.encode()) <= MAX_CALLBACK_DATA for _, value in buttons):
            raise ProviderError("rejected", "bad_button")
        keyboard = [[{"text": label, "callback_data": value} for label, value in buttons]]
        fields["reply_markup"] = json.dumps({"inline_keyboard": keyboard}, separators=(",", ":"))
    result = call(
        "sendDocument",
        data=fields,
        files={"document": (filename, data, "application/pdf")},
    )
    return message_ref(to, result)


def get_updates(offset: int | None, timeout: int = POLL_SECONDS) -> list[dict]:
    """Long-poll for new `message` and `callback_query` updates; `offset` confirms every earlier update."""
    payload = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
    if offset is not None:
        payload["offset"] = offset
    result = call("getUpdates", json=payload, timeout=httpx.Timeout(timeout + 10.0, connect=5.0))
    return [item for item in result if isinstance(item, dict)] if isinstance(result, list) else []


def answer_callback(callback_id: str, text: str = "") -> bool:
    """Stop the button's progress spinner with `answerCallbackQuery`; best effort, True on success.

    Only fixed text is ever passed (0-200 characters, per the Bot API). A failure is swallowed
    and logged as an opaque code: the answer is cosmetic, is never retried, and never prints
    customer text, the callback id or the token-bearing URL.
    """
    try:
        call("answerCallbackQuery", json={"callback_query_id": callback_id, "text": text[:MAX_CALLBACK_ANSWER]})
    except ProviderError as error:
        logger.warning("Telegram callback answer failed: %s", error.code)
        return False
    return True


def clear_buttons(chat_id: str, message_id: int) -> bool:
    """Remove the inline keyboard from one message with `editMessageReplyMarkup`; best effort, True on success.

    Omitting `reply_markup` removes the keyboard (Bot API: the parameter is optional and is an
    InlineKeyboardMarkup when present). Called after a button press is settled so a stale
    Accept/Decline cannot be pressed again. Side effect: one Telegram call, never retried and never
    inside a database transaction. A refusal (for example "message is not modified" when the
    keyboard is already gone, or a message older than Telegram allows) is swallowed and logged as an
    opaque code only; chat id, message id, customer text and the token-bearing URL are never logged.
    """
    if not (CHAT_ID.fullmatch(chat_id) and isinstance(message_id, int) and message_id > 0):
        return False
    try:
        call("editMessageReplyMarkup", json={"chat_id": int(chat_id), "message_id": message_id})
    except ProviderError as error:
        logger.warning("Telegram button removal failed: %s", error.code)
        return False
    return True


def fetch_media(file_id: str, maximum: int, allowed_mime: tuple[str, ...], declared_mime: str) -> tuple[bytes, str]:
    """Resolve a `file_id` through getFile and download it with type, size and path limits.

    `declared_mime` comes from the Message (photos are JPEG by Telegram's design) and must be
    allowed before any request. The file path from getFile is pattern-checked before it is
    joined to the fixed download URL. Raises `ProviderError` on every violation.
    """
    if not FILE_ID.fullmatch(file_id):
        raise ProviderError("rejected", "bad_media_id")
    mime = declared_mime.split(";")[0].strip().lower()
    if mime not in allowed_mime:
        raise ProviderError("rejected", "media_type_denied")
    info = call("getFile", json={"file_id": file_id})
    path = info.get("file_path", "") if isinstance(info, dict) else ""
    size = info.get("file_size") if isinstance(info, dict) else None
    if not (isinstance(path, str) and FILE_PATH.fullmatch(path) and ".." not in path):
        raise ProviderError("rejected", "media_path_denied")
    if isinstance(size, int) and size > maximum:
        raise ProviderError("rejected", "media_too_large")
    received = bytearray()
    try:
        with make_client() as client, client.stream("GET", f"{API_HOST}/file/bot{token()}/{path}") as response:
            if response.status_code != 200:
                raise ProviderError("rejected", f"http_{response.status_code}")
            for chunk in response.iter_bytes():
                received.extend(chunk)
                if len(received) > maximum:
                    raise ProviderError("rejected", "media_too_large")
    except (httpx.ConnectError, httpx.ConnectTimeout):
        raise ProviderError("unreachable", "connect_error") from None
    except httpx.HTTPError:
        raise ProviderError("unknown", "transport_error") from None
    if not received:
        raise ProviderError("rejected", "media_empty")
    return bytes(received), mime
