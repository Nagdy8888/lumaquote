"""Read-only stock queries for the inventory screens, alerts and exports (decision D49).

Nothing here writes. Every query is scoped by `company_id` and only sees products of
non-retired sources. Available stock is always `on_hand - reserved`, computed here.
"""

from datetime import datetime
from uuid import UUID

# Products with their ledger row (zero stock and the default reorder level when the row is missing).
_STOCK_SELECT = """select p.id as product_id,p.sku,p.name,p.family,p.discontinued,
    coalesce(sl.on_hand,0) as on_hand,coalesce(sl.reserved,0) as reserved,
    coalesce(sl.on_hand,0)-coalesce(sl.reserved,0) as available,
    coalesce(sl.reorder_level,20) as reorder_level,
    (not p.discontinued and coalesce(sl.on_hand,0)-coalesce(sl.reserved,0)<=coalesce(sl.reorder_level,20)) as low
    from luma.products p
    join luma.sources s on s.company_id=p.company_id and s.id=p.source_id
    left join luma.stock_levels sl on sl.company_id=p.company_id and sl.product_id=p.id
    where p.company_id=%s and s.retired_at is null"""


def stock_rows(conn, company) -> list[dict]:
    """Return one stock row per current product: sku, name, family, on_hand, reserved, available,
    reorder_level and a `low` flag (available <= reorder_level; discontinued products are never low).
    Ordered by family then SKU. Read-only; a product without a ledger row shows zero stock.
    """
    return conn.execute(_STOCK_SELECT + " order by p.family,p.sku", (company,)).fetchall()


def low_stock_rows(conn, company) -> list[dict]:
    """Return the live low-stock list (the `low` rows of `stock_rows`), emptiest first.

    Low-stock alerts are never stored, so this list cannot go stale or need acknowledging.
    """
    return conn.execute(
        "select * from (" + _STOCK_SELECT + ") r where r.low order by r.available,r.sku", (company,)
    ).fetchall()


def low_stock_count(conn, company) -> int:
    """Return how many current, non-discontinued products have available <= their reorder level."""
    return conn.execute(
        "select count(*) n from (" + _STOCK_SELECT + ") r where r.low", (company,)
    ).fetchone()["n"]


def movements_page(
    conn, company, product_id: UUID | None = None, limit: int = 50, before: tuple[datetime, UUID] | None = None
) -> dict:
    """Return the newest stock movements, one keyset page at a time.

    `limit` is clamped to 1..200. `before` is the `next` cursor of the previous page, a
    (created_at, id) pair; rows strictly older are returned, newest first, so concurrent
    inserts never shift a page. Returns {"items": [...], "next": cursor-or-None}. Each item has
    the movement fields plus the product `sku` and `name`. Read-only, scoped by company.
    """
    limit = max(1, min(int(limit), 200))
    rows = conn.execute(
        """select m.id,m.product_id,p.sku,p.name,m.delta,m.kind,m.reference_id,m.reason,m.actor,m.created_at
        from luma.stock_movements m join luma.products p on p.company_id=m.company_id and p.id=m.product_id
        where m.company_id=%s and (%s::uuid is null or m.product_id=%s::uuid)
        and (%s::timestamptz is null or (m.created_at,m.id)<(%s::timestamptz,%s::uuid))
        order by m.created_at desc,m.id desc limit %s""",
        (
            company,
            product_id,
            product_id,
            before[0] if before else None,
            before[0] if before else None,
            before[1] if before else None,
            limit + 1,
        ),
    ).fetchall()
    items = rows[:limit]
    more = len(rows) > limit
    return {"items": items, "next": (items[-1]["created_at"], items[-1]["id"]) if more else None}


def open_alerts(conn, company) -> list[dict]:
    """Return the stored alerts still waiting for acknowledgement, newest first.

    Shortage and refused-acceptance alerts only; the live low-stock list is `low_stock_rows`.
    Each row carries the product `sku` and `name` when the alert names a product.
    """
    return conn.execute(
        """select a.*,p.sku,p.name from luma.stock_alerts a
        left join luma.products p on p.company_id=a.company_id and p.id=a.product_id
        where a.company_id=%s and a.status='open' order by a.created_at desc,a.id desc""",
        (company,),
    ).fetchall()
