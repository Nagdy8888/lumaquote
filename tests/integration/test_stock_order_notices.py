"""Fixed order notices survive the customer's next message; everything else queued is still blocked (D49).

Runs through the real local-test routes, the real conversation lock and the real local-channel
dispatcher (`deliver_one`), in isolated synthetic tenants. A fixed order notice (acceptance,
decline, refusal, order waiting, order confirmed) is marked `payload.notice = 'order'`; a new
customer text or attachment must not block it (`customer_revision`), while a queued quotation
send, a clarification reply and an unmarked notice stay blocked, and staff takeover blocks the
notice. Label: local (no provider call).
"""

import psycopg
import pytest
from luma.core.database import database
from luma.features.conversations.service import queue_notice
from luma.features.orders.management import CONFIRMED_NOTICE
from luma.features.orders.service import ACCEPTED_NOTICE, DECLINED_NOTICE, WAITING_NOTICE
from luma_agent.runtime.delivery import deliver_one
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from test_manual_workflow import get_detail, post
from test_stock_acceptance import notices, one, reply, sent
from test_stock_reservations import approved
from test_voice_intake import upload, wav_bytes

REQUEST = "I need 2 DL-002"


@pytest.fixture
def conn(environment):
    """Owner connection (bypasses row security) used to arrange and inspect; callers commit explicitly."""
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as connection:
        yield connection


def outbox(conn_, cid):
    """Return (text, status, error_code) of every reply row of the conversation, oldest first."""
    return [
        (row["payload"]["text"], row["status"], row["error_code"])
        for row in one(
            conn_,
            "select payload,status,error_code from luma.outbox where conversation_id=%s and kind='reply' order by created_at",
            cid,
        )
    ]


def confirm(env, cid):
    """Staff confirm the conversation's pending order through the public route; return its number."""
    response = env["api"].get("/api/orders?status=pending", headers=env["headers"])
    [order] = [o for o in response.json()["items"] if o["conversation_id"] == cid]
    assert post(env, f"/orders/{order['id']}/confirm", {}).status_code == 200
    return order["number"]


def quote_row(conn_, qid):
    """Return the quotation's number and revision as the notices spell them."""
    return one(conn_, "select number,revision from luma.quotes where id=%s", qid)[0]


def drain(env):
    """Deliver everything queued for the tenant through the local channel."""
    while deliver_one(env["company"]):
        pass


def test_confirmed_and_acceptance_notices_survive_the_next_text_and_are_delivered(environment, conn):
    """Accept, staff confirm, then the customer writes again before dispatch: both notices stay queued and arrive once."""
    env = environment
    cid, qid = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    number = confirm(env, cid)
    accepted = ACCEPTED_NOTICE.format(**quote_row(conn, qid))
    confirmed = CONFIRMED_NOTICE.format(number=number)
    assert outbox(conn, cid)[-2:] == [(accepted, "queued", None), (confirmed, "queued", None)]
    assert reply(env, cid, REQUEST).status_code == 200
    assert outbox(conn, cid)[-2:] == [(accepted, "queued", None), (confirmed, "queued", None)]
    assert get_detail(env, cid)["conversation"]["status"] == "new"  # the new request still wakes the agent
    drain(env)
    assert [status for _, status, _ in outbox(conn, cid)][-2:] == ["local_delivered", "local_delivered"]
    texts = [m["body"] for m in one(conn, "select body from luma.messages where conversation_id=%s and actor='assistant'", cid)]
    assert texts.count(confirmed) == 1 and texts.count(accepted) == 1


def test_decline_notice_survives_the_next_text(environment, conn):
    """A queued decline notice is still delivered after the customer asks for something new."""
    env = environment
    cid, qid = sent(env, conn)
    assert reply(env, cid, "Decline").status_code == 200
    declined = DECLINED_NOTICE.format(**quote_row(conn, qid))
    assert outbox(conn, cid)[-1] == (declined, "queued", None)
    assert reply(env, cid, REQUEST).status_code == 200
    assert outbox(conn, cid)[-1] == (declined, "queued", None)
    drain(env)
    assert outbox(conn, cid)[-1] == (declined, "local_delivered", None)


def test_waiting_notice_survives_a_later_text(environment, conn):
    """The order-waiting notice (queued when a request was parked) survives the request that follows confirmation."""
    env = environment
    cid, _ = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    assert reply(env, cid, REQUEST).status_code == 200  # parked; queues the waiting notice
    number = confirm(env, cid)
    assert reply(env, cid, "Please also send 5 DL-001").status_code == 200  # an ordinary request again
    rows = outbox(conn, cid)
    assert (WAITING_NOTICE.format(number=number), "queued", None) in rows
    assert all(error != "customer_revision" for _, _, error in rows)


def test_an_attachment_keeps_the_order_notice_too(environment, conn):
    """A voice note after confirmation blocks nothing that states an order fact."""
    env = environment
    cid, _ = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    number = confirm(env, cid)
    assert upload(env, cid, wav_bytes()).status_code == 200
    assert outbox(conn, cid)[-1] == (CONFIRMED_NOTICE.format(number=number), "queued", None)


def test_quotation_clarification_and_unmarked_notices_are_still_blocked(environment, conn):
    """The revision block is unchanged for a queued quotation send, a clarification reply and an unmarked notice."""
    env = environment
    cid, qid = approved(env, 3)  # the quotation send is queued, not yet delivered
    conn.execute(
        """insert into luma.outbox(id,company_id,conversation_id,kind,payload,action_key)
        values(gen_random_uuid(),%s,%s,'reply',%s,%s)""",
        (env["company"], cid, Jsonb({"text": "Which colour temperature?"}), f"clarify:test-{cid}"),
    )
    conn.commit()
    with database(worker=True) as session:
        current = {"id": cid, "owner": "agent"}
        queue_notice(session, env["company"], current, "Welcome.", f"inbound-notice:test-{cid}")
        queue_notice(session, env["company"], current, "Order notice.", f"order-test:{cid}", order=True)
    assert reply(env, cid, "Make it 5 DL-001").status_code == 200
    rows = one(conn, "select payload,status,error_code,quote_id from luma.outbox where conversation_id=%s", cid)
    by_text = {r["payload"].get("text"): (r["status"], r["error_code"]) for r in rows}
    assert by_text["Which colour temperature?"] == ("blocked", "customer_revision")
    assert by_text["Welcome."] == ("blocked", "customer_revision")
    assert by_text["Order notice."] == ("queued", None)
    [send] = [r for r in rows if r["quote_id"]]
    assert (send["status"], send["error_code"]) == ("blocked", "customer_revision")
    assert one(conn, "select status from luma.quotes where id=%s", qid)[0]["status"] == "superseded"


def test_staff_takeover_still_blocks_the_order_notice(environment, conn):
    """Staff own the conversation after takeover: the queued notice is blocked (`staff_takeover`) and never sent."""
    env = environment
    cid, _ = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    number = confirm(env, cid)
    version = get_detail(env, cid)["conversation"]["version"]
    assert post(env, f"/conversations/{cid}/ownership", {"expected_version": version, "owner": "staff"}).status_code == 200
    assert outbox(conn, cid)[-1] == (CONFIRMED_NOTICE.format(number=number), "blocked", "staff_takeover")
    drain(env)
    assert outbox(conn, cid)[-1][1] == "blocked"


def test_an_order_notice_is_queued_once_per_action_key(environment, conn):
    """A repeated key or a repeated confirm adds no second order notice."""
    env = environment
    cid, _ = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    number = confirm(env, cid)
    order = one(conn, "select id from luma.orders where conversation_id=%s", cid)[0]
    with database(worker=True) as session:
        queue_notice(session, env["company"], {"id": cid, "owner": "agent"}, "Again", f"order-confirmed:{order['id']}", order=True)
    assert post(env, f"/orders/{order['id']}/confirm", {}).status_code == 409
    texts = notices(conn, cid)
    assert texts.count(CONFIRMED_NOTICE.format(number=number)) == 1 and "Again" not in texts
