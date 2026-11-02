"""Development recipient allowlist shared by WhatsApp ingress and egress."""

from luma.core.config import settings


def allowed_senders() -> set[str]:
    """Parse `WHATSAPP_TEST_RECIPIENTS` (comma-separated numbers, optional leading +); empty admits nobody.

    The same list gates inbound senders and outbound recipients, so a number that is not an
    authorized test recipient can neither create a conversation nor receive a message.
    """
    return {value.strip().lstrip("+") for value in settings().whatsapp_test_recipients.split(",") if value.strip()}
