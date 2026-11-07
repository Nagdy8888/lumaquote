"""Staff stock actions: adjustments, reorder levels and alert acknowledgement (decision D49).

Authority: adjustments and reorder levels are administrator-only (checked here, from the verified
membership role); acknowledging an alert is open to every staff member. Stock numbers change only
through `ledger`. Every write appends an audit event in the same transaction. Nothing here commits;
the route's `operation()` wrapper commits the effect together with the idempotency record.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from luma.core.audit import audit
from luma.core.errors import DomainError
from luma.core.identity import require_admin

from . import ledger, queries


def level_view(level) -> dict:
    """Shape a `stock_levels` row as the position the API returns (available derived, never stored)."""
    return {
        "product_id": level["product_id"],
        "on_hand": level["on_hand"],
        "reserved": level["reserved"],
        "available": level["on_hand"] - level["reserved"],
        "reorder_level": level["reorder_level"],
    }


def adjust(conn, member, user, body) -> dict:
    """Apply an administrator's signed stock correction and return the product's new position.

    Admin-only (403). Delegates to `ledger.apply_movement(kind='adjustment')`, which refuses a
    result below zero or below the quantity reserved for quotations (409) and an unknown product
    (404). Side effects: one level update, one movement, audit `stock.adjusted` (the free-text
    reason stays in the movement, not in the audit detail).
    """
    require_admin(member, "adjust stock")
    company = member["company_id"]
    level = ledger.apply_movement(
        conn, company, body.product_id, body.delta, "adjustment", str(user), reason=body.reason
    )
    audit(conn, company, user, "stock.adjusted", body.product_id, delta=body.delta, on_hand=level["on_hand"])
    return level_view(level)


def set_reorder_level(conn, member, user, body) -> dict:
    """Set a product's low-stock threshold and return its position (admin-only, 403 otherwise).

    Delegates the write to `ledger.set_reorder_level` (404 for a product outside the company).
    Side effects: one level update and audit `stock.reorder_level_set`; no stock movement.
    """
    require_admin(member, "change reorder levels")
    company = member["company_id"]
    level = ledger.set_reorder_level(conn, company, body.product_id, body.reorder_level)
    audit(conn, company, user, "stock.reorder_level_set", body.product_id, reorder_level=body.reorder_level)
    return level_view(level)


def stock_view(conn, member) -> dict:
    """Return the stock table rows and the low-stock count for the staff member's company (read only)."""
    rows = queries.stock_rows(conn, member["company_id"])
    return {"items": rows, "low_count": sum(1 for row in rows if row["low"])}


EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def parse_cursor(value: str | None) -> tuple[datetime, UUID] | None:
    """Decode a movements `before` cursor ("<microseconds since 1970 UTC>_<uuid>"); 422 when malformed.

    The cursor uses only digits, letters and `_`, so it needs no URL escaping.
    """
    if not value:
        return None
    try:
        micros, ident = value.split("_", 1)
        if not micros.isdigit():
            raise ValueError
        return EPOCH + timedelta(microseconds=int(micros)), UUID(ident)
    except (ValueError, OverflowError):
        raise DomainError("The page cursor is not valid.", 422) from None


def movements(conn, member, product_id, limit: int, before: str | None) -> dict:
    """Return one newest-first page of movements (optionally one product) and the next cursor (read only)."""
    page = queries.movements_page(conn, member["company_id"], product_id, limit, parse_cursor(before))
    cursor = page["next"]
    token = f"{(cursor[0] - EPOCH) // timedelta(microseconds=1)}_{cursor[1]}" if cursor else None
    return {"items": page["items"], "next": token}


def alerts(conn, member) -> dict:
    """Return open stored alerts, the live low-stock products and counts (read only)."""
    company = member["company_id"]
    stored = queries.open_alerts(conn, company)
    low = queries.low_stock_rows(conn, company)
    shortage = sum(1 for row in stored if row["kind"] == "shortage")
    return {
        "alerts": stored,
        "low_stock": low,
        "counts": {
            "shortage": shortage,
            "acceptance_refused": len(stored) - shortage,
            "low_stock": len(low),
            "total": len(stored) + len(low),
        },
    }


def acknowledge(conn, member, user, alert_id) -> dict:
    """Mark an open alert acknowledged by this staff member; 404 when unknown, 409 when already acknowledged.

    Open to every staff role. One conditional update decides the race, so two staff members
    acknowledging together produce one success and one 409. Audit `alert.acknowledged`.
    """
    company = member["company_id"]
    row = conn.execute(
        """update luma.stock_alerts set status='acknowledged',acknowledged_by=%s,acknowledged_at=now()
        where company_id=%s and id=%s and status='open' returning id""",
        (user, company, alert_id),
    ).fetchone()
    if not row:
        known = conn.execute(
            "select 1 from luma.stock_alerts where company_id=%s and id=%s", (company, alert_id)
        ).fetchone()
        if known:
            raise DomainError("This alert is already acknowledged.", 409)
        raise DomainError("Alert not found.", 404)
    audit(conn, company, user, "alert.acknowledged", alert_id)
    return {"id": alert_id, "status": "acknowledged"}
