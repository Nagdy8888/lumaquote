"""Stock ledger invariants, reservation lifecycle and reconcile rules on real PostgreSQL (D49, task T1).

Everything runs in isolated synthetic tenants created by the `environment` fixture. Tests drive
`luma.features.inventory.ledger` directly with real transactions; no HTTP route or agent is involved
(approval wiring belongs to task T2).
"""

import threading
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg
import pytest
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.inventory import ledger, queries
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

DL1, DL2, DL11 = 0, 1, 2  # fixture product indexes: 100, 100 and 0 units opening stock


@pytest.fixture
def conn(environment):
    """Owner connection (bypasses row security) used to arrange and inspect; every test commits explicitly."""
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as connection:
        yield connection


def make_quote(conn, env, lines, status="approved", valid_for=timedelta(days=1), outbox=()):
    """Insert a conversation, a quotation with stored lines and optional quotation outbox rows; return the quote."""
    cid, qid = uuid4(), uuid4()
    conn.execute(
        """insert into luma.conversations(id,company_id,customer_name,recipient,channel)
        values(%s,%s,'Synthetic customer','synthetic-recipient','local_test')""",
        (cid, env["company"]),
    )
    content = {
        "lines": [{"product_id": str(env["products"][index]), "quantity": quantity} for index, quantity in lines]
    }
    quote = conn.execute(
        """insert into luma.quotes(id,company_id,conversation_id,number,revision,status,recipient,snapshot_id,
        content,content_hash,valid_until) values(%s,%s,%s,%s,1,%s,'synthetic-recipient',%s,%s,'hash',%s)
        returning *""",
        (
            qid,
            env["company"],
            cid,
            f"LQ-{str(qid)[:8]}",
            status,
            env["snapshot"],
            Jsonb(content),
            datetime.now(UTC) + valid_for,
        ),
    ).fetchone()
    for state in outbox:
        conn.execute(
            """insert into luma.outbox(id,company_id,conversation_id,quote_id,kind,payload,status,action_key)
            values(%s,%s,%s,%s,'quotation','{}',%s,%s)""",
            (uuid4(), env["company"], cid, qid, state, f"quotation:{qid}:{uuid4()}"),
        )
    conn.commit()
    return quote


def level(conn, env, index):
    """Return the (on_hand, reserved) pair of a fixture product."""
    row = conn.execute(
        "select on_hand,reserved from luma.stock_levels where company_id=%s and product_id=%s",
        (env["company"], env["products"][index]),
    ).fetchone()
    return row["on_hand"], row["reserved"]


def held(conn, quote):
    """Return the reservation statuses of a quotation keyed by product id."""
    return {
        row["product_id"]: row["status"]
        for row in conn.execute("select product_id,status from luma.stock_reservations where quote_id=%s", (quote["id"],))
    }


def assert_invariants(conn, env):
    """on_hand equals the sum of movements and reserved the sum of held reservations, within bounds."""
    bad = conn.execute(
        """select l.product_id from luma.stock_levels l where l.company_id=%s and (
        l.on_hand <> coalesce((select sum(delta) from luma.stock_movements m
            where m.company_id=l.company_id and m.product_id=l.product_id),0)
        or l.reserved <> coalesce((select sum(quantity) from luma.stock_reservations r
            where r.company_id=l.company_id and r.product_id=l.product_id and r.status='held'),0)
        or l.reserved > l.on_hand or l.reserved < 0)""",
        (env["company"],),
    ).fetchall()
    assert bad == []


def test_invariants_hold_through_a_mixed_sequence(environment, conn):
    """Reserve, receive, release, convert, adjust and cancel keep the ledger equal to its movements."""
    env = environment
    first = make_quote(conn, env, [(DL1, 30), (DL2, 10)])
    second = make_quote(conn, env, [(DL1, 20)])
    company, order = env["company"], uuid4()
    assert_invariants(conn, env)
    ledger.reserve_quote(conn, company, first)
    ledger.reserve_quote(conn, company, second)
    assert level(conn, env, DL1) == (100, 50) and level(conn, env, DL2) == (100, 10)
    assert_invariants(conn, env)
    ledger.apply_movement(conn, company, env["products"][DL1], 50, "receipt", "admin", uuid4())
    ledger.release_quote(conn, company, second["id"], "superseded")
    assert level(conn, env, DL1) == (150, 30)
    assert ledger.convert_quote(conn, company, first["id"], order, "staff") == 2
    assert level(conn, env, DL1) == (120, 0) and level(conn, env, DL2) == (90, 0)
    ledger.apply_movement(conn, company, env["products"][DL2], -5, "adjustment", "admin", reason="Damaged in store")
    ledger.apply_movement(conn, company, env["products"][DL2], 10, "order_cancel", "staff", order)
    assert level(conn, env, DL2) == (95, 0)
    assert_invariants(conn, env)
    conn.commit()
    kinds = conn.execute(
        "select kind,count(*) n from luma.stock_movements where company_id=%s group by kind", (company,)
    ).fetchall()
    assert {row["kind"]: row["n"] for row in kinds} == {
        "opening": 2,  # DL-011 has zero stock and so no opening movement
        "receipt": 1,
        "order": 2,
        "adjustment": 1,
        "order_cancel": 1,
    }
    assert held(conn, first) == {env["products"][DL1]: "converted", env["products"][DL2]: "converted"}
    assert held(conn, second) == {env["products"][DL1]: "released"}


def test_movements_cannot_go_negative_or_below_reserved(environment, conn):
    """apply_movement refuses a result under zero or under the reserved quantity, and malformed movements."""
    env = environment
    company, product = env["company"], env["products"][DL1]
    ledger.reserve_quote(conn, company, make_quote(conn, env, [(DL1, 60)]))
    with pytest.raises(DomainError) as refused:
        ledger.apply_movement(conn, company, product, -41, "adjustment", "admin", reason="Stock count")
    assert refused.value.status == 409
    ledger.apply_movement(conn, company, product, -40, "adjustment", "admin", reason="Stock count")
    assert level(conn, env, DL1) == (60, 60)
    with pytest.raises(DomainError) as negative:
        ledger.apply_movement(conn, company, env["products"][DL2], -101, "adjustment", "admin", reason="Stock count")
    assert negative.value.status == 409
    for call, status in [
        (dict(delta=0, kind="receipt"), 422),
        (dict(delta=5, kind="gift"), 422),
        (dict(delta=-1, kind="adjustment"), 422),  # reason missing
        (dict(delta=-1, kind="adjustment", reason="ab"), 422),  # reason too short
        (dict(delta=-1, kind="adjustment", reason="x" * 201), 422),
    ]:
        with pytest.raises(DomainError) as bad:
            ledger.apply_movement(conn, company, product, actor="admin", **call)
        assert bad.value.status == status
    with pytest.raises(DomainError) as unknown:
        ledger.apply_movement(conn, company, uuid4(), 5, "receipt", "admin")
    assert unknown.value.status == 404
    with pytest.raises(DomainError) as foreign:
        ledger.apply_movement(conn, uuid4(), product, 5, "receipt", "admin")
    assert foreign.value.status == 404
    assert level(conn, env, DL1) == (60, 60)
    assert_invariants(conn, env)


def test_reserve_is_all_or_nothing_and_idempotent(environment, conn):
    """One short line holds nothing; a repeat reserves nothing more; a closed reservation cannot be re-held."""
    env = environment
    company = env["company"]
    short = make_quote(conn, env, [(DL1, 10), (DL2, 101)])
    with pytest.raises(DomainError) as refused:
        ledger.reserve_quote(conn, company, short)
    assert refused.value.status == 409 and "Stock changed" in refused.value.message
    assert held(conn, short) == {} and level(conn, env, DL1) == (100, 0)
    with pytest.raises(DomainError):
        ledger.reserve_quote(conn, company, make_quote(conn, env, [(DL11, 1)]))  # out of stock
    ok = make_quote(conn, env, [(DL1, 40), (DL2, 5)])
    assert ledger.reserve_quote(conn, company, ok) == {env["products"][DL1]: 40, env["products"][DL2]: 5}
    ledger.reserve_quote(conn, company, ok)
    assert level(conn, env, DL1) == (100, 40) and level(conn, env, DL2) == (100, 5)
    # The hold itself counts against availability: 60 left, so 61 is refused and 60 is not.
    with pytest.raises(DomainError):
        ledger.reserve_quote(conn, company, make_quote(conn, env, [(DL1, 61)]))
    ledger.reserve_quote(conn, company, make_quote(conn, env, [(DL1, 60)]))
    assert level(conn, env, DL1) == (100, 100)
    ledger.release_quote(conn, company, ok["id"], "declined")
    with pytest.raises(DomainError) as closed:
        ledger.reserve_quote(conn, company, ok)
    assert closed.value.status == 409
    assert_invariants(conn, env)


def test_release_and_convert_are_idempotent(environment, conn):
    """A second release or convert changes nothing; convert after release moves no stock."""
    env = environment
    company = env["company"]
    quote = make_quote(conn, env, [(DL1, 25)])
    ledger.reserve_quote(conn, company, quote)
    assert ledger.release_quote(conn, company, quote["id"], "superseded") == 1
    assert ledger.release_quote(conn, company, quote["id"], "superseded") == 0
    assert ledger.convert_quote(conn, company, quote["id"], uuid4(), "staff") == 0
    assert level(conn, env, DL1) == (100, 0)
    reason = conn.execute("select release_reason,closed_at from luma.stock_reservations where quote_id=%s", (quote["id"],))
    row = reason.fetchone()
    assert row["release_reason"] == "superseded" and row["closed_at"] is not None
    other = make_quote(conn, env, [(DL1, 25)])
    ledger.reserve_quote(conn, company, other)
    order = uuid4()
    assert ledger.convert_quote(conn, company, other["id"], order, "staff") == 1
    assert ledger.convert_quote(conn, company, other["id"], order, "staff") == 0
    assert ledger.release_quote(conn, company, other["id"], "late") == 0
    assert level(conn, env, DL1) == (75, 0)
    moved = conn.execute(
        "select delta,reference_id,actor from luma.stock_movements where company_id=%s and kind='order'", (company,)
    ).fetchall()
    assert moved == [{"delta": -25, "reference_id": order, "actor": "staff"}]
    assert_invariants(conn, env)


def test_seed_opening_is_idempotent(environment, conn):
    """Seeding a product that already has a level changes nothing; a zero-stock product has a row and no movement."""
    env = environment
    assert ledger.seed_opening(conn, env["company"], env["products"][DL1], 999) is False
    assert level(conn, env, DL1) == (100, 0)
    assert level(conn, env, DL11) == (0, 0)
    count = conn.execute(
        "select count(*) n from luma.stock_movements where company_id=%s and product_id=%s",
        (env["company"], env["products"][DL11]),
    ).fetchone()["n"]
    assert count == 0
    assert_invariants(conn, env)


RECONCILE_CASES = [
    # (name, quote status, valid for, outbox states, expect released, expected quote status, expected reason)
    ("superseded", "superseded", timedelta(days=1), ["queued"], True, "superseded", "quote_superseded"),
    ("declined", "declined", timedelta(days=1), [], True, "declined", "quote_declined"),
    ("rejected", "rejected", timedelta(days=1), [], True, "rejected", "quote_rejected"),
    ("expired approved", "approved", timedelta(hours=-1), ["delivered"], True, "expired", "expired"),
    ("blocked delivery", "approved", timedelta(days=1), ["blocked"], True, "approved", "delivery_failed"),
    ("failed delivery", "approved", timedelta(days=1), ["failed"], True, "approved", "delivery_failed"),
    ("unknown delivery", "approved", timedelta(days=1), ["unknown"], False, "approved", None),
    ("failed then unknown", "approved", timedelta(days=1), ["failed", "unknown"], False, "approved", None),
    ("failed beside queued retry", "approved", timedelta(days=1), ["failed", "queued"], False, "approved", None),
    ("delivered", "approved", timedelta(days=1), ["delivered"], False, "approved", None),
    ("fresh approval, outbox queued", "approved", timedelta(days=1), ["queued"], False, "approved", None),
    ("approved, no outbox yet", "approved", timedelta(days=1), [], False, "approved", None),
    ("accepted, order pending", "accepted", timedelta(days=1), ["delivered"], False, "accepted", None),
    ("accepted, past validity", "accepted", timedelta(hours=-1), ["delivered"], False, "accepted", None),
]


@pytest.mark.parametrize("case", RECONCILE_CASES, ids=[case[0] for case in RECONCILE_CASES])
def test_reconcile_rules(environment, conn, case):
    """Each reconcile rule releases exactly what the plan says and spares unknown and accepted holds."""
    _, status, valid_for, outbox, released, final_status, reason = case
    env = environment
    company = env["company"]
    quote = make_quote(conn, env, [(DL1, 10)], status="approved", valid_for=timedelta(days=1), outbox=outbox)
    ledger.reserve_quote(conn, company, quote)
    if status == "accepted":
        conn.execute(
            """insert into luma.orders(id,company_id,number,conversation_id,quote_id,revision,accepted_via,currency,
            total,customer_name) values(%s,%s,'SO-0001',%s,%s,1,'reply','USD',10,'Synthetic customer')""",
            (uuid4(), company, quote["conversation_id"], quote["id"]),
        )
    conn.execute(
        "update luma.quotes set status=%s,valid_until=%s where id=%s",
        (status, datetime.now(UTC) + valid_for, quote["id"]),
    )
    conn.commit()
    result = ledger.reconcile(conn, company)
    conn.commit()
    assert held(conn, quote) == {env["products"][DL1]: "released" if released else "held"}
    assert level(conn, env, DL1) == (100, 0 if released else 10)
    assert result == {"released": int(released), "expired": int(final_status == "expired" and released)}
    assert conn.execute("select status from luma.quotes where id=%s", (quote["id"],)).fetchone()["status"] == final_status
    stored = conn.execute("select release_reason from luma.stock_reservations where quote_id=%s", (quote["id"],)).fetchone()
    assert stored["release_reason"] == reason
    if released:
        event = conn.execute(
            "select detail from luma.audit where company_id=%s and action='stock.released' and resource_id=%s",
            (company, quote["id"]),
        ).fetchone()
        assert event["detail"]["reason"] == reason
    assert_invariants(conn, env)
    # Running it again is a no-op.
    assert ledger.reconcile(conn, company) == {"released": 0, "expired": 0}


def test_reconcile_is_scoped_by_company_and_batches_levels(environment, conn):
    """A company filter spares other tenants; the global form releases invalid holds of every tenant."""
    env = environment
    company = env["company"]
    stale = make_quote(conn, env, [(DL1, 5), (DL2, 5)], status="superseded")
    live = make_quote(conn, env, [(DL1, 5)], outbox=["delivered"])
    ledger.reserve_quote(conn, company, stale)
    ledger.reserve_quote(conn, company, live)
    conn.commit()
    assert ledger.reconcile(conn, uuid4()) == {"released": 0, "expired": 0}
    conn.commit()
    assert set(held(conn, stale).values()) == {"held"}
    assert ledger.reconcile(conn)["released"] >= 1  # other tenants' invalid holds, if any, are released too
    conn.commit()
    assert set(held(conn, stale).values()) == {"released"} and set(held(conn, live).values()) == {"held"}
    assert level(conn, env, DL1) == (100, 5) and level(conn, env, DL2) == (100, 0)
    assert_invariants(conn, env)


def test_two_approvals_race_for_the_last_units(environment, conn):
    """Two transactions reserve 60 of 100 units at once: exactly one wins, the other gets a 409."""
    env = environment
    quotes = [make_quote(conn, env, [(DL1, 60)]) for _ in range(2)]
    start, outcomes = threading.Barrier(2), []

    def attempt(quote):
        """Reserve in its own worker-role transaction and record the result."""
        try:
            with database(worker=True) as worker:
                start.wait(timeout=10)
                ledger.reserve_quote(worker, env["company"], quote)
            outcomes.append("held")
        except DomainError as error:
            outcomes.append(error.status)

    threads = [threading.Thread(target=attempt, args=(quote,)) for quote in quotes]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert sorted(map(str, outcomes)) == ["409", "held"]
    assert level(conn, env, DL1) == (100, 60)
    assert_invariants(conn, env)


def test_roles_row_security_and_append_only_movements(environment, conn):
    """Staff see only their company; the API cannot rewrite history; the worker cannot add movements."""
    env = environment
    company = env["company"]
    with database(str(env["user"])) as staff:
        assert queries.stock_rows(staff, company)
        assert queries.stock_rows(staff, uuid4()) == []
    with database(str(uuid4())) as outsider:
        assert queries.stock_rows(outsider, company) == []
    with database(str(env["user"])) as staff:
        ledger.apply_movement(staff, company, env["products"][DL1], 5, "receipt", "admin")
    for statement in (
        "update luma.stock_movements set delta=delta+1",
        "delete from luma.stock_movements",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege), database(str(env["user"])) as staff:
            staff.execute(statement)
    with pytest.raises(psycopg.errors.InsufficientPrivilege), database(worker=True) as worker:
        ledger.apply_movement(worker, company, env["products"][DL1], 1, "receipt", "worker")
    with database(worker=True) as worker:
        quote = make_quote(conn, env, [(DL1, 3)])
        ledger.reserve_quote(worker, company, quote)
        assert ledger.release_quote(worker, company, quote["id"], "superseded") == 1
    assert level(conn, env, DL1) == (105, 0)
    assert_invariants(conn, env)


def test_queries_report_stock_movements_alerts_and_low_stock(environment, conn):
    """Stock rows show available = on hand - reserved; movements page by keyset; low stock is live."""
    env = environment
    company = env["company"]
    ledger.reserve_quote(conn, company, make_quote(conn, env, [(DL1, 30)]))
    for _ in range(5):
        ledger.apply_movement(conn, company, env["products"][DL2], 1, "receipt", "admin")
    conn.commit()
    rows = {row["sku"]: row for row in queries.stock_rows(conn, company)}
    assert (rows["DL-001"]["on_hand"], rows["DL-001"]["reserved"], rows["DL-001"]["available"]) == (100, 30, 70)
    assert rows["DL-011"]["available"] == 0 and rows["DL-011"]["low"] is True
    assert rows["DL-001"]["low"] is False and rows["DL-001"]["reorder_level"] == 20
    assert queries.low_stock_count(conn, company) == 1
    conn.execute(
        "update luma.stock_levels set reorder_level=70 where company_id=%s and product_id=%s",
        (company, env["products"][DL1]),
    )
    conn.commit()
    assert queries.low_stock_count(conn, company) == 2
    assert [row["sku"] for row in queries.low_stock_rows(conn, company)] == ["DL-011", "DL-001"]
    seen, cursor = [], None
    while True:
        page = queries.movements_page(conn, company, env["products"][DL2], limit=2, before=cursor)
        seen += [row["id"] for row in page["items"]]
        cursor = page["next"]
        if cursor is None:
            break
    assert len(seen) == len(set(seen)) == 6  # opening + five receipts, no repeats across pages
    assert queries.movements_page(conn, uuid4())["items"] == []
    conn.execute(
        "insert into luma.stock_alerts(company_id,kind,product_id,requested,available) values(%s,'shortage',%s,50,3)",
        (company, env["products"][DL1]),
    )
    conn.commit()
    alerts = queries.open_alerts(conn, company)
    assert [(a["kind"], a["sku"], a["requested"]) for a in alerts] == [("shortage", "DL-001", 50)]
