"""Development recipient allowlists shared by messaging ingress and egress (WhatsApp and Telegram)."""

from luma.core.config import settings


def allowed_senders() -> set[str]:
    """Parse `WHATSAPP_TEST_RECIPIENTS` (comma-separated numbers, optional leading +); empty admits nobody.

    The same list gates inbound senders and outbound recipients, so a number that is not an
    authorized test recipient can neither create a conversation nor receive a message.
    """
    return {value.strip().lstrip("+") for value in settings().whatsapp_test_recipients.split(",") if value.strip()}


def allowed_telegram_users() -> set[str]:
    """Parse `TELEGRAM_ALLOWED_USERS` (comma-separated numeric user ids); empty admits nobody.

    Only private chats are accepted, where the chat id equals the user id, so this one list
    gates who can open a Telegram conversation and who the bot may send to.
    """
    return {value.strip() for value in settings().telegram_allowed_users.split(",") if value.strip().isdigit()}


def allowed(channel: str) -> set[str]:
    """Return the allowlist for a messaging channel (`whatsapp` or `telegram`)."""
    return allowed_telegram_users() if channel == "telegram" else allowed_senders()
