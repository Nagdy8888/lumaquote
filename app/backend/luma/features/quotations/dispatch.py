from datetime import UTC, datetime

from luma.core.errors import DomainError

from .freshness import check_snapshot
from .rules import assert_dispatchable


def check_quotation(conn, item, current):
    """Verify this immutable quotation's exact approval, active approver, recipient, expiry, and current commercial snapshot."""
    quote = None
    if item["quote_id"]:
        quote = conn.execute(
            "select * from luma.quotes where company_id=%s and id=%s for update",
            (item["company_id"], item["quote_id"]),
        ).fetchone()
        approval = conn.execute("select * from luma.approvals where quote_id=%s", (quote["id"],)).fetchone()
        allowed = (
            conn.execute(
                "select 1 from luma.memberships where user_id=%s and company_id=%s and active",
                (approval["approver"], item["company_id"]),
            ).fetchone()
            if approval
            else None
        )
        if not allowed:
            raise DomainError("Approver no longer has active staff access.")
        assert_dispatchable(quote, approval, current, datetime.now(UTC))
        check_snapshot(conn, quote, current)
    return quote
