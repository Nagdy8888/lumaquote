"""Staff order, purchase-order, adjustment and alert routes on real PostgreSQL (D49, task T4).

Everything runs through the real HTTP routes with a real Supabase Auth token, in isolated synthetic
tenants (`environment`); the customer side (accept) uses the real local-test reply route, and the
shortage alert is written by the real `prepare` node. Rows are read back with an owner connection.
Label: local. The fixture user is an administrator; role tests flip its membership to salesperson.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg
import pytest
from luma.features.inventory import ledger
from luma_agent.nodes.workflow import prepare
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from test_manual_workflow import create_request, get_detail, make_draft, post
from test_preparation_conflicts import running_job
from test_stock_acceptance import reply, sent
from test_stock_ledger import assert_invariants
from test_stock_reservations import approved, stock

DL1, DL2 = 0, 1
CONFIRMED = "Your order {number} is confirmed. Our sales team will contact you about delivery."


@pytest.fixture
def conn(environment):
    """Owner connection (bypasses row security) used to arrange and inspect; callers commit explicitly."""
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as connection:
        yield connection


def get(env, path):
    """GET an authenticated staff route."""
    return env["api"].get("/api" + path, headers=env["headers"])


def rows(conn_, sql, *args):
    """Run a query on a fresh snapshot and return all rows."""
    conn_.commit()
    return conn_.execute(sql, args).fetchall()


def as_salesperson(conn_, env):
    """Demote the fixture user's membership to salesperson (roles are read from the database per request)."""
    conn_.execute("update luma.memberships set role='salesperson' where user_id=%s", (env["user"],))
    conn_.commit()


def pending_order(env, conn_):
    """Customer accepts a delivered quotation; return (conversation id, quote id, order id)."""
    cid, qid = sent(env, conn_)
    assert reply(env, cid, "accept").status_code == 200
    [order] = get(env, "/orders?status=pending").json()["items"]
    return cid, qid, order["id"]


def movements(conn_, env, kind=None):
    """Return the movements of the first fixture product, oldest first, optionally of one kind."""
    return rows(
        conn_,
        "select * from luma.stock_movements where company_id=%s and product_id=%s and (%s::text is null or kind=%s) order by created_at,id",
        env["company"],
        env["products"][DL1],
        kind,
        kind,
    )


def level(conn_, env, index):
    """Return (on_hand, reserved, reorder_level) of a fixture product."""
    row = rows(
        conn_,
        "select on_hand,reserved,reorder_level from luma.stock_levels where company_id=%s and product_id=%s",
        env["company"],
        env["products"][index],
    )[0]
    return row["on_hand"], row["reserved"], row["reorder_level"]


def po_body(env, lines=((DL1, 10, "5.50"), (DL2, 4, "6.00")), **extra):
    """Build a valid purchase-order command."""
    return {
        "supplier": "Synthetic Supplier Ltd",
        "lines": [{"product_id": str(env["products"][i]), "quantity": q, "unit_cost": c} for i, q, c in lines],
        **extra,
    }


def receive_body(env, lines):
    """Build a receive command from (product index, quantity) pairs."""
    return {"lines": [{"product_id": str(env["products"][i]), "quantity": q} for i, q in lines]}


# ---------------------------------------------------------------- customer orders


def test_confirm_moves_stock_once_and_replays(environment, conn):
    """Confirm turns the hold into a stock movement once; the same key replays, a new key is a 409."""
    env = environment
    cid, qid, oid = pending_order(env, conn)
    assert stock(conn, env) == (100, 3)
    key = uuid4()
    first = post(env, f"/orders/{oid}/confirm", {}, key)
    assert first.status_code == 200, first.text
    body = first.json()
    assert (body["status"], body["number"]) == ("confirmed", "SO-0001")
    assert [(line["sku"], line["quantity"], line["unit_price"]) for line in body["lines"]] == [("DL-001", 3, "32.35")]
    assert body["confirmed_at"] is not None
    assert stock(conn, env) == (97, 0)
    [move] = movements(conn, env, "order")
    assert (move["delta"], str(move["reference_id"]), move["actor"]) == (-3, oid, env["user"])
    assert_invariants(conn, env)
    assert get_detail(env, cid)["conversation"]["status"] == "ordered"
    assert rows(conn, "select status from luma.stock_reservations where quote_id=%s", qid) == [{"status": "converted"}]
    notices = [
        row["payload"]["text"]
        for row in rows(conn, "select payload from luma.outbox where conversation_id=%s and kind='reply'", cid)
    ]
    assert CONFIRMED.format(number="SO-0001") in notices
    assert len(rows(conn, "select 1 from luma.audit where company_id=%s and action='order.confirmed'", env["company"])) == 1
    replay = post(env, f"/orders/{oid}/confirm", {}, key)
    assert replay.status_code == 200 and replay.json() == body
    assert stock(conn, env) == (97, 0) and len(movements(conn, env, "order")) == 1
    again = post(env, f"/orders/{oid}/confirm", {})
    assert again.status_code == 409 and "already confirmed" in again.json()["detail"]
    assert stock(conn, env) == (97, 0)


def test_confirm_is_refused_when_the_hold_is_gone(environment, conn):
    """If the reservation was released by another path, confirming is a 409 and stock is untouched."""
    env = environment
    cid, qid, oid = pending_order(env, conn)
    ledger.release_quote(conn, env["company"], qid, "test_release")
    conn.commit()
    response = post(env, f"/orders/{oid}/confirm", {})
    assert response.status_code == 409 and "no longer reserved" in response.json()["detail"]
    assert get(env, "/orders").json()["items"][0]["status"] == "pending"
    assert stock(conn, env) == (100, 0)


def test_cancel_pending_releases_the_hold(environment, conn):
    """Cancelling a pending order releases the reservation, keeps on-hand, and marks the conversation for staff."""
    env = environment
    cid, qid, oid = pending_order(env, conn)
    assert post(env, f"/orders/{oid}/cancel", {"reason": "ab"}).status_code == 422
    response = post(env, f"/orders/{oid}/cancel", {"reason": "  Customer phoned to withdraw  "})
    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["status"], body["cancel_reason"]) == ("cancelled", "Customer phoned to withdraw")
    assert stock(conn, env) == (100, 0)
    assert rows(conn, "select status,release_reason from luma.stock_reservations where quote_id=%s", qid) == [
        {"status": "released", "release_reason": "order_cancelled"}
    ]
    assert movements(conn, env, "order_cancel") == []
    assert get_detail(env, cid)["conversation"]["status"] == "needs_staff"
    assert rows(conn, "select status from luma.quotes where id=%s", qid) == [{"status": "superseded"}]
    assert_invariants(conn, env)
    revised = make_draft(env, cid, 2)  # staff can quote again after the cancel
    assert revised["revision"] == 2
    again = post(env, f"/orders/{oid}/cancel", {"reason": "Second attempt"})
    assert again.status_code == 409 and "already cancelled" in again.json()["detail"]
    assert post(env, f"/orders/{oid}/confirm", {}).status_code == 409


def test_cancel_confirmed_returns_the_stock(environment, conn):
    """Cancelling a confirmed order appends an order_cancel movement per line and restores on-hand."""
    env = environment
    cid, qid, oid = pending_order(env, conn)
    assert post(env, f"/orders/{oid}/confirm", {}).status_code == 200
    assert stock(conn, env) == (97, 0)
    response = post(env, f"/orders/{oid}/cancel", {"reason": "Customer changed the project"})
    assert response.status_code == 200 and response.json()["status"] == "cancelled"
    assert stock(conn, env) == (100, 0)
    [back] = movements(conn, env, "order_cancel")
    assert (back["delta"], str(back["reference_id"])) == (3, oid)
    assert_invariants(conn, env)
    assert [row["action"] for row in rows(conn, "select action from luma.audit where company_id=%s and action like 'order.%%' order by id", env["company"])][-2:] == [
        "order.confirmed",
        "order.cancelled",
    ]


def test_order_list_filters_by_status_and_orders_newest_first(environment, conn):
    """GET /api/orders lists lines, filters by status and rejects an unknown status."""
    env = environment
    _, _, oid = pending_order(env, conn)
    assert [o["id"] for o in get(env, "/orders").json()["items"]] == [oid]
    assert get(env, "/orders?status=confirmed").json()["items"] == []
    assert get(env, "/orders?status=bogus").status_code == 422
    assert post(env, f"/orders/{oid}/confirm", {}).status_code == 200
    [order] = get(env, "/orders?status=confirmed").json()["items"]
    assert order["customer_name"] == "Synthetic test customer" and order["lines"][0]["line_total"] == "97.05"


# ---------------------------------------------------------------- purchase orders


def test_purchase_order_partial_then_full_receipt(environment, conn):
    """Receipts raise stock per line, the status follows, and over-receiving is refused without writing."""
    env = environment
    created = post(env, "/purchase-orders", po_body(env, expected_on="2026-12-01", notes="Synthetic note"))
    assert created.status_code == 200, created.text
    po = created.json()
    assert (po["number"], po["status"], po["expected_on"], po["notes"]) == ("PO-0001", "ordered", "2026-12-01", "Synthetic note")
    assert sorted((line["sku"], line["quantity_ordered"], line["quantity_received"]) for line in po["lines"]) == [
        ("DL-001", 10, 0),
        ("DL-002", 4, 0),
    ]
    assert level(conn, env, DL1)[:2] == (100, 0)
    pid = po["id"]
    partial = post(env, f"/purchase-orders/{pid}/receive", receive_body(env, [(DL1, 6)]))
    assert partial.status_code == 200 and partial.json()["status"] == "partially_received"
    assert level(conn, env, DL1)[:2] == (106, 0)
    [receipt] = movements(conn, env, "receipt")
    assert (receipt["delta"], str(receipt["reference_id"])) == (6, pid)
    over = post(env, f"/purchase-orders/{pid}/receive", receive_body(env, [(DL1, 5), (DL2, 1)]))
    assert over.status_code == 409 and "more was received" in over.json()["detail"].lower()
    assert level(conn, env, DL1)[:2] == (106, 0) and level(conn, env, DL2)[:2] == (100, 0)
    rest = post(env, f"/purchase-orders/{pid}/receive", receive_body(env, [(DL1, 4)]))
    assert rest.json()["status"] == "partially_received"  # DL-002 is still outstanding
    last = post(env, f"/purchase-orders/{pid}/receive", receive_body(env, [(DL2, 4)]))
    assert last.status_code == 200 and last.json()["status"] == "received"
    assert level(conn, env, DL1)[:2] == (110, 0) and level(conn, env, DL2)[:2] == (104, 0)
    assert_invariants(conn, env)
    done = post(env, f"/purchase-orders/{pid}/receive", receive_body(env, [(DL1, 1)]))
    assert done.status_code == 409 and "already received" in done.json()["detail"]
    assert post(env, f"/purchase-orders/{pid}/cancel", None).status_code == 409
    second = post(env, "/purchase-orders", po_body(env, lines=[(DL1, 1, "1.00")]))
    assert second.json()["number"] == "PO-0002"
    listed = get(env, "/purchase-orders").json()["items"]
    assert [p["number"] for p in listed] == ["PO-0002", "PO-0001"]
    assert all(line["sku"] for p in listed for line in p["lines"])


def test_receive_idempotency_replay_does_not_double_count(environment, conn):
    """The same receive command and key replays the stored response without a second movement."""
    env = environment
    pid = post(env, "/purchase-orders", po_body(env, lines=[(DL1, 10, "5.00")])).json()["id"]
    key = uuid4()
    first = post(env, f"/purchase-orders/{pid}/receive", receive_body(env, [(DL1, 5)]), key)
    again = post(env, f"/purchase-orders/{pid}/receive", receive_body(env, [(DL1, 5)]), key)
    assert first.status_code == again.status_code == 200 and first.json() == again.json()
    assert level(conn, env, DL1)[:2] == (105, 0) and len(movements(conn, env, "receipt")) == 1
    changed = post(env, f"/purchase-orders/{pid}/receive", receive_body(env, [(DL1, 4)]), key)
    assert changed.status_code == 409


def test_purchase_order_cancel_rules(environment, conn):
    """An untouched order cancels; a cancelled one cannot be received; one with receipts cannot be cancelled."""
    env = environment
    first = post(env, "/purchase-orders", po_body(env)).json()["id"]
    cancelled = post(env, f"/purchase-orders/{first}/cancel", None)
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
    assert post(env, f"/purchase-orders/{first}/cancel", None).status_code == 409
    refused = post(env, f"/purchase-orders/{first}/receive", receive_body(env, [(DL1, 1)]))
    assert refused.status_code == 409 and "already cancelled" in refused.json()["detail"]
    second = post(env, "/purchase-orders", po_body(env)).json()["id"]
    assert post(env, f"/purchase-orders/{second}/receive", receive_body(env, [(DL1, 1)])).status_code == 200
    late = post(env, f"/purchase-orders/{second}/cancel", None)
    assert late.status_code == 409 and "received goods" in late.json()["detail"]
    assert level(conn, env, DL1)[:2] == (101, 0)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b, env: b.update(supplier=""),
        lambda b, env: b.update(supplier="x" * 121),
        lambda b, env: b.update(notes="n" * 501),
        lambda b, env: b.update(lines=[]),
        lambda b, env: b.update(lines=b["lines"] * 2),  # same product twice
        lambda b, env: b["lines"][0].update(quantity=0),
        lambda b, env: b["lines"][0].update(quantity=100001),
        lambda b, env: b["lines"][0].update(quantity=1.5),
        lambda b, env: b["lines"][0].update(unit_cost="-1"),
        lambda b, env: b["lines"][0].update(unit_cost="1000000.01"),
        lambda b, env: b["lines"][0].update(unit_cost="1.234"),
        lambda b, env: b.update(surprise=1),
        lambda b, env: b["lines"][0].update(product_id="not-a-uuid"),
    ],
)
def test_purchase_order_input_is_validated(environment, mutate):
    """Out-of-bounds, duplicate, fractional, unknown-field and malformed purchase-order input is a 422."""
    env = environment
    body = po_body(env, lines=[(DL1, 5, "2.00")])
    mutate(body, env)
    assert post(env, "/purchase-orders", body).status_code == 422


def test_purchase_order_needs_real_products_and_receive_lines_on_the_order(environment):
    """A foreign product id cannot be ordered, and a product that is not on the order cannot be received."""
    env = environment
    body = po_body(env, lines=[(DL1, 5, "2.00")])
    body["lines"][0]["product_id"] = str(uuid4())
    assert post(env, "/purchase-orders", body).status_code == 422
    pid = post(env, "/purchase-orders", po_body(env, lines=[(DL1, 5, "2.00")])).json()["id"]
    elsewhere = post(env, f"/purchase-orders/{pid}/receive", receive_body(env, [(DL2, 1)]))
    assert elsewhere.status_code == 422
    assert post(env, f"/purchase-orders/{pid}/receive", receive_body(env, [(DL1, 1), (DL1, 1)])).status_code == 422


# ---------------------------------------------------------------- adjustments and reorder levels


def test_adjustment_changes_on_hand_with_a_reason_and_replays(environment, conn):
    """An adjustment appends one movement with the reason; the same key replays; bad input is a 422."""
    env = environment
    pid = str(env["products"][DL1])
    key = uuid4()
    body = {"product_id": pid, "delta": 5, "reason": "  Cycle count found extras  "}
    first = post(env, "/inventory/adjustments", body, key)
    assert first.status_code == 200, first.text
    assert first.json() == {"product_id": pid, "on_hand": 105, "reserved": 0, "available": 105, "reorder_level": 20}
    assert post(env, "/inventory/adjustments", body, key).json() == first.json()
    [move] = movements(conn, env, "adjustment")
    assert (move["delta"], move["reason"], move["actor"]) == (5, "Cycle count found extras", env["user"])
    assert level(conn, env, DL1)[:2] == (105, 0)
    assert post(env, "/inventory/adjustments", {**body, "delta": 0}).status_code == 422
    assert post(env, "/inventory/adjustments", {**body, "reason": "ab"}).status_code == 422
    assert post(env, "/inventory/adjustments", {**body, "delta": 100001}).status_code == 422
    assert post(env, "/inventory/adjustments", {**body, "delta": 1.5}).status_code == 422
    assert post(env, "/inventory/adjustments", {**body, "extra": 1}).status_code == 422
    assert post(env, "/inventory/adjustments", {**body, "product_id": str(uuid4())}).status_code == 404
    assert_invariants(conn, env)


def test_adjustment_below_reserved_or_zero_is_refused(environment, conn):
    """On-hand cannot fall below the quantity reserved for quotations, nor below zero."""
    env = environment
    approved(env, 3)  # reserves 3 of DL-001
    pid = str(env["products"][DL1])
    refused = post(env, "/inventory/adjustments", {"product_id": pid, "delta": -98, "reason": "Damaged goods"})
    assert refused.status_code == 409 and "reserved" in refused.json()["detail"]
    assert stock(conn, env) == (100, 3)
    below_zero = post(env, "/inventory/adjustments", {"product_id": pid, "delta": -101, "reason": "Damaged goods"})
    assert below_zero.status_code == 409
    allowed = post(env, "/inventory/adjustments", {"product_id": pid, "delta": -97, "reason": "Damaged goods"})
    assert allowed.status_code == 200 and allowed.json()["available"] == 0
    assert movements(conn, env, "adjustment")[0]["delta"] == -97
    assert_invariants(conn, env)


def test_reorder_level_drives_the_low_flag_and_alerts(environment, conn):
    """Setting a reorder level changes the low flag and the live low-stock list; range is enforced."""
    env = environment
    pid = str(env["products"][DL1])
    stock_view = get(env, "/inventory/stock").json()
    row = next(item for item in stock_view["items"] if item["sku"] == "DL-001")
    assert (row["available"], row["reorder_level"], row["low"]) == (100, 20, False)
    low_skus = lambda: [item["sku"] for item in get(env, "/inventory/alerts").json()["low_stock"]]  # noqa: E731
    assert low_skus() == ["DL-011"]  # zero stock is always at or below 20
    changed = post(env, "/inventory/reorder-levels", {"product_id": pid, "reorder_level": 100})
    assert changed.status_code == 200 and changed.json()["reorder_level"] == 100
    assert low_skus() == ["DL-011", "DL-001"]
    view = get(env, "/inventory/alerts").json()
    assert view["counts"] == {"shortage": 0, "acceptance_refused": 0, "low_stock": 2, "total": 2}
    assert get(env, "/inventory/stock").json()["low_count"] == 2
    assert level(conn, env, DL1) == (100, 0, 100) and movements(conn, env, "adjustment") == []
    assert post(env, "/inventory/reorder-levels", {"product_id": pid, "reorder_level": 100001}).status_code == 422
    assert post(env, "/inventory/reorder-levels", {"product_id": pid, "reorder_level": -1}).status_code == 422
    assert post(env, "/inventory/reorder-levels", {"product_id": str(uuid4()), "reorder_level": 5}).status_code == 404
    assert post(env, "/inventory/reorder-levels", {"product_id": pid, "reorder_level": 0}).status_code == 200
    assert low_skus() == ["DL-011"]


def test_stock_and_movement_reads(environment, conn):
    """The stock table shows every product; movements page newest first with a cursor and a product filter."""
    env = environment
    pid = str(env["products"][DL1])
    for delta in (1, 2, 3):
        assert post(env, "/inventory/adjustments", {"product_id": pid, "delta": delta, "reason": f"Count {delta}"}).status_code == 200
    items = get(env, "/inventory/stock").json()["items"]
    assert {item["sku"] for item in items} == {"DL-001", "DL-002", "DL-011"}
    first = get(env, f"/inventory/movements?product_id={pid}&limit=2").json()
    assert [m["delta"] for m in first["items"]] == [3, 2] and first["next"]
    assert first["items"][0]["sku"] == "DL-001" and first["items"][0]["kind"] == "adjustment"
    second = get(env, f"/inventory/movements?product_id={pid}&limit=2&before={first['next']}").json()
    assert [m["delta"] for m in second["items"]] == [1, 100] and second["next"] is None
    assert get(env, "/inventory/movements?limit=0").status_code == 422
    assert get(env, "/inventory/movements?before=garbage").status_code == 422


# ---------------------------------------------------------------- alerts


def test_prepare_writes_a_shortage_alert_once_and_the_customer_is_not_told(environment, conn):
    """A known SKU asked beyond available raises one open shortage alert; unknown and discontinued SKUs raise none."""
    env = environment
    cid = create_request(env)
    job = running_job(env, cid)

    def state(sku, quantity):
        """Build the preparation state for one extracted line, observing the conversation's current version."""
        version = get_detail(env, cid)["conversation"]["version"]
        return {
            "company_id": str(env["company"]),
            "conversation_id": cid,
            "job_id": str(job["id"]),
            "fence": job["fence"],
            "observed_version": version,
            "extraction": {"lines": [{"sku": sku, "quantity": quantity}]},
        }

    assert prepare(state("DL-999", 1)) == {"quote_id": None}  # unknown SKU: staff review, no alert
    conn.execute("update luma.products set discontinued=true where id=%s", (env["products"][DL2],))
    conn.commit()
    assert prepare(state("DL-002", 1)) == {"quote_id": None}  # discontinued: no alert
    assert rows(conn, "select 1 from luma.stock_alerts where company_id=%s", env["company"]) == []
    assert prepare(state("DL-001", 150)) == {"quote_id": None}
    assert prepare(state("DL-001", 160)) == {"quote_id": None}  # same conversation and product: still one alert
    [alert] = rows(conn, "select * from luma.stock_alerts where company_id=%s", env["company"])
    assert (alert["kind"], alert["status"], alert["requested"], alert["available"]) == ("shortage", "open", 150, 100)
    assert (str(alert["product_id"]), str(alert["conversation_id"])) == (str(env["products"][DL1]), cid)
    detail = get_detail(env, cid)
    assert detail["conversation"]["status"] == "needs_staff"
    assert not any(row["kind"] == "reply" for row in detail["delivery"])  # the customer is not told
    listed = get(env, "/inventory/alerts").json()
    [shown] = listed["alerts"]
    assert (shown["kind"], shown["sku"], shown["name"], shown["conversation_id"]) == ("shortage", "DL-001", "Synthetic downlight", cid)
    assert listed["counts"]["shortage"] == 1
    # After staff acknowledge, a repeated shortage on the same line raises a fresh alert.
    assert post(env, f"/inventory/alerts/{shown['id']}/acknowledge", {}).status_code == 200
    assert prepare(state("DL-001", 170)) == {"quote_id": None}
    assert len(rows(conn, "select 1 from luma.stock_alerts where company_id=%s and status='open'", env["company"])) == 1


def test_acknowledge_alerts(environment, conn):
    """Acknowledging moves an open alert once (replay safe), a second acknowledgement is a 409, unknown is a 404."""
    env = environment
    conn.execute("insert into luma.stock_alerts(company_id,kind) values(%s,'acceptance_refused')", (env["company"],))
    conn.commit()
    [alert] = get(env, "/inventory/alerts").json()["alerts"]
    assert alert["kind"] == "acceptance_refused" and alert["sku"] is None and alert["status"] == "open"
    key = uuid4()
    ok = post(env, f"/inventory/alerts/{alert['id']}/acknowledge", {}, key)
    assert ok.status_code == 200 and ok.json() == {"id": alert["id"], "status": "acknowledged"}
    assert post(env, f"/inventory/alerts/{alert['id']}/acknowledge", {}, key).json() == ok.json()
    twice = post(env, f"/inventory/alerts/{alert['id']}/acknowledge", {})
    assert twice.status_code == 409
    assert post(env, f"/inventory/alerts/{uuid4()}/acknowledge", {}).status_code == 404
    assert get(env, "/inventory/alerts").json()["alerts"] == []
    [row] = rows(conn, "select * from luma.stock_alerts where id=%s", alert["id"])
    assert str(row["acknowledged_by"]) == env["user"] and row["acknowledged_at"] is not None


# ---------------------------------------------------------------- roles and isolation


ADMIN_ONLY = [
    ("/inventory/adjustments", lambda env: {"product_id": str(env["products"][DL1]), "delta": 1, "reason": "Recount"}),
    ("/inventory/reorder-levels", lambda env: {"product_id": str(env["products"][DL1]), "reorder_level": 5}),
    ("/purchase-orders", lambda env: po_body(env)),
    (f"/purchase-orders/{uuid4()}/receive", lambda env: receive_body(env, [(DL1, 1)])),
    (f"/purchase-orders/{uuid4()}/cancel", lambda env: None),
]


@pytest.mark.parametrize(("path", "body"), ADMIN_ONLY)
def test_salesperson_gets_403_on_every_admin_route(environment, conn, path, body):
    """A salesperson is refused (403, plain message) on adjustments, reorder levels and every purchase-order write."""
    env = environment
    as_salesperson(conn, env)
    response = post(env, path, body(env))
    assert response.status_code == 403, response.text
    assert response.json()["detail"].startswith("Only an administrator can ")
    assert rows(conn, "select 1 from luma.stock_movements where company_id=%s and kind in ('adjustment','receipt')", env["company"]) == []
    assert rows(conn, "select 1 from luma.purchase_orders where company_id=%s", env["company"]) == []
    assert level(conn, env, DL1) == (100, 0, 20)


def test_salesperson_can_confirm_cancel_acknowledge_and_read(environment, conn):
    """A salesperson confirms and cancels orders, acknowledges alerts and reads stock, orders and purchase orders."""
    env = environment
    _, _, oid = pending_order(env, conn)
    conn.execute(
        "insert into luma.stock_alerts(company_id,kind) values(%s,'acceptance_refused')", (env["company"],)
    )
    conn.commit()
    as_salesperson(conn, env)
    assert post(env, f"/orders/{oid}/confirm", {}).status_code == 200
    assert post(env, f"/orders/{oid}/cancel", {"reason": "Salesperson cancel"}).status_code == 200
    [alert] = get(env, "/inventory/alerts").json()["alerts"]
    assert post(env, f"/inventory/alerts/{alert['id']}/acknowledge", {}).status_code == 200
    for path in ("/inventory/stock", "/inventory/movements", "/orders", "/purchase-orders"):
        assert get(env, path).status_code == 200, path
    assert stock(conn, env) == (100, 0)


def test_other_companys_rows_are_not_found(environment, conn):
    """Another company's order, purchase order and alert ids answer 404 and are never changed."""
    env = environment
    other, snapshot, conversation, quote = uuid4(), uuid4(), uuid4(), uuid4()
    order, purchase, alert = uuid4(), uuid4(), uuid4()
    conn.execute("insert into luma.companies(id,name) values(%s,'Other synthetic company')", (other,))
    conn.execute(
        "insert into luma.snapshots(id,company_id,source,observed_at,digest) values(%s,%s,'synthetic',%s,'fixture')",
        (snapshot, other, datetime.now(UTC)),
    )
    conn.execute(
        """insert into luma.conversations(id,company_id,customer_name,recipient,channel)
        values(%s,%s,'Other customer','other-recipient','local_test')""",
        (conversation, other),
    )
    conn.execute(
        """insert into luma.quotes(id,company_id,conversation_id,number,revision,status,recipient,snapshot_id,
        content,content_hash,valid_until) values(%s,%s,%s,'LQ-OTHER',1,'accepted','other-recipient',%s,%s,'hash',%s)""",
        (quote, other, conversation, snapshot, Jsonb({"lines": []}), datetime.now(UTC) + timedelta(days=1)),
    )
    conn.execute(
        """insert into luma.orders(id,company_id,number,conversation_id,quote_id,revision,accepted_via,currency,total,customer_name)
        values(%s,%s,'SO-0001',%s,%s,1,'reply','USD',10,'Other customer')""",
        (order, other, conversation, quote),
    )
    conn.execute(
        "insert into luma.purchase_orders(id,company_id,number,supplier,created_by) values(%s,%s,'PO-0001','Other supplier',%s)",
        (purchase, other, env["user"]),
    )
    conn.execute("insert into luma.stock_alerts(id,company_id,kind) values(%s,%s,'shortage')", (alert, other))
    conn.commit()
    try:
        assert post(env, f"/orders/{order}/confirm", {}).status_code == 404
        assert post(env, f"/orders/{order}/cancel", {"reason": "Not mine to cancel"}).status_code == 404
        assert post(env, f"/purchase-orders/{purchase}/receive", receive_body(env, [(DL1, 1)])).status_code == 404
        assert post(env, f"/purchase-orders/{purchase}/cancel", None).status_code == 404
        assert post(env, f"/inventory/alerts/{alert}/acknowledge", {}).status_code == 404
        assert get(env, "/orders").json()["items"] == [] and get(env, "/purchase-orders").json()["items"] == []
        assert get(env, "/inventory/alerts").json()["alerts"] == []
        assert rows(conn, "select status from luma.orders where id=%s", order) == [{"status": "pending"}]
        assert rows(conn, "select status from luma.stock_alerts where id=%s", alert) == [{"status": "open"}]
    finally:
        conn.execute("delete from luma.stock_alerts where company_id=%s", (other,))
        conn.execute("delete from luma.orders where company_id=%s", (other,))
        conn.execute("delete from luma.purchase_orders where company_id=%s", (other,))
        conn.execute("delete from luma.quotes where company_id=%s", (other,))
        conn.execute("delete from luma.conversations where company_id=%s", (other,))
        conn.execute("delete from luma.snapshots where company_id=%s", (other,))
        conn.execute("delete from luma.companies where id=%s", (other,))
        conn.commit()


def test_new_routes_are_in_the_openapi_contract(environment):
    """The OpenAPI document lists every T4 route with a response model."""
    spec = environment["api"].get("/openapi.json").json()
    expected = {
        ("get", "/api/inventory/stock"),
        ("get", "/api/inventory/movements"),
        ("post", "/api/inventory/adjustments"),
        ("post", "/api/inventory/reorder-levels"),
        ("get", "/api/inventory/alerts"),
        ("post", "/api/inventory/alerts/{alert_id}/acknowledge"),
        ("get", "/api/orders"),
        ("post", "/api/orders/{order_id}/confirm"),
        ("post", "/api/orders/{order_id}/cancel"),
        ("get", "/api/purchase-orders"),
        ("post", "/api/purchase-orders"),
        ("post", "/api/purchase-orders/{order_id}/receive"),
        ("post", "/api/purchase-orders/{order_id}/cancel"),
    }
    for method, path in expected:
        schema = spec["paths"][path][method]["responses"]["200"]["content"]["application/json"]["schema"]
        assert "$ref" in schema, (method, path)
