"""The single writer of stock: levels, movements and quote reservations (decision D49).

Every function takes the caller's open transaction and never commits. Nothing else in the
application may write `luma.stock_levels`, `luma.stock_movements` or `luma.stock_reservations`.

Invariants kept per company and product:
- `on_hand` equals the sum of that product's movement deltas.
- `reserved` equals the sum of its `held` reservation quantities.
- `0 <= reserved <= on_hand`; available is `on_hand - reserved` and is never stored.

Lock order (deadlock rule): the caller locks conversation, then quote; this module then locks
`stock_levels` rows always in ascending product-id order, and a function that touches several
products locks all of them before it changes any.
"""

from uuid import UUID, uuid4

from luma.core.audit import audit
from luma.core.errors import DomainError

MOVEMENT_KINDS = ("opening", "adjustment", "receipt", "order", "order_cancel")
RECONCILE_BATCH = 200
# Outbox states that mean the quotation may have reached, or still may reach, the customer.
LIVE_DELIVERY = ("queued", "submitting", "submitted", "delivered", "read", "local_delivered", "unknown")


def _ids(product_ids) -> list[UUID]:
    """Return the distinct product ids as UUIDs in the one global lock order (ascending)."""
    return sorted({UUID(str(value)) for value in product_ids})


def _line_quantities(quote) -> dict[UUID, int]:
    """Sum the quantities of a quotation's stored lines per product; lines of one product merge."""
    totals: dict[UUID, int] = {}
    for line in quote["content"]["lines"]:
        key = UUID(str(line["product_id"]))
        totals[key] = totals.get(key, 0) + int(line["quantity"])
    return totals


def lock_levels(conn, company, product_ids) -> dict[UUID, dict]:
    """Lock the stock level rows of the given products and return them keyed by product id.

    Rows are locked `for update` in ascending product-id order, the deadlock rule every
    caller shares. Products that have no level row are absent from the result; this function
    creates nothing. The lock lasts until the caller's transaction ends. Scoped by company.
    """
    ids = _ids(product_ids)
    if not ids:
        return {}
    rows = conn.execute(
        """select * from luma.stock_levels where company_id=%s and product_id=any(%s::uuid[])
        order by product_id for update""",
        (company, ids),
    ).fetchall()
    return {row["product_id"]: row for row in rows}


def ensure_level(conn, company, product_id) -> None:
    """Create a zero-stock level row for an existing product of the company when it has none.

    Idempotent. Lets a product added after the migration receive stock. A product that does
    not belong to the company gets no row; the caller's next lock then finds nothing.
    """
    conn.execute(
        """insert into luma.stock_levels(company_id,product_id)
        select company_id,id from luma.products where company_id=%s and id=%s
        on conflict(company_id,product_id) do nothing""",
        (company, product_id),
    )


def _move(conn, company, product_id, delta, kind, actor, reference_id, reason, reserved_delta) -> dict:
    """Apply one movement and an optional reserved change to a product in a single write.

    Locks the product's level row, refuses a result with `on_hand < 0` or `on_hand < reserved`
    (409), updates the level and appends the movement. `reserved_delta` is non-zero only when a
    reservation converts to an order movement, where both numbers must fall together. Returns
    the updated level row. The caller must already hold the right conversation and quote locks.
    """
    if kind not in MOVEMENT_KINDS:
        raise DomainError("Unknown stock movement.", 422)
    if type(delta) is not int or delta == 0:
        raise DomainError("A stock movement must change the quantity.", 422)
    if kind == "adjustment" and not 3 <= len((reason or "").strip()) <= 200:
        raise DomainError("An adjustment needs a reason of 3 to 200 characters.", 422)
    ensure_level(conn, company, product_id)
    level = lock_levels(conn, company, [product_id]).get(UUID(str(product_id)))
    if level is None:
        raise DomainError("Product not found.", 404)
    on_hand = level["on_hand"] + delta
    reserved = level["reserved"] + reserved_delta
    if on_hand < 0 or on_hand < reserved:
        raise DomainError("Stock cannot fall below the quantity reserved for quotations.", 409)
    updated = conn.execute(
        """update luma.stock_levels set on_hand=%s,reserved=%s,updated_at=now()
        where company_id=%s and product_id=%s returning *""",
        (on_hand, reserved, company, product_id),
    ).fetchone()
    conn.execute(
        """insert into luma.stock_movements(id,company_id,product_id,delta,kind,reference_id,reason,actor)
        values(%s,%s,%s,%s,%s,%s,%s,%s)""",
        (uuid4(), company, product_id, delta, kind, reference_id, reason, actor),
    )
    return updated


def apply_movement(conn, company, product_id, delta, kind, actor, reference_id=None, reason=None) -> dict:
    """Append one stock movement and move on-hand by `delta`; return the updated level row.

    Refuses (409) a result below zero or below the quantity reserved for quotations, and
    rejects a zero delta, an unknown kind or an adjustment without a 3 to 200 character reason
    (422); an unknown product is a 404. Creates the level row for a product that has none.
    Authority is the caller's: adjustments and receipts are admin-only routes, order movements
    follow staff confirmation. Side effects: one `stock_levels` update and one
    `stock_movements` insert, no commit.
    """
    return _move(conn, company, product_id, delta, kind, actor, reference_id, reason, 0)


def seed_opening(conn, company, product_id, quantity: int, actor: str = "seed") -> bool:
    """Give a new product its level row and, when quantity > 0, an `opening` movement.

    Used by the local seed and by test fixtures that create products. Idempotent: a product that
    already has a level row is left alone and the call returns False. A zero quantity creates the
    level row without a movement (movements need a non-zero delta); the invariants still hold.
    """
    inserted = conn.execute(
        """insert into luma.stock_levels(company_id,product_id) values(%s,%s)
        on conflict(company_id,product_id) do nothing returning product_id""",
        (company, product_id),
    ).fetchone()
    if not inserted:
        return False
    if quantity > 0:
        apply_movement(conn, company, product_id, quantity, "opening", actor)
    return True


def reserve_quote(conn, company, quote) -> dict[UUID, int]:
    """Hold stock for every line of an approved quotation, all or nothing; return held quantities.

    Locks the lines' levels in product-id order, requires `available >= quantity` for every
    line (409 "Stock changed. Create a new revision." otherwise, nothing written), inserts one
    `held` reservation per product and raises `reserved`. Idempotent on (quote, product): a line
    that is already held is skipped. A line whose reservation was already released or converted
    cannot be held again (409). The caller holds the conversation and quote locks.
    """
    wanted = _line_quantities(quote)
    levels = lock_levels(conn, company, wanted)
    existing = {
        row["product_id"]: row
        for row in conn.execute(
            "select * from luma.stock_reservations where company_id=%s and quote_id=%s",
            (company, quote["id"]),
        ).fetchall()
    }
    fresh = {}
    for product_id, quantity in wanted.items():
        previous = existing.get(product_id)
        if previous:
            if previous["status"] != "held":
                raise DomainError("This quotation's stock reservation is already closed.", 409)
            continue
        level = levels.get(product_id)
        if not level or level["on_hand"] - level["reserved"] < quantity:
            raise DomainError("Stock changed. Create a new revision.", 409)
        fresh[product_id] = quantity
    for product_id, quantity in sorted(fresh.items()):
        conn.execute(
            """insert into luma.stock_reservations(id,company_id,quote_id,product_id,quantity)
            values(%s,%s,%s,%s,%s)""",
            (uuid4(), company, quote["id"], product_id, quantity),
        )
        conn.execute(
            """update luma.stock_levels set reserved=reserved+%s,updated_at=now()
            where company_id=%s and product_id=%s""",
            (quantity, company, product_id),
        )
    return wanted


def held_quantities(conn, company, quote_id) -> dict[UUID, int]:
    """Return the quantity currently held for a quotation, keyed by product id; empty when nothing is held.

    A read only: no lock, no write. The dispatch freshness check uses it to prove that an
    approved quotation still owns its stock. The caller holds the quote lock, so a release
    (which also needs that lock or the reconcile row lock) cannot interleave.
    """
    return {
        row["product_id"]: row["quantity"]
        for row in conn.execute(
            "select product_id,quantity from luma.stock_reservations where company_id=%s and quote_id=%s and status='held'",
            (company, quote_id),
        ).fetchall()
    }


def _held(conn, company, quote_id) -> list[dict]:
    """Lock a quotation's levels, then its held reservations; return the held rows by product id.

    The reservation product ids are read first without locking so the levels are locked before
    the reservation rows, matching the order `reserve_quote` uses. Returns an empty list when
    nothing is held, which makes release and convert idempotent.
    """
    ids = [
        row["product_id"]
        for row in conn.execute(
            "select product_id from luma.stock_reservations where company_id=%s and quote_id=%s and status='held'",
            (company, quote_id),
        ).fetchall()
    ]
    if not ids:
        return []
    lock_levels(conn, company, ids)
    return conn.execute(
        """select * from luma.stock_reservations where company_id=%s and quote_id=%s and status='held'
        order by product_id for update""",
        (company, quote_id),
    ).fetchall()


def release_quote(conn, company, quote_id, reason: str) -> int:
    """Release every held reservation of a quotation and lower `reserved`; return how many.

    `reason` (at most 60 characters, for example "declined" or "superseded") is stored on each
    reservation. Idempotent: with nothing held it changes nothing and returns 0, so every
    release hook may call it freely. Never writes a movement; on-hand is unchanged.
    """
    held = _held(conn, company, quote_id)
    for row in held:
        conn.execute(
            """update luma.stock_reservations set status='released',release_reason=%s,closed_at=now()
            where id=%s""",
            (reason[:60], row["id"]),
        )
        conn.execute(
            """update luma.stock_levels set reserved=reserved-%s,updated_at=now()
            where company_id=%s and product_id=%s""",
            (row["quantity"], company, row["product_id"]),
        )
    return len(held)


def convert_quote(conn, company, quote_id, order_id, actor: str) -> int:
    """Turn a quotation's held reservations into stock leaving on-hand; return how many lines.

    For each held line, mark it `converted`, lower `reserved` and append an `order` movement
    (negative delta, `reference_id` = the order) in one step, so available never changes.
    Idempotent: with nothing held it returns 0. Called when staff confirm an order; the
    caller holds the conversation and order locks and records the audit event.
    """
    held = _held(conn, company, quote_id)
    for row in held:
        conn.execute(
            "update luma.stock_reservations set status='converted',closed_at=now() where id=%s", (row["id"],)
        )
        _move(
            conn,
            company,
            row["product_id"],
            -row["quantity"],
            "order",
            actor,
            order_id,
            None,
            -row["quantity"],
        )
    return len(held)


def reconcile(conn, company=None) -> dict[str, int]:
    """Release reservations that no longer protect a live quotation; return counts.

    Examines up to 200 quotations with held stock (all companies when `company` is None; rows
    another transaction has locked are skipped and retried on the next call). A quotation is
    released when:
    - its status is not `approved` or `accepted` (superseded, rejected, declined, expired);
    - it is `approved` and `valid_until <= now()`: released and the quotation marked `expired`;
    - it is `approved` and its quotation outbox has a `blocked` or `failed` row and no row that is
      queued, in flight, delivered or `unknown` (an unknown delivery may have reached the customer).
    An `accepted` quotation keeps its hold until staff confirm or cancel the order. All the
    levels involved are locked in product-id order before any change. Audit events use actor
    `system`. The caller owns the transaction (the worker runs this once per tick).
    """
    candidates = conn.execute(
        """select q.id,q.company_id,q.status,q.valid_until<=now() as expired,
        exists(select 1 from luma.outbox o where o.company_id=q.company_id and o.quote_id=q.id
            and o.kind='quotation' and o.status in ('blocked','failed')) as dead,
        exists(select 1 from luma.outbox o where o.company_id=q.company_id and o.quote_id=q.id
            and o.kind='quotation' and o.status=any(%s)) as live
        from luma.quotes q
        where q.id in (select r.quote_id from luma.stock_reservations r
            where r.status='held' and (%s::uuid is null or r.company_id=%s::uuid))
        order by q.created_at limit %s for update of q skip locked""",
        (list(LIVE_DELIVERY), company, company, RECONCILE_BATCH),
    ).fetchall()
    plan = []
    for row in candidates:
        if row["status"] not in ("approved", "accepted"):
            plan.append((row, "quote_" + row["status"]))
        elif row["status"] == "approved" and row["expired"]:
            plan.append((row, "expired"))
        elif row["status"] == "approved" and row["dead"] and not row["live"]:
            plan.append((row, "delivery_failed"))
    if not plan:
        return {"released": 0, "expired": 0}
    held = conn.execute(
        "select company_id,product_id from luma.stock_reservations where status='held' and quote_id=any(%s::uuid[])",
        ([row["id"] for row, _ in plan],),
    ).fetchall()
    for tenant in sorted({row["company_id"] for row, _ in plan}, key=str):
        lock_levels(conn, tenant, [h["product_id"] for h in held if h["company_id"] == tenant])
    expired = 0
    for row, reason in plan:
        count = release_quote(conn, row["company_id"], row["id"], reason)
        if reason == "expired":
            conn.execute("update luma.quotes set status='expired' where id=%s and status='approved'", (row["id"],))
            expired += 1
        audit(conn, row["company_id"], "system", "stock.released", row["id"], reason=reason, lines=count)
    return {"released": len(plan), "expired": expired}
