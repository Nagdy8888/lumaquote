"""Staff confirmation and cancellation of customer orders, and the order list (decision D49).

Authority: any active staff member (salesperson or administrator) may confirm or cancel; the
customer never can. Stock moves only through `inventory.ledger`:
- confirm converts the quotation's held reservations into `order` movements (stock leaves on-hand);
- cancel of a pending order releases the hold (reason `order_cancelled`), on-hand is unchanged;
- cancel of a confirmed order returns each line with an `order_cancel` movement (positive delta).

Lock order (deadlock rule): conversation, quote, order, then stock levels in ascending product-id
order (the ledger). Every write appends an audit event in the same transaction. Nothing here
commits; the route's `operation()` wrapper commits the effect with its idempotency record.
"""

from luma.core.audit import audit
from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation
from luma.features.conversations.service import queue_notice
from luma.features.inventory import ledger

LIST_LIMIT = 200
CONFIRMED_NOTICE = "Your order {number} is confirmed. Our sales team will contact you about delivery."
ORDER_STATUSES = ("pending", "confirmed", "cancelled")


def order_rows(conn, company, status: str | None = None, order_id=None) -> list[dict]:
    """Return orders newest first (at most 200) with their lines; optionally one status or one order.

    Read only, scoped by company. Two queries regardless of the number of orders: the orders, then
    all their lines at once. Each order carries `lines` ordered by SKU.
    """
    orders = conn.execute(
        """select * from luma.orders where company_id=%s and (%s::text is null or status=%s)
        and (%s::uuid is null or id=%s) order by created_at desc,id desc limit %s""",
        (company, status, status, order_id, order_id, LIST_LIMIT),
    ).fetchall()
    lines = conn.execute(
        """select order_id,product_id,sku,name,quantity,unit_price,line_total from luma.order_lines
        where company_id=%s and order_id=any(%s::uuid[]) order by sku""",
        (company, [row["id"] for row in orders]),
    ).fetchall()
    by_order: dict = {}
    for line in lines:
        by_order.setdefault(line["order_id"], []).append(line)
    return [{**row, "lines": by_order.get(row["id"], [])} for row in orders]


def list_orders(conn, member, status: str | None) -> dict:
    """Return the company's orders (optionally one status, 422 for an unknown status); read only."""
    if status is not None and status not in ORDER_STATUSES:
        raise DomainError("Unknown order status.", 422)
    return {"items": order_rows(conn, member["company_id"], status)}


def _lock(conn, company, order_id):
    """Lock the order's conversation, quote and the order itself, in that order; return (conversation, order).

    The order is read unlocked first only to learn its immutable conversation and quote ids (404 for
    an id outside the company, so no tenant is disclosed). The status is read again after the lock,
    so a concurrent confirm or cancel is seen by the caller.
    """
    found = conn.execute(
        "select conversation_id,quote_id from luma.orders where company_id=%s and id=%s", (company, order_id)
    ).fetchone()
    if not found:
        raise DomainError("Order not found.", 404)
    current = conversation(conn, company, found["conversation_id"], lock=True)
    conn.execute("select 1 from luma.quotes where company_id=%s and id=%s for update", (company, found["quote_id"]))
    order = conn.execute(
        "select * from luma.orders where company_id=%s and id=%s for update", (company, order_id)
    ).fetchone()
    return current, order


def _line_quantities(conn, company, order_id) -> dict:
    """Return the order's line quantities keyed by product id, summed per product."""
    totals: dict = {}
    for row in conn.execute(
        "select product_id,quantity from luma.order_lines where company_id=%s and order_id=%s", (company, order_id)
    ).fetchall():
        totals[row["product_id"]] = totals.get(row["product_id"], 0) + row["quantity"]
    return totals


def confirm(conn, member, user, order_id) -> dict:
    """Confirm a pending order: stock leaves on-hand once, the conversation becomes `ordered`; return the order.

    409 when the order is already confirmed or cancelled. 409 "The stock held for this order is no
    longer reserved" when the quotation's reservation was released by some other path (staff should
    cancel and re-quote). Otherwise `ledger.convert_quote` writes one `order` movement per line and
    lowers `reserved` by the same amount. Queues the fixed customer notice (no prices, no dates)
    only while the agent owns the conversation. A customer message that arrived after the
    acceptance (a request parked by `service.hold_for_pending_order`) is still unanswered, so the
    conversation then stays `needs_staff` instead of `ordered`. Audit `order.confirmed`.
    """
    company = member["company_id"]
    current, order = _lock(conn, company, order_id)
    if order["status"] != "pending":
        raise DomainError(f"This order is already {order['status']}.", 409)
    if ledger.held_quantities(conn, company, order["quote_id"]) != _line_quantities(conn, company, order_id):
        raise DomainError("The stock held for this order is no longer reserved. Cancel the order and re-quote.", 409)
    ledger.convert_quote(conn, company, order["quote_id"], order_id, actor=str(user))
    conn.execute(
        "update luma.orders set status='confirmed',confirmed_by=%s,confirmed_at=now() where id=%s", (user, order_id)
    )
    waiting = conn.execute(
        "select 1 from luma.orders where id=%s and %s>accepted_at", (order_id, current["last_customer_at"])
    ).fetchone()
    conn.execute(
        "update luma.conversations set status=%s,updated_at=now() where id=%s",
        ("needs_staff" if waiting else "ordered", current["id"]),
    )
    queue_notice(conn, company, current, CONFIRMED_NOTICE.format(number=order["number"]), f"order-confirmed:{order_id}")
    audit(conn, company, user, "order.confirmed", order_id, number=order["number"])
    return order_rows(conn, company, order_id=order_id)[0]


def cancel(conn, member, user, order_id, reason: str) -> dict:
    """Cancel a pending or confirmed order and give its stock back; return the order.

    Pending: the quotation's hold is released (reason `order_cancelled`), on-hand is unchanged.
    Confirmed: one `order_cancel` movement per line returns the quantity to on-hand, referencing
    the order. Already cancelled: 409. The accepted quotation becomes `superseded` so staff can draft
    a new revision. The conversation goes to `needs_staff` so a person follows up with the
    customer; no customer notice is sent. `reason` (3-200 characters, validated by the
    schema) is stored on the order. Audit `order.cancelled` (the reason text stays on the order).
    """
    company = member["company_id"]
    current, order = _lock(conn, company, order_id)
    if order["status"] == "cancelled":
        raise DomainError("This order is already cancelled.", 409)
    if order["status"] == "pending":
        ledger.release_quote(conn, company, order["quote_id"], "order_cancelled")
    else:
        quantities = _line_quantities(conn, company, order_id)
        for product_id in quantities:
            ledger.ensure_level(conn, company, product_id)
        ledger.lock_levels(conn, company, quantities)
        for product_id, quantity in sorted(quantities.items()):
            ledger.apply_movement(conn, company, product_id, quantity, "order_cancel", str(user), reference_id=order_id)
    conn.execute(
        """update luma.orders set status='cancelled',cancelled_by=%s,cancelled_at=now(),cancel_reason=%s
        where id=%s""",
        (user, reason, order_id),
    )
    # The accepted quotation is dead; `superseded` lets staff draft a new revision (drafting refuses
    # to revise an `accepted` one) and makes a later customer "accept" a refusal, not a second order.
    conn.execute("update luma.quotes set status='superseded' where id=%s and status='accepted'", (order["quote_id"],))
    conn.execute("update luma.conversations set status='needs_staff',updated_at=now() where id=%s", (current["id"],))
    audit(conn, company, user, "order.cancelled", order_id, number=order["number"], was=order["status"])
    return order_rows(conn, company, order_id=order_id)[0]
