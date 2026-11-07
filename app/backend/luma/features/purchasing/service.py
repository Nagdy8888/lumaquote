"""Supplier purchase orders and goods receipts (decision D49).

Authority: staff may read purchase orders; creating, receiving and cancelling are administrator-only
(403 from `require_admin`, role read from the verified membership). Stock rises only through
`inventory.ledger` (`receipt` movements referencing the purchase order). Status machine:
`ordered -> partially_received -> received`, and `ordered -> cancelled` only while nothing has been
received. Lock order: the purchase order, its lines, then stock levels in ascending product-id order.
Every write appends an audit event in the same transaction. Nothing here commits; the route's
`operation()` wrapper commits the effect with its idempotency record.
"""

from uuid import uuid4

from luma.core.audit import audit
from luma.core.errors import DomainError
from luma.core.identity import require_admin
from luma.core.numbering import next_number
from luma.features.inventory import ledger

LIST_LIMIT = 200


def order_rows(conn, company, order_id=None) -> list[dict]:
    """Return purchase orders newest first (at most 200) with their lines; optionally exactly one.

    Read only, scoped by company. Two queries regardless of the number of orders: the orders, then
    all their lines (with product SKU and name) at once, ordered by SKU.
    """
    orders = conn.execute(
        """select * from luma.purchase_orders where company_id=%s and (%s::uuid is null or id=%s)
        order by created_at desc,id desc limit %s""",
        (company, order_id, order_id, LIST_LIMIT),
    ).fetchall()
    lines = conn.execute(
        """select l.purchase_order_id,l.product_id,p.sku,p.name,l.quantity_ordered,l.quantity_received,l.unit_cost
        from luma.purchase_order_lines l join luma.products p on p.company_id=l.company_id and p.id=l.product_id
        where l.company_id=%s and l.purchase_order_id=any(%s::uuid[]) order by p.sku""",
        (company, [row["id"] for row in orders]),
    ).fetchall()
    by_order: dict = {}
    for line in lines:
        by_order.setdefault(line["purchase_order_id"], []).append(line)
    return [{**row, "lines": by_order.get(row["id"], [])} for row in orders]


def list_orders(conn, member) -> dict:
    """Return the company's purchase orders with lines for any staff member (read only)."""
    return {"items": order_rows(conn, member["company_id"])}


def create(conn, member, user, body) -> dict:
    """Record a purchase order in status `ordered` and return it (admin-only, 403 otherwise).

    Every product must belong to the company (422 otherwise). The number `PO-0001` comes from the
    company's serialized counter. Writes `purchase_orders`, `purchase_order_lines` and audit
    `purchase_order.created`; stock is untouched until goods are received.
    """
    require_admin(member, "create purchase orders")
    company = member["company_id"]
    wanted = [line.product_id for line in body.lines]
    known = conn.execute(
        "select id from luma.products where company_id=%s and id=any(%s::uuid[])", (company, wanted)
    ).fetchall()
    if len(known) != len(wanted):
        raise DomainError("A product on the purchase order does not exist.", 422)
    order = conn.execute(
        """insert into luma.purchase_orders(id,company_id,number,supplier,expected_on,notes,created_by)
        values(%s,%s,%s,%s,%s,%s,%s) returning id""",
        (uuid4(), company, next_number(conn, company, "purchase_order"), body.supplier, body.expected_on,
         body.notes or None, user),
    ).fetchone()
    for line in sorted(body.lines, key=lambda item: str(item.product_id)):
        conn.execute(
            """insert into luma.purchase_order_lines(company_id,purchase_order_id,product_id,quantity_ordered,unit_cost)
            values(%s,%s,%s,%s,%s)""",
            (company, order["id"], line.product_id, line.quantity, line.unit_cost),
        )
    audit(conn, company, user, "purchase_order.created", order["id"], lines=len(body.lines))
    return order_rows(conn, company, order["id"])[0]


def _lock(conn, company, order_id):
    """Lock a purchase order and its lines; return (order, lines keyed by product id). 404 outside the company."""
    order = conn.execute(
        "select * from luma.purchase_orders where company_id=%s and id=%s for update", (company, order_id)
    ).fetchone()
    if not order:
        raise DomainError("Purchase order not found.", 404)
    lines = conn.execute(
        """select * from luma.purchase_order_lines where company_id=%s and purchase_order_id=%s
        order by product_id for update""",
        (company, order_id),
    ).fetchall()
    return order, {line["product_id"]: line for line in lines}


def receive(conn, member, user, order_id, body) -> dict:
    """Receive goods against a purchase order, raise stock, and return the updated order (admin-only).

    409 when the order is cancelled or already fully received, or when a line would exceed its
    ordered quantity (cumulative received <= ordered; nothing is written then). 422 when a line
    names a product that is not on the order. Each line appends a `receipt` movement (positive delta,
    reference = the purchase order) and raises `quantity_received`; the status becomes `received`
    when every line is complete, otherwise `partially_received`. Levels are locked in ascending
    product-id order before any change. Audit `purchase_order.received`.
    """
    require_admin(member, "receive purchase orders")
    company = member["company_id"]
    order, lines = _lock(conn, company, order_id)
    if order["status"] in ("cancelled", "received"):
        raise DomainError(f"This purchase order is already {order['status']}.", 409)
    arrivals = {item.product_id: item.quantity for item in body.lines}
    for product_id, quantity in arrivals.items():
        line = lines.get(product_id)
        if line is None:
            raise DomainError("A received product is not on this purchase order.", 422)
        if line["quantity_received"] + quantity > line["quantity_ordered"]:
            raise DomainError("More was received than was ordered for a product.", 409)
    for product_id in arrivals:
        ledger.ensure_level(conn, company, product_id)
    ledger.lock_levels(conn, company, arrivals)
    for product_id, quantity in sorted(arrivals.items()):
        ledger.apply_movement(conn, company, product_id, quantity, "receipt", str(user), reference_id=order_id)
        conn.execute(
            "update luma.purchase_order_lines set quantity_received=quantity_received+%s where id=%s",
            (quantity, lines[product_id]["id"]),
        )
    complete = all(
        line["quantity_received"] + arrivals.get(product_id, 0) == line["quantity_ordered"]
        for product_id, line in lines.items()
    )
    conn.execute(
        "update luma.purchase_orders set status=%s,updated_at=now() where id=%s",
        ("received" if complete else "partially_received", order_id),
    )
    audit(conn, company, user, "purchase_order.received", order_id, number=order["number"], lines=len(arrivals))
    return order_rows(conn, company, order_id)[0]


def cancel(conn, member, user, order_id) -> dict:
    """Cancel a purchase order that has received nothing and return it (admin-only, 403 otherwise).

    409 when already cancelled, or when any quantity was received (stock already rose; correct it
    with an adjustment instead). Stock is untouched. Audit `purchase_order.cancelled`.
    """
    require_admin(member, "cancel purchase orders")
    company = member["company_id"]
    order, lines = _lock(conn, company, order_id)
    if order["status"] == "cancelled":
        raise DomainError("This purchase order is already cancelled.", 409)
    if order["status"] != "ordered" or any(line["quantity_received"] for line in lines.values()):
        raise DomainError("A purchase order with received goods cannot be cancelled.", 409)
    conn.execute("update luma.purchase_orders set status='cancelled',updated_at=now() where id=%s", (order_id,))
    audit(conn, company, user, "purchase_order.cancelled", order_id, number=order["number"])
    return order_rows(conn, company, order_id)[0]
