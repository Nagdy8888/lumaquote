"""Telegram ingress by long polling (D44): fetch updates, reduce them, persist before confirming.

Authority model: there is no inbound HTTP endpoint. The worker calls `getUpdates` with the bot
token, so every update is authenticated by Telegram's TLS connection, not by a shared secret.
The tenant is `TELEGRAM_COMPANY_ID` from configuration. Only private chats are accepted (the chat
id then equals the sender's user id), and the sender allowlist is applied later by the inbox
worker exactly as for WhatsApp.

Durability: updates are written to `luma.inbox` (idempotent on `tg:<chat id>:<message id>`)
before the next poll passes `offset = highest update_id + 1`, which is what confirms them to
Telegram. A crash between the two only causes Telegram to resend those updates, which the
inbox key deduplicates. The offset is kept in memory: after a restart the first poll omits it
and receives every still-unconfirmed update (Telegram keeps them up to 24 hours).
"""

import logging
import re

from luma.core.config import settings

from . import telegram_client
from .errors import ProviderError
from .webhook import persist

logger = logging.getLogger("luma.telegram")
USER_ID = re.compile(r"[0-9]{1,20}")
AUDIO_FALLBACK = "audio/ogg"


def largest_photo(sizes) -> dict | None:
    """Pick the largest PhotoSize by area; the Bot API does not promise an order."""
    candidates = [s for s in sizes if isinstance(s, dict) and isinstance(s.get("file_id"), str)] if isinstance(sizes, list) else []
    return max(candidates, key=lambda s: int(s.get("width", 0)) * int(s.get("height", 0)), default=None)


def reduce_update(update: dict) -> tuple[str, str, dict] | None:
    """Reduce one Update to `(provider_id, "message", event)` in the shared event shape, or None to skip it."""
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    chat, sender = message.get("chat"), message.get("from")
    if not (isinstance(chat, dict) and isinstance(sender, dict) and chat.get("type") == "private"):
        return None
    chat_id, user_id, message_id = str(chat.get("id", "")), str(sender.get("id", "")), message.get("message_id")
    if not (USER_ID.fullmatch(user_id) and chat_id == user_id and isinstance(message_id, int) and message_id > 0):
        return None
    if sender.get("is_bot") is True:
        return None
    identity = f"tg:{chat_id}:{message_id}"
    name = " ".join(str(sender.get(k, "")) for k in ("first_name", "last_name") if sender.get(k))[:120]
    event = {"id": identity, "from": user_id, "name": name, "provider": "telegram", "channel": "telegram"}
    voice = message.get("voice") or message.get("audio")
    photo = largest_photo(message.get("photo"))
    if isinstance(message.get("text"), str):
        event.update(type="text", text=message["text"][:4000])
    elif isinstance(voice, dict) and isinstance(voice.get("file_id"), str):
        event.update(type="audio", media_id=voice["file_id"], mime=str(voice.get("mime_type") or AUDIO_FALLBACK)[:80])
    elif photo:
        event.update(type="image", media_id=photo["file_id"], mime="image/jpeg")
    else:
        event["type"] = "unsupported"
    return identity, "message", event


def poll_once(offset: int | None, timeout: int = telegram_client.POLL_SECONDS) -> int | None:
    """Fetch one batch, persist the usable messages, and return the offset that confirms this batch.

    Returns the unchanged offset when Telegram is unreachable or refuses the call, so nothing is
    confirmed without first being stored. Storage errors propagate for the same reason.
    """
    try:
        updates = telegram_client.get_updates(offset, timeout)
    except ProviderError as error:
        logger.warning("Telegram poll failed: %s", error.code)
        return offset
    ids = [u["update_id"] for u in updates if isinstance(u.get("update_id"), int)]
    events = [event for event in (reduce_update(u) for u in updates) if event]
    if events:
        persist(events, settings().telegram_company_id)
    return max(ids) + 1 if ids else offset
