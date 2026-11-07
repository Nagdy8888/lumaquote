"""Bind a customer's accept or decline to the one sent quotation they may answer (decision D49).

Authority: a customer answer comes from an allowlisted sender on their own chat. It can accept or
decline only the newest revision of that chat's conversation, and only while that revision is
approved, unexpired, addressed to this recipient, still holds its stock and was actually sent.
Everything else is refused in code. The answer never changes a price or a quantity: the order
copies the immutable quotation content. A pending order does not move on-hand stock; staff confirm
or cancel it later, and the reservation made at approval stays held until then.

The caller holds the conversation lock and an open transaction, and has already stored the
customer message (that store is the idempotency point for a redelivered provider message).
Lock order: conversation (caller), quote, stock levels. Nothing here commits.
"""

from decimal import Decimal
from uuid import uuid4

from luma.core.audit import audit
from luma.features.conversations.service import queue_notice
from luma.features.inventory import ledger

SENT = ("submitted", "delivered", "read", "local_delivered")
ACCEPTED_NOTICE = (
    "Thank you. Your acceptance of quotation {number}, revision {revision}, is recorded. "
    "Our sales team will confirm your order."
)
DECLINED_NOTICE = "Thank you. Quotation {number} is declined. Send a new request any time."
REFUSED_NOTICE = "This quotation can no longer be accepted. Our sales team will contact you."


def refusal_reason(conn, current, quote, quote_id) -> str | None:
    """Return an opaque code for why `quote` cannot be answered now, or None when it can.

    Checks, in order: a quotation exists, a button's quote id matches it, it is approved,
    unexpired, addressed to this conversation's recipient, was sent (outbox `submitted`,
    `delivered`, `read` or `local_delivered`; `unknown` is not enough) and still holds all of
    its stock. Read only; the caller has locked the quote row.
    """
    if quote is None:
        return "no_quotation"
    if quote_id is not None and str(quote["id"]) != str(quote_id):
        return "not_current_quotation"
    if quote["status"] != "approved":
        return "not_open"
    if quote["valid_until"] <= conn.execute("select now() as now").fetchone()["now"]:
        return "expired"
    if quote["recipient"] != current["recipient"]:
        return "recipient_mismatch"
    sent = conn.execute(
        "select 1 from luma.outbox where company_id=%s and quote_id=%s and kind='quotation' and status=any(%s)",
        (quote["company_id"], quote["id"], list(SENT)),
    ).fetchone()
    if not sent:
        return "not_sent"
    wanted: dict[str, int] = {}
    for line in quote["content"]["lines"]:
        wanted[str(line["product_id"])] = wanted.get(str(line["product_id"]), 0) + int(line["quantity"])
    held = {str(key): value for key, value in ledger.held_quantities(conn, quote["company_id"], quote["id"]).items()}
    return None if held == wanted else "stock_not_held"


def next_order_number(conn, company) -> str:
    """Return the next `SO-0001` style number for the company, serialized by a row lock.

    The counter row is created on first use. The increment is a single upsert, so two concurrent
    acceptances queue on the row lock and receive different numbers. Numbers are gap-tolerant:
    a rolled-back transaction rolls the increment back with it.
    """
    row = conn.execute(
        """insert into luma.document_counters(company_id,kind,next_value) values(%s,'order',2)
        on conflict(company_id,kind) do update set next_value=document_counters.next_value+1
        returning next_value""",
        (company,),
    ).fetchone()
    return f"SO-{row['next_value'] - 1:04d}"


def create_order(conn, company, current, quote, via: str) -> dict:
    """Insert the pending order and its lines from the accepted quotation's stored content.

    Prices, names and totals are copied exactly as approved and never recomputed. Lines of one
    product are merged (the table has one row per product). Customer name and company come from
    the conversation. Returns the order row. Writes `orders` and `order_lines` only.
    """
    content = quote["content"]
    order = conn.execute(
        """insert into luma.orders(id,company_id,number,conversation_id,quote_id,revision,accepted_via,
        currency,total,customer_name,customer_company) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning *""",
        (
            uuid4(),
            company,
            next_order_number(conn, company),
            current["id"],
            quote["id"],
            quote["revision"],
            "telegram_button" if via == "telegram_button" else "reply",
            content["currency"],
            content["total"],
            current["customer_name"],
            current["customer_company"],
        ),
    ).fetchone()
    merged: dict[str, dict] = {}
    for line in content["lines"]:
        key = str(line["product_id"])
        if key in merged:
            merged[key]["quantity"] += int(line["quantity"])
            merged[key]["line_total"] += Decimal(line["line_total"])
        else:
            merged[key] = {**line, "quantity": int(line["quantity"]), "line_total": Decimal(line["line_total"])}
    for key, line in sorted(merged.items()):
        conn.execute(
            """insert into luma.order_lines(order_id,company_id,product_id,sku,name,quantity,unit_price,line_total)
            values(%s,%s,%s,%s,%s,%s,%s,%s)""",
            (order["id"], company, key, line["sku"], line["name"], line["quantity"], line["unit_price"], line["line_total"]),
        )
    return order


def answer_quote(conn, company, current, answer, via, quote_id=None, provider_id=None) -> dict:
    """Apply a customer's 'accept' or 'decline' under the binding rules; return the outcome.

    `via` is `reply` (typed text, any channel) or `telegram_button`; `quote_id` is the button's
    quotation and must be the conversation's current target. `provider_id` only names the
    fixed notice, so a redelivered message queues it once. Outcomes (`outcome` key):
    - `accepted`: quote -> `accepted`, pending order created, stock hold kept, conversation
      `order_pending`, audit `order.accepted`.
    - `already_accepted`: the newest quote is already accepted; no new order and no other change
      (the conversation status is restated), and the same confirmation notice is queued again.
    - `declined`: quote -> `declined`, hold released (reason `declined`), conversation `declined`,
      audit `quotation.declined`.
    - `refused`: nothing is bound; a `stock_alerts` row (`acceptance_refused`) is inserted,
      the conversation becomes `needs_staff` and audit `order.acceptance_refused` records the
      opaque reason code. No agent job is queued and no revision is superseded.
    Notices are fixed texts queued only while the agent owns the conversation; under staff
    ownership the answer is applied and the conversation is marked `needs_staff` for staff.
    A refusal raises nothing; database errors propagate and roll the caller back.
    """
    newest = conn.execute(
        """select * from luma.quotes where company_id=%s and conversation_id=%s
        order by revision desc limit 1 for update""",
        (company, current["id"]),
    ).fetchone()
    key = f"inbound-notice:{provider_id or uuid4()}"
    if (
        newest
        and newest["status"] == "accepted"
        and answer == "accept"
        and (quote_id is None or str(newest["id"]) == str(quote_id))
    ):
        order = conn.execute(
            "select id from luma.orders where company_id=%s and quote_id=%s", (company, newest["id"])
        ).fetchone()
        status = "order_pending" if current["owner"] == "agent" else "needs_staff"
        conn.execute("update luma.conversations set status=%s,updated_at=now() where id=%s", (status, current["id"]))
        queue_notice(conn, company, current, ACCEPTED_NOTICE.format(**newest), key)
        return {"outcome": "already_accepted", "order_id": order["id"] if order else None}
    reason = refusal_reason(conn, current, newest, quote_id)
    if reason:
        conn.execute(
            "insert into luma.stock_alerts(company_id,kind,conversation_id,quote_id) values(%s,'acceptance_refused',%s,%s)",
            (company, current["id"], newest["id"] if newest else None),
        )
        conn.execute("update luma.conversations set status='needs_staff',updated_at=now() where id=%s", (current["id"],))
        queue_notice(conn, company, current, REFUSED_NOTICE, key)
        audit(conn, company, "customer", "order.acceptance_refused", current["id"], reason=reason, answer=answer, via=via)
        return {"outcome": "refused", "reason": reason}
    status = "needs_staff" if current["owner"] != "agent" else {"accept": "order_pending", "decline": "declined"}[answer]
    if answer == "accept":
        conn.execute("update luma.quotes set status='accepted' where id=%s", (newest["id"],))
        order = create_order(conn, company, current, newest, via)
        conn.execute("update luma.conversations set status=%s,updated_at=now() where id=%s", (status, current["id"]))
        queue_notice(conn, company, current, ACCEPTED_NOTICE.format(**newest), key)
        audit(conn, company, "customer", "order.accepted", order["id"], number=order["number"], quote_id=str(newest["id"]), via=via)
        return {"outcome": "accepted", "order_id": order["id"], "number": order["number"]}
    conn.execute("update luma.quotes set status='declined' where id=%s", (newest["id"],))
    ledger.release_quote(conn, company, newest["id"], "declined")
    conn.execute("update luma.conversations set status=%s,updated_at=now() where id=%s", (status, current["id"]))
    queue_notice(conn, company, current, DECLINED_NOTICE.format(**newest), key)
    audit(conn, company, "customer", "quotation.declined", newest["id"], via=via)
    return {"outcome": "declined"}
