"""A customer who already has an accepted quotation can send a new request (D49, repeat requests).

Confirmed or cancelled order: the new request drafts the next revision through the real agent
runtime (paid AI off, the deterministic written grammar). Pending order: the request is parked
before any job or model call. A failing agent job always leaves a staff signal. Label: local
(no provider call; the paid-model seam is the scripted fixture from `test_agent_brain.py`, which
fails the test if the model is called). Rows are read back with an owner connection.
"""

from uuid import uuid4

import psycopg
import pytest
from luma.core.admission import enqueue
from luma.core.database import database
from luma.core.errors import DomainError
from luma_agent import worker
from luma_agent.brain import catalog_context
from luma_agent.runtime.conversations import process_conversation
from luma_agent.runtime.delivery import deliver_one
from luma_agent.runtime.escalation import escalate_unanswered
from luma_agent.runtime.jobs import finish_job
from psycopg.rows import dict_row
from test_agent_brain import brain  # noqa: F401  (fixture)
from test_manual_workflow import get_detail, post
from test_stock_acceptance import customer_messages, notices, one, quote_status, reply, sent
from test_stock_ledger import assert_invariants
from test_stock_reservations import approve, reservations

WAITING = (
    "Your order {number} is waiting for confirmation by our sales team. "
    "We will reply to your new request after that."
)


@pytest.fixture
def conn(environment):
    """Owner connection (bypasses row security) used to arrange and inspect; callers commit explicitly."""
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as connection:
        yield connection


def status(env, cid):
    """Return the conversation status shown to staff."""
    return get_detail(env, cid)["conversation"]["status"]


def run_job(env, cid):
    """Lease this conversation's oldest queued job and process it in-process; return the job row."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as c:
        job = c.execute(
            """update luma.jobs set status='running',fence=fence+1,attempts=attempts+1,
            lease_until=now()+interval '120 seconds'
            where id=(select id from luma.jobs where company_id=%s and conversation_id=%s
            and status='queued' order by created_at limit 1) returning *""",
            (env["company"], cid),
        ).fetchone()
    assert job
    process_conversation(job)
    finish_job(job, "done")
    return job


def queued(conn_, cid):
    """Return how many agent jobs of the conversation still wait to run."""
    return one(conn_, "select count(*) n from luma.jobs where conversation_id=%s and status='queued'", cid)[0]["n"]


def settle_old_jobs(conn_, cid):
    """Mark the jobs created before the quotation as done so only the new request's job remains."""
    conn_.execute("update luma.jobs set status='done' where conversation_id=%s", (cid,))
    conn_.commit()


def confirm(env, cid):
    """Staff confirm the conversation's pending order through the public route."""
    [order] = [o for o in get_orders(env, "pending") if o["conversation_id"] == cid]
    response = post(env, f"/orders/{order['id']}/confirm", {})
    assert response.status_code == 200, response.text
    return order["id"]


def get_orders(env, state):
    """List orders of one status through the public route."""
    response = env["api"].get(f"/api/orders?status={state}", headers=env["headers"])
    assert response.status_code == 200, response.text
    return response.json()["items"]


def deliver_all(env):
    """Locally deliver everything queued for the tenant."""
    while deliver_one(env["company"]):
        pass


def test_confirmed_order_then_new_request_drafts_the_next_revision_and_a_second_order(environment, conn):
    """After staff confirm SO-0001 the customer asks again: revision 2 is drafted, approved, accepted as SO-0002."""
    env = environment
    cid, first = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    confirm(env, cid)
    settle_old_jobs(conn, cid)
    assert status(env, cid) == "ordered"
    assert reply(env, cid, "I need 2 DL-002").status_code == 200
    assert queued(conn, cid) == 1 and status(env, cid) == "new"
    assert quote_status(conn, first) == "accepted"  # history is kept; nothing was superseded
    run_job(env, cid)
    revisions = one(conn, "select id,revision,status from luma.quotes where conversation_id=%s order by revision", cid)
    assert [(r["revision"], r["status"]) for r in revisions] == [(1, "accepted"), (2, "review")]
    assert one(conn, "select status from luma.orders where quote_id=%s", first)[0]["status"] == "confirmed"
    assert one(conn, "select status from luma.stock_reservations where quote_id=%s", first)[0]["status"] == "converted"
    assert approve(env, cid, 2).status_code == 200
    deliver_all(env)
    assert reply(env, cid, "Accept").status_code == 200
    second = revisions[1]["id"]
    assert quote_status(conn, second) == "accepted" and quote_status(conn, first) == "accepted"
    orders = one(conn, "select number,status,quote_id,revision from luma.orders where conversation_id=%s order by number", cid)
    assert [(o["number"], o["status"], o["revision"]) for o in orders] == [("SO-0001", "confirmed", 1), ("SO-0002", "pending", 2)]
    assert reservations(conn, second) == [("held", None)]
    assert status(env, cid) == "order_pending"
    assert_invariants(conn, env)


def test_pending_order_parks_a_new_request_without_a_job_or_a_model_call(environment, conn, brain):  # noqa: F811
    """A new request while SO-0001 awaits staff: needs_staff, system message, one fixed notice, no job, no model call."""
    env = environment
    cid, first = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    settle_old_jobs(conn, cid)
    before = notices(conn, cid)
    for text in ("I need 2 DL-002", "Please also send 5 DL-001"):
        assert reply(env, cid, text).status_code == 200
    assert queued(conn, cid) == 0 and brain.calls == []
    assert status(env, cid) == "needs_staff"
    assert notices(conn, cid) == before + [WAITING.format(number="SO-0001")]  # one notice for two requests
    assert quote_status(conn, first) == "accepted" and reservations(conn, first) == [("held", None)]
    assert len(one(conn, "select 1 from luma.quotes where conversation_id=%s", cid)) == 1
    assert customer_messages(conn, cid)[-2:] == ["I need 2 DL-002", "Please also send 5 DL-001"]
    system = [m["body"] for m in one(conn, "select body from luma.messages where conversation_id=%s and actor='system'", cid)]
    assert len(system) == 2 and all("SO-0001" in text for text in system)
    assert len(one(conn, "select 1 from luma.audit where company_id=%s and action='order.request_held'", env["company"])) == 2
    # The current quotation's accept and decline phrases keep their T3 behavior.
    assert reply(env, cid, "Accept").status_code == 200
    assert quote_status(conn, first) == "accepted" and len(one(conn, "select 1 from luma.orders where quote_id=%s", first)) == 1
    assert reply(env, cid, "Decline").status_code == 200
    assert quote_status(conn, first) == "accepted" and reservations(conn, first) == [("held", None)]
    assert [a["kind"] for a in one(conn, "select kind from luma.stock_alerts where conversation_id=%s", cid)] == [
        "acceptance_refused"
    ]
    assert_invariants(conn, env)


def test_a_voice_request_job_is_parked_before_the_graph(environment, conn, brain):  # noqa: F811
    """A job that reaches the agent while the order is pending (a transcribed voice note) is parked, not drafted."""
    env = environment
    cid, first = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    settle_old_jobs(conn, cid)
    with database(worker=True) as session:
        session.execute("update luma.conversations set last_customer_at=now(),status='new' where id=%s", (cid,))
        enqueue(session, env["company"], cid)
    run_job(env, cid)
    assert brain.calls == []
    assert status(env, cid) == "needs_staff"
    assert notices(conn, cid)[-1] == WAITING.format(number="SO-0001")
    assert len(one(conn, "select 1 from luma.quotes where conversation_id=%s", cid)) == 1


def test_confirming_keeps_needs_staff_for_a_parked_request_and_the_next_request_drafts(environment, conn):
    """Confirm does not hide a waiting request behind `ordered`; once confirmed a later request drafts revision 2."""
    env = environment
    cid, first = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    settle_old_jobs(conn, cid)
    assert reply(env, cid, "I need 2 DL-002").status_code == 200
    confirm(env, cid)
    assert status(env, cid) == "needs_staff"
    assert reply(env, cid, "I need 2 DL-002").status_code == 200
    assert queued(conn, cid) == 1
    run_job(env, cid)
    assert [r["revision"] for r in one(conn, "select revision from luma.quotes where conversation_id=%s order by revision", cid)] == [1, 2]
    assert quote_status(conn, first) == "accepted"


def test_cancelled_order_then_new_request_works(environment, conn):
    """After staff cancel the pending order the quotation is superseded and the new request drafts revision 2."""
    env = environment
    cid, first = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    [order] = get_orders(env, "pending")
    assert post(env, f"/orders/{order['id']}/cancel", {"reason": "Customer changed the plan"}).status_code == 200
    settle_old_jobs(conn, cid)
    assert quote_status(conn, first) == "superseded"
    assert reply(env, cid, "I need 2 DL-002").status_code == 200
    assert queued(conn, cid) == 1
    run_job(env, cid)
    assert [(r["revision"], r["status"]) for r in one(conn, "select revision,status from luma.quotes where conversation_id=%s order by revision", cid)] == [
        (1, "superseded"),
        (2, "review"),
    ]
    assert_invariants(conn, env)


def test_drafting_still_refuses_while_the_order_is_pending(environment, conn):
    """The domain rule behind the parking: a draft over a pending order's quotation is a 409 and changes nothing."""
    env = environment
    cid, first = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    version = get_detail(env, cid)["conversation"]["version"]
    line = {"product_id": str(env["products"][0]), "quantity": 1}
    assert post(env, f"/conversations/{cid}/draft", {"expected_version": version, "lines": [line]}).status_code == 409
    confirm(env, cid)
    version = get_detail(env, cid)["conversation"]["version"]
    again = post(env, f"/conversations/{cid}/draft", {"expected_version": version, "lines": [line]})
    assert again.status_code == 200 and again.json()["revision"] == 2
    assert quote_status(conn, first) == "accepted"


def make_job(env, conn_, cid):
    """Create and lease an agent job for the conversation's latest customer message; return the job row."""
    conn_.execute("update luma.jobs set status='done' where conversation_id=%s", (cid,))
    conn_.commit()
    with database(worker=True) as session:
        session.execute("update luma.conversations set status='new',last_customer_at=now() where id=%s", (cid,))
        enqueue(session, env["company"], cid)
    with psycopg.connect(env["dsn"], row_factory=dict_row) as c:
        return c.execute(
            """update luma.jobs set status='running',fence=fence+1,lease_until=now()+interval '120 seconds'
            where conversation_id=%s and status='queued' returning *""",
            (cid,),
        ).fetchone()


def test_a_failed_agent_job_marks_the_conversation_for_staff(environment, conn, monkeypatch):
    """tick: a DomainError in an agent job ends the job `blocked` and leaves needs_staff plus one system message."""
    env = environment
    cid = post(env, "/conversations", {"customer_name": "Synthetic", "text": "Please quote 3 DL-001."}).json()["id"]
    job = make_job(env, conn, cid)

    def fail(_job):
        raise DomainError("Synthetic refusal", 409)

    monkeypatch.setattr(worker, "claim_job", lambda: job)
    monkeypatch.setattr(worker, "process_conversation", fail)
    for name in ("deliver_one", "process_inbox"):
        monkeypatch.setattr(worker, name, lambda *a, **k: False)
    monkeypatch.setattr(worker, "reconcile_stock", lambda: 0)
    worker.tick()
    assert one(conn, "select status,error_code from luma.jobs where id=%s", job["id"]) == [{"status": "blocked", "error_code": "DomainError"}]
    assert status(env, cid) == "needs_staff"
    system = [m["body"] for m in one(conn, "select body from luma.messages where conversation_id=%s and actor='system'", cid)]
    assert system == ["Automation could not process the latest customer message (DomainError). Staff should review and reply."]
    assert one(conn, "select 1 from luma.audit where company_id=%s and action='job.escalated'", env["company"])
    assert escalate_unanswered(job, "DomainError") is False  # already needs_staff: no second message


@pytest.mark.parametrize("case", ["staff_owned", "reviewing", "newer_message"])
def test_escalation_leaves_handled_conversations_alone(environment, conn, case):
    """No signal is added when staff own the chat, a draft awaits review, or a newer message has its own job."""
    env = environment
    cid = post(env, "/conversations", {"customer_name": "Synthetic", "text": "Please quote 3 DL-001."}).json()["id"]
    job = make_job(env, conn, cid)
    if case == "staff_owned":
        conn.execute("update luma.conversations set owner='staff' where id=%s", (cid,))
    elif case == "reviewing":
        conn.execute("update luma.conversations set status='review' where id=%s", (cid,))
    else:
        conn.execute("update luma.conversations set last_customer_at=now()+interval '1 minute' where id=%s", (cid,))
    conn.commit()
    assert escalate_unanswered(job, "DomainError") is False
    assert one(conn, "select 1 from luma.messages where conversation_id=%s and actor='system'", cid) == []


def add_filler_products(conn_, env, count):
    """Insert `count` current products 'AA-001'... that sort before every fixture SKU, plus 'ZZ-999'."""
    for sku in [f"AA-{n:03d}" for n in range(1, count + 1)] + ["ZZ-999"]:
        pid = uuid4()
        conn_.execute(
            """insert into luma.products(id,company_id,sku,name,family,description,watts,lumens,cct,ip_rating,price,source_id,page,snapshot_id)
            values(%s,%s,%s,'Synthetic filler','Filler','Synthetic',10,1000,3000,'IP20',1,%s,1,%s)""",
            (pid, env["company"], sku, env["source"], env["snapshot"]),
        )
    conn_.commit()


def test_catalog_listing_includes_skus_named_in_the_chat(environment, conn):
    """A bare "YES" matches no catalog text, so a SKU beyond the first 30 appears only via the chat history."""
    env = environment
    add_filler_products(conn, env, 35)
    with database(worker=True) as session:
        bare = catalog_context(session, env["company"], "YES")
        named = catalog_context(session, env["company"], "YES", "Customer: I need 4 x zz-999\nAgent: ok")
        other = catalog_context(session, env["company"], "YES", "Customer: send ZZ-998 and XX-12")
    assert "ZZ-999" not in bare
    assert named.splitlines()[0].startswith("ZZ-999 |")
    assert named.count("ZZ-999") == 1 and len(named.splitlines()) == 31  # 30 first rows plus the named SKU
    assert "ZZ-999" not in other  # an unknown SKU adds nothing and never errors
    assert "$" not in named
