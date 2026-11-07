"""Adapter selection for customer messaging: WhatsApp (Meta D11 or Twilio D43), Telegram (D44), email (D47).

The conversation's channel picks the adapter for sends: `telegram` uses the Telegram Bot API;
`whatsapp` uses `WHATSAPP_PROVIDER` (Meta Graph or Twilio Sandbox). Inbound media is fetched by
the provider recorded on the stored event (`provider` field, absent means Meta), so changing a
setting never sends one provider's media id to another. Email (`email_dispatch`) is pulled by Apps
Script, so it has no push adapter; `ready` and `live_enabled` still gate it in `outbound.begin`. This module holds no authority: gates,
allowlists and the WhatsApp service window are checked by `outbound.begin` before any call here.
"""

from luma.core.config import settings

from . import email_dispatch, telegram_client, twilio_client, whatsapp_client


def adapter(channel: str = "whatsapp"):
    """Return the adapter module that sends on `channel`."""
    if channel == "telegram":
        return telegram_client
    if channel == "email":
        return email_dispatch
    return twilio_client if settings().whatsapp_provider == "twilio" else whatsapp_client


def ready(channel: str = "whatsapp") -> bool:
    """True when the channel's adapter has every credential a live send needs."""
    return adapter(channel).ready()


def live_enabled(channel: str) -> bool:
    """The per-channel master switch for real sends (`ENABLE_LIVE_WHATSAPP`, `_TELEGRAM`, `_EMAIL`)."""
    config = settings()
    if channel == "email":
        return config.enable_live_email
    return config.enable_live_telegram if channel == "telegram" else config.enable_live_whatsapp


def fetch_media(event: dict, maximum: int, allowed_mime: tuple[str, ...]) -> tuple[bytes, str]:
    """Fetch an inbound event's media through the provider that received it."""
    provider = event.get("provider")
    if provider == "telegram":
        return telegram_client.fetch_media(event["media_id"], maximum, allowed_mime, event.get("mime", ""))
    if provider == "twilio":
        return twilio_client.fetch_media(event["media_id"], maximum, allowed_mime, event.get("mime", ""))
    return whatsapp_client.fetch_media(event["media_id"], maximum, allowed_mime)
