"""Stock reservation at approval and release on every exit, on real PostgreSQL (D49, task T2).

Approval is driven through the real HTTP route (or `decide` on independent connections for the
race); releases through the real participation, drafting, dispatch and worker code. Rows are read
back with an owner connection. Everything runs in isolated synthetic tenants (`environment`).
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg
import pytest
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.conversations.participation import change_ownership
from luma.features.inventory import ledger
from luma.features.messaging import email_dispatch, outbound
from luma.features.quotations import approval
from luma.features.quotations.approval import decide
from luma.features.quotations.schemas import Decision
from luma_agent import worker
from luma_agent.runtime.delivery import deliver_one
from psycopg.rows import dict_row
from test_manual_workflow import create_request, get_detail, make_draft, post
from test_stock_ledger import assert_invariants, make_quote

DL1 = 0  # fixture product index: 100 units of opening stock


@pytest.fixture
def conn(environment):
    """Owner connection (bypasses row security) used to arrange and inspect; callers commit explicitly."""
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as connection:
        yield connection


def approve(env, cid, revision=1):
    """Approve the displayed revision through the public route and return the response."""
    return post(env, f"/conversations/{cid}/decision", {"expected_revision": revision, "decision": "approve"})


def stock(conn, env):
    """Return (on_hand, reserved) of the first fixture product after ending any open snapshot."""
    conn.commit()
    row = conn.execute(
        "select on_hand,reserved from luma.stock_levels where company_id=%s and product_id=%s",
        (env["company"], env["products"][DL1]),
    ).fetchone()
    return row["on_hand"], row["reserved"]


def reservations(conn, quote_id):
    """Return (status, release_reason) pairs of a quotation's reservations."""
    conn.commit()
    return [
        (row["status"], row["release_reason"])
        for row in conn.execute(
            "select status,release_reason from luma.stock_reservations where quote_id=%s", (quote_id,)
        )
    ]


def approved(env, quantity=3):
    """Create, draft and approve a request; return (conversation id, quote id)."""
    cid = create_request(env)
    quote = make_draft(env, cid, quantity)
    assert approve(env, cid, quote["revision"]).status_code == 200
    return cid, quote["id"]


def outbox_of(conn, quote_id):
    """Return the quotation outbox row of a quote."""
    conn.commit()
    return conn.execute("select * from luma.outbox where quote_id=%s", (quote_id,)).fetchone()


def assert_nothing_written(conn, env, qid):
    """The quote is still in review with no approval, outbox row, Drive export or reservation."""
    conn.commit()
    assert conn.execute("select status from luma.quotes where id=%s", (qid,)).fetchone()["status"] == "review"
    for table in ("approvals", "outbox", "drive_exports", "stock_reservations"):
        count = conn.execute(f"select count(*) as n from luma.{table} where quote_id=%s", (qid,)).fetchone()
        assert count["n"] == 0, table
    assert stock(conn, env)[1] == 0


def test_approval_reserves_stock_and_dispatch_proves_the_hold(environment, conn):
    """Approving a revision holds its quantity, available falls, and local delivery still succeeds with its own hold."""
    env = environment
    cid, qid = approved(env, 3)
    assert stock(conn, env) == (100, 3)
    assert reservations(conn, qid) == [("held", None)]
    assert_invariants(conn, env)
    assert deliver_one(env["company"]) is True
    assert get_detail(env, cid)["delivery"][0]["status"] == "local_delivered"
    assert reservations(conn, qid) == [("held", None)]


def test_insufficient_stock_is_a_409_and_writes_nothing(environment, conn):
    """Stock that vanished after drafting refuses approval; no approval, outbox, export or hold is written."""
    env = environment
    cid = create_request(env)
    quote = make_draft(env, cid, 60)
    ledger.apply_movement(conn, env["company"], env["products"][DL1], -50, "adjustment", "test", reason="stock take")
    conn.commit()
    assert approve(env, cid).status_code == 409
    assert_nothing_written(conn, env, quote["id"])


def test_a_ledger_refusal_after_the_snapshot_check_rolls_the_whole_approval_back(environment, conn, monkeypatch):
    """When only the ledger refuses (a race the snapshot check cannot see), the 409 leaves no trace."""
    env = environment
    cid = create_request(env)
    quote = make_draft(env, cid, 60)
    ledger.apply_movement(conn, env["company"], env["products"][DL1], -50, "adjustment", "test", reason="stock take")
    conn.commit()
    monkeypatch.setattr(approval, "check_snapshot", lambda *args, **kwargs: None)
    response = approve(env, cid)
    assert response.status_code == 409
    assert "Stock changed" in response.text
    assert_nothing_written(conn, env, quote["id"])


def test_two_approvals_race_for_the_last_units_and_exactly_one_wins(environment, conn):
    """Two staff connections approve 60 + 60 units of a 100-unit product at once; one succeeds, one gets 409."""
    env = environment
    first, second = create_request(env), create_request(env)
    quotes = {cid: make_draft(env, cid, 60) for cid in (first, second)}
    barrier = threading.Barrier(2)

    def run(cid):
        """Approve one conversation on its own connection after both threads are ready."""
        try:
            with database(env["user"]) as session:
                barrier.wait(timeout=5)
                decide(
                    session,
                    {"company_id": env["company"], "role": "admin"},
                    env["user"],
                    cid,
                    Decision(expected_revision=1, decision="approve"),
                )
            return "approved"
        except DomainError as error:
            return error.status

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, [first, second]))
    assert sorted(results, key=str) == [409, "approved"]
    assert stock(conn, env) == (100, 60)
    assert_invariants(conn, env)
    loser = first if results[0] == 409 else second
    winner_quote = quotes[second if loser == first else first]["id"]
    assert reservations(conn, winner_quote) == [("held", None)]
    conn.commit()
    row = conn.execute("select status from luma.quotes where id=%s", (quotes[loser]["id"],)).fetchone()
    assert row["status"] == "review"
    for table in ("approvals", "outbox", "drive_exports", "stock_reservations"):
        count = conn.execute(f"select count(*) as n from luma.{table} where quote_id=%s", (quotes[loser]["id"],))
        assert count.fetchone()["n"] == 0, table


def test_customer_revision_and_new_draft_release_the_hold(environment, conn):
    """A customer message supersedes the approved offer and frees its stock; so does saving a new revision."""
    env = environment
    cid, qid = approved(env, 3)
    assert stock(conn, env) == (100, 3)
    response = post(env, f"/conversations/{cid}/customer-reply", {"text": "Please change the quantity to five."})
    assert response.status_code == 200, response.text
    assert stock(conn, env) == (100, 0)
    assert reservations(conn, qid) == [("released", "superseded")]
    # A fresh approval, then a new revision by staff: the old hold is released and not double counted.
    quote = make_draft(env, cid, 100)
    assert approve(env, cid, quote["revision"]).status_code == 200
    assert stock(conn, env) == (100, 100)
    newer = make_draft(env, cid, 100)
    assert newer["status"] == "review"
    assert stock(conn, env) == (100, 0)
    assert reservations(conn, quote["id"]) == [("released", "superseded")]
    assert_invariants(conn, env)


def test_staff_takeover_blocks_the_queued_send_and_releases_the_hold(environment, conn):
    """Takeover blocks a queued quotation and frees its stock with reason staff_takeover."""
    env = environment
    cid, qid = approved(env, 4)
    version = get_detail(env, cid)["conversation"]["version"]
    assert (
        post(env, f"/conversations/{cid}/ownership", {"expected_version": version, "owner": "staff"}).status_code == 200
    )
    assert outbox_of(conn, qid)["error_code"] == "staff_takeover"
    assert reservations(conn, qid) == [("released", "staff_takeover")]
    assert stock(conn, env) == (100, 0)


def test_takeover_function_leaves_a_submitted_send_holding_its_stock(environment, conn):
    """A quotation already submitted to the provider is not blocked by takeover and keeps its hold."""
    env = environment
    cid, qid = approved(env, 4)
    conn.execute("update luma.outbox set status='submitted' where quote_id=%s", (qid,))
    conn.commit()
    version = get_detail(env, cid)["conversation"]["version"]
    with database(env["user"]) as session:
        change_ownership(
            session,
            {"company_id": env["company"]},
            env["user"],
            cid,
            type("Body", (), {"expected_version": version, "owner": "staff"})(),
        )
    assert reservations(conn, qid) == [("held", None)]


def test_dispatch_revalidation_failure_blocks_and_releases(environment, conn):
    """A quotation that fails the final dispatch check (here, a live channel on a synthetic snapshot) frees its hold."""
    env = environment
    cid, qid = approved(env, 5)
    conn.execute("update luma.conversations set channel='whatsapp' where id=%s", (cid,))
    conn.commit()
    assert deliver_one(env["company"]) is True
    assert outbox_of(conn, qid)["error_code"] == "dispatch_revalidation"
    assert reservations(conn, qid) == [("released", "delivery_blocked")]
    assert stock(conn, env) == (100, 0)


def test_dispatch_refuses_an_approved_quote_whose_reservation_was_released(environment, conn):
    """Dispatch requires the quotation's own held reservation; without it the intent is blocked."""
    env = environment
    cid, qid = approved(env, 5)
    ledger.release_quote(conn, env["company"], qid, "test")
    conn.commit()
    assert deliver_one(env["company"]) is True
    row = outbox_of(conn, qid)
    assert (row["status"], row["error_code"]) == ("blocked", "dispatch_revalidation")
    assert not any(m["kind"] == "document" for m in get_detail(env, cid)["messages"])


def test_dispatch_refuses_a_hold_with_a_different_quantity(environment, conn):
    """A reservation that no longer matches the quoted quantity is treated as missing."""
    env = environment
    cid, qid = approved(env, 5)
    conn.execute("update luma.stock_reservations set quantity=4 where quote_id=%s", (qid,))
    conn.commit()
    assert deliver_one(env["company"]) is True
    assert outbox_of(conn, qid)["error_code"] == "dispatch_revalidation"


def submitting_quote(conn, env, units=10):
    """A reserved, approved quotation whose outbox row is `submitting`; return (quote, outbox item)."""
    quote = make_quote(conn, env, [(DL1, units)], outbox=["submitting"])
    ledger.reserve_quote(conn, env["company"], quote)
    conn.commit()
    return quote, outbox_of(conn, quote["id"])


def test_blocked_and_failed_delivery_release_but_unknown_does_not(environment, conn):
    """block() and a failed record() free the hold; an unknown outcome keeps it."""
    env = environment
    quote, item = submitting_quote(conn, env)
    assert stock(conn, env) == (100, 10)
    with database(worker=True) as session:
        outbound.record(session, {"item": item, "quote": quote, "text": "x"}, {"status": "unknown", "code": "net"})
    assert reservations(conn, quote["id"]) == [("held", None)]
    assert stock(conn, env) == (100, 10)
    with database(worker=True) as session:
        outbound.record(session, {"item": item, "quote": quote, "text": "x"}, {"status": "failed", "code": "rejected"})
    # The row was `submitting` -> `unknown` above, and a failed record may still follow an unknown one.
    assert reservations(conn, quote["id"]) == [("released", "delivery_failed")]
    assert stock(conn, env) == (100, 0)
    assert_invariants(conn, env)

    blocked, bitem = submitting_quote(conn, env, 7)
    assert stock(conn, env) == (100, 7)
    with database(worker=True) as session:
        outbound.block(session, bitem, "recipient_not_allowed")
    assert reservations(conn, blocked["id"]) == [("released", "delivery_blocked")]
    assert stock(conn, env) == (100, 0)
    assert_invariants(conn, env)


def test_email_uncollected_failure_releases_but_an_expired_lease_does_not(environment, conn):
    """A mail nobody collected in 24 hours frees the hold; a claimed mail with a lost receipt keeps it."""
    env = environment
    company = env["company"]
    waiting, witem = submitting_quote(conn, env, 10)
    claimed, citem = submitting_quote(conn, env, 20)
    for item, state in ((witem, "waiting"), (citem, "claimed")):
        conn.execute(
            """insert into luma.email_dispatch(outbox_id,company_id,recipient,subject,body,created_at,status,
            claim_token,lease_until) values(%s,%s,'a@example.test','s','b',now()-interval '25 hours',%s,%s,%s)""",
            (
                item["id"],
                company,
                state,
                uuid4() if state == "claimed" else None,
                datetime.now(UTC) - timedelta(minutes=1) if state == "claimed" else None,
            ),
        )
    conn.commit()
    with database(worker=True) as session:
        email_dispatch.sweep(session, company)
    assert reservations(conn, waiting["id"]) == [("released", "delivery_failed")]
    assert reservations(conn, claimed["id"]) == [("held", None)]
    assert outbox_of(conn, claimed["id"])["status"] == "unknown"
    assert stock(conn, env) == (100, 20)
    assert_invariants(conn, env)


def test_worker_reconcile_releases_an_expired_approved_quote(environment, conn):
    """The worker's reconcile step (its own role and grants) frees an expired approval and marks it expired."""
    env = environment
    cid, qid = approved(env, 6)
    conn.execute("update luma.quotes set valid_until=now()-interval '1 minute' where id=%s", (qid,))
    conn.commit()
    assert worker.reconcile_stock() >= 1
    assert reservations(conn, qid) == [("released", "expired")]
    assert conn.execute("select status from luma.quotes where id=%s", (qid,)).fetchone()["status"] == "expired"
    assert stock(conn, env) == (100, 0)
    assert_invariants(conn, env)


def test_tick_runs_reconcile_once_and_a_failure_never_stops_the_loop(environment, monkeypatch, caplog):
    """tick() calls reconcile_stock exactly once; an error inside it is logged by class only and swallowed."""
    calls = []
    monkeypatch.setattr(worker, "claim_job", lambda: None)
    monkeypatch.setattr(worker, "deliver_one", lambda: False)
    monkeypatch.setattr(worker, "process_inbox", lambda: False)
    monkeypatch.setattr(worker, "reconcile_stock", lambda: calls.append(1) or 0)
    assert worker.tick() is False
    assert calls == [1]

    monkeypatch.undo()

    def explode(connection):
        """Simulate a database failure inside reconcile with a message that must not be logged."""
        raise RuntimeError("secret-detail-must-not-appear")

    monkeypatch.setattr(ledger, "reconcile", explode)
    with caplog.at_level("WARNING", logger="luma.worker"):
        assert worker.reconcile_stock() == 0
    assert "RuntimeError" in caplog.text
    assert "secret-detail" not in caplog.text
