"""Human and agent authority are rechecked at the final outbound boundary."""

from uuid import UUID

from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation
from luma.features.quotations.dispatch import check_quotation


def authorize_outbound(conn, item):
    """Resolve current ownership and actor permissions; separately require exact approval for any quotation document."""
    current = conversation(conn, item["company_id"], item["conversation_id"], lock=True)
    origin = item["payload"].get("origin", "agent")
    if origin not in ("agent", "staff"):
        raise DomainError("Unknown dispatch authority.")
    if origin == "staff":
        if item["kind"] != "reply" or current["owner"] != "staff":
            raise DomainError("Human reply ownership changed before dispatch.")
        try:
            author = UUID(item["payload"]["author_id"])
        except (KeyError, TypeError, ValueError):
            raise DomainError("A valid human reply author is required.") from None
        if not conn.execute(
            "select 1 from luma.memberships where user_id=%s and company_id=%s and active",
            (author, item["company_id"]),
        ).fetchone():
            raise DomainError("The reply author no longer has staff access.")
    elif current["owner"] != "agent":
        raise DomainError("Automation paused by staff.")
    quote = check_quotation(conn, item, current) if item["quote_id"] else None
    return current, quote
