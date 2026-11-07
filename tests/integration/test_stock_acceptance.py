"""Customer acceptance and decline of a sent quotation on real PostgreSQL (D49, task T3).

Typed answers run through the real staff-operated local-test reply route (which calls
`accept_customer_text`); Telegram buttons and Gmail replies run through the real inbox worker with
the same mock transports as `test_telegram.py` and `test_email.py`. Label: local / local-substitute
(no real Telegram or Gmail). Rows are read back with an owner connection in isolated tenants.
"""

import base64
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.conversations.participation import accept_customer_text
from luma.features.conversations.repository import conversation
from luma.features.messaging import outbound
from luma.features.messaging.telegram_ingress import poll_once, reduce_update
from luma.features.orders import service
from luma_agent.runtime.delivery import deliver_one
from psycopg.rows import dict_row
from test_email import CUSTOMER, conversation_for, process, script  # noqa: F401  (fixture)
from test_email import mail as gmail
from test_manual_workflow import create_request, get_detail, make_draft, post
from test_stock_ledger import assert_invariants
from test_stock_reservations import approve, approved, reservations, stock
from test_telegram import USER, Bot, bot, start, telegram_conversation, update  # noqa: F401  (fixture)
from test_whatsapp import drain

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import retention  # noqa: E402

ACCEPTED = (
    "Thank you. Your acceptance of quotation {number}, revision {revision}, is recorded. "
    "Our sales team will confirm your order."
)


@pytest.fixture
def conn(environment):
    """Owner connection (bypasses row security) used to arrange and inspect; callers commit explicitly."""
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as connection:
        yield connection


def reply(env, cid, text):
    """Send a typed customer reply through the local-test route."""
    return post(env, f"/conversations/{cid}/customer-reply", {"text": text})


def sent(env, conn_):
    """Create, approve and locally deliver a quotation; return (conversation id, quote id)."""
    cid, qid = approved(env, 3)
    assert deliver_one(env["company"]) is True
    while deliver_one(env["company"]):  # earlier notices in the same tenant may be queued ahead of this quotation
        pass
    return cid, qid


def one(conn_, sql, *args):
    """Run a query on a fresh snapshot and return all rows."""
    conn_.commit()
    return conn_.execute(sql, args).fetchall()


def quote_status(conn_, qid):
    """Return a quotation's status."""
    return one(conn_, "select status from luma.quotes where id=%s", qid)[0]["status"]


def notices(conn_, cid):
    """Return the texts of fixed reply notices queued for a conversation, oldest first."""
    return [
        row["payload"]["text"]
        for row in one(
            conn_, "select payload from luma.outbox where conversation_id=%s and kind='reply' order by created_at", cid
        )
    ]


def jobs(conn_, cid):
    """Return the number of agent jobs of a conversation."""
    return one(conn_, "select count(*) n from luma.jobs where conversation_id=%s", cid)[0]["n"]


def customer_messages(conn_, cid):
    """Return the stored customer message bodies of a conversation."""
    return [
        row["body"]
        for row in one(
            conn_, "select body from luma.messages where conversation_id=%s and actor='customer' order by created_at", cid
        )
    ]


def test_accept_creates_a_pending_order_and_keeps_the_hold(environment, conn):
    """'Accept' after delivery accepts the quote, copies its lines and prices, keeps the stock held and queues one notice."""
    env = environment
    cid, qid = sent(env, conn)
    before = jobs(conn, cid)
    assert reply(env, cid, "  i accept the quotation. ").status_code == 200
    assert quote_status(conn, qid) == "accepted"
    [order] = one(conn, "select * from luma.orders where quote_id=%s", qid)
    assert (order["number"], order["status"], order["accepted_via"], order["revision"]) == ("SO-0001", "pending", "reply", 1)
    quote = one(conn, "select content from luma.quotes where id=%s", qid)[0]["content"]
    assert (str(order["total"]), order["currency"]) == (quote["total"], quote["currency"])
    assert (order["customer_name"], order["customer_company"]) == ("Synthetic test customer", "Fixture company")
    [line] = one(conn, "select * from luma.order_lines where order_id=%s", order["id"])
    assert (line["sku"], line["quantity"], str(line["unit_price"]), str(line["line_total"])) == (
        "DL-001",
        3,
        "32.35",
        "97.05",
    )
    assert reservations(conn, qid) == [("held", None)]
    assert stock(conn, env) == (100, 3)
    assert_invariants(conn, env)
    assert get_detail(env, cid)["conversation"]["status"] == "order_pending"
    number = one(conn, "select number from luma.quotes where id=%s", qid)[0]["number"]
    assert notices(conn, cid) == [ACCEPTED.format(number=number, revision=1)]
    assert quote["total"] == str(order["total"])
    assert jobs(conn, cid) == before
    assert len(customer_messages(conn, cid)) == 2  # the original request and the answer
    [event] = one(conn, "select * from luma.audit where company_id=%s and action='order.accepted'", env["company"])
    assert event["resource_id"] == order["id"]
    assert one(conn, "select next_value from luma.document_counters where company_id=%s and kind='order'", env["company"])[
        0
    ]["next_value"] == 2


def test_decline_releases_the_hold_and_confirms(environment, conn):
    """'Decline' declines the quote, releases its stock, marks the conversation declined and queues one notice."""
    env = environment
    cid, qid = sent(env, conn)
    assert reply(env, cid, "DECLINE!").status_code == 200
    assert quote_status(conn, qid) == "declined"
    assert reservations(conn, qid) == [("released", "declined")]
    assert stock(conn, env) == (100, 0)
    assert one(conn, "select 1 from luma.orders where quote_id=%s", qid) == []
    assert get_detail(env, cid)["conversation"]["status"] == "declined"
    number = one(conn, "select number from luma.quotes where id=%s", qid)[0]["number"]
    assert notices(conn, cid) == [f"Thank you. Quotation {number} is declined. Send a new request any time."]
    assert one(conn, "select 1 from luma.audit where company_id=%s and action='quotation.declined'", env["company"])
    assert_invariants(conn, env)


REFUSED = "This quotation can no longer be accepted. Our sales team will contact you."


def refusal_setup(env, conn_, case):
    """Arrange one situation in which an accept must be refused; return (conversation id, quote id or None, reason)."""
    if case == "no_quotation":
        return create_request(env), None, "no_quotation"
    if case == "in_review":
        cid = create_request(env)
        return cid, make_draft(env, cid)["id"], "not_open"
    if case == "not_sent":
        cid, qid = approved(env, 3)  # approved, but the send was never delivered
        return cid, qid, "not_sent"
    if case == "blocked":
        cid, qid = sent(env, conn_)
        conn_.execute("update luma.outbox set status='blocked' where quote_id=%s", (qid,))
        conn_.commit()
        return cid, qid, "not_sent"
    if case == "expired":
        cid, qid = sent(env, conn_)
        conn_.execute("update luma.quotes set valid_until=now()-interval '1 minute' where id=%s", (qid,))
        conn_.commit()
        return cid, qid, "expired"
    if case == "older_revision":
        cid, qid = sent(env, conn_)
        make_draft(env, cid, 2)  # revision 2 supersedes revision 1 and is still in review
        return cid, qid, "not_open"
    if case == "hold_lost":
        cid, qid = sent(env, conn_)
        conn_.execute("update luma.stock_reservations set status='released',closed_at=now() where quote_id=%s", (qid,))
        conn_.execute("update luma.stock_levels set reserved=0 where company_id=%s", (env["company"],))
        conn_.commit()
        return cid, qid, "stock_not_held"
    raise AssertionError(case)


@pytest.mark.parametrize(
    "case", ["no_quotation", "in_review", "not_sent", "blocked", "expired", "older_revision", "hold_lost"]
)
def test_accept_is_refused_without_a_valid_sent_quotation(environment, conn, case):
    """No quotation, one in review, unsent, blocked, expired, superseded or without stock: alert, notice, needs_staff."""
    env = environment
    cid, qid, reason = refusal_setup(env, conn, case)
    statuses = {r["id"]: r["status"] for r in one(conn, "select id,status from luma.quotes where conversation_id=%s", cid)}
    before = jobs(conn, cid)
    assert reply(env, cid, "Accept").status_code == 200
    assert {r["id"]: r["status"] for r in one(conn, "select id,status from luma.quotes where conversation_id=%s", cid)} == statuses
    assert one(conn, "select 1 from luma.orders where conversation_id=%s", cid) == []
    [alert] = one(conn, "select * from luma.stock_alerts where conversation_id=%s", cid)
    assert (alert["kind"], alert["status"]) == ("acceptance_refused", "open")
    [event] = one(conn, "select detail from luma.audit where company_id=%s and action='order.acceptance_refused'", env["company"])
    assert event["detail"]["reason"] == reason
    assert notices(conn, cid) == [REFUSED]
    assert get_detail(env, cid)["conversation"]["status"] == "needs_staff"
    assert jobs(conn, cid) == before
    assert customer_messages(conn, cid)[-1] == "Accept"
    assert len(customer_messages(conn, cid)) == 2


def test_the_same_provider_message_has_one_effect(environment, conn):
    """A redelivered provider message id stores one message, creates one order and queues one notice."""
    env = environment
    cid, qid = sent(env, conn)
    for _ in range(2):
        with database(worker=True) as session:
            current = conversation(session, env["company"], cid, lock=True)
            accept_customer_text(session, env["company"], current, "Accept", provider_id="synthetic:dup-1")
    assert len(one(conn, "select 1 from luma.orders where quote_id=%s", qid)) == 1
    assert len(notices(conn, cid)) == 1
    assert customer_messages(conn, cid).count("Accept") == 1


def test_a_second_accept_changes_nothing_and_a_decline_after_accept_is_refused(environment, conn):
    """Accepting twice keeps one order; declining an accepted quotation is refused and its hold stays."""
    env = environment
    cid, qid = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    assert reply(env, cid, "I accept").status_code == 200
    [order] = one(conn, "select * from luma.orders where quote_id=%s", qid)
    assert quote_status(conn, qid) == "accepted" and get_detail(env, cid)["conversation"]["status"] == "order_pending"
    assert one(conn, "select 1 from luma.stock_alerts where conversation_id=%s", cid) == []
    assert one(conn, "select next_value from luma.document_counters where company_id=%s", env["company"])[0]["next_value"] == 2
    assert reply(env, cid, "Decline").status_code == 200
    assert quote_status(conn, qid) == "accepted"
    assert reservations(conn, qid) == [("held", None)]
    assert [a["kind"] for a in one(conn, "select kind from luma.stock_alerts where conversation_id=%s", cid)] == [
        "acceptance_refused"
    ]
    assert one(conn, "select id from luma.orders where quote_id=%s", qid)[0]["id"] == order["id"]


def test_order_numbers_count_up_per_company(environment, conn):
    """Two accepted quotations in one company are SO-0001 and SO-0002."""
    env = environment
    numbers = []
    for _ in range(2):
        cid, qid = sent(env, conn)
        assert reply(env, cid, "Accept").status_code == 200
        numbers.append(one(conn, "select number from luma.orders where quote_id=%s", qid)[0]["number"])
    assert numbers == ["SO-0001", "SO-0002"]


def test_staff_ownership_records_the_answer_but_queues_no_notice(environment, conn):
    """Under takeover a delivered quotation can still be accepted; staff see needs_staff and no notice is queued."""
    env = environment
    cid, qid = sent(env, conn)
    version = get_detail(env, cid)["conversation"]["version"]
    assert post(env, f"/conversations/{cid}/ownership", {"expected_version": version, "owner": "staff"}).status_code == 200
    assert reservations(conn, qid) == [("held", None)]  # a delivered send keeps its hold
    assert reply(env, cid, "Accept").status_code == 200
    assert quote_status(conn, qid) == "accepted"
    assert len(one(conn, "select 1 from luma.orders where quote_id=%s", qid)) == 1
    assert notices(conn, cid) == []
    assert get_detail(env, cid)["conversation"]["status"] == "needs_staff"
    assert customer_messages(conn, cid)[-1] == "Accept"


def test_ordinary_text_still_supersedes_and_plain_yes_is_not_acceptance(environment, conn):
    """Anything but an exact phrase keeps the old behavior: supersede, release the hold, wake the agent."""
    env = environment
    for text in ("Accept but change qty to 20", "yes"):
        cid, qid = sent(env, conn)
        before = jobs(conn, cid)
        assert reply(env, cid, text).status_code == 200
        assert quote_status(conn, qid) == "superseded"
        assert reservations(conn, qid) == [("released", "superseded")]
        assert one(conn, "select 1 from luma.orders where quote_id=%s", qid) == []
        assert jobs(conn, cid) == before + 1
        assert get_detail(env, cid)["conversation"]["status"] == "new"


def test_an_accepted_quotation_cannot_be_revised(environment, conn):
    """A new draft over an accepted revision is a 409, so the order's reservation cannot be superseded away."""
    env = environment
    cid, qid = sent(env, conn)
    assert reply(env, cid, "Accept").status_code == 200
    current = get_detail(env, cid)["conversation"]
    response = post(
        env,
        f"/conversations/{cid}/draft",
        {"expected_version": current["version"], "lines": [{"product_id": str(env["products"][0]), "quantity": 1}]},
    )
    assert response.status_code == 409
    assert quote_status(conn, qid) == "accepted"
    assert reservations(conn, qid) == [("held", None)]


def test_answers_share_the_conversation_rate_limit(environment, conn):
    """The seventh answer within a minute is a 429, exactly like typed requests."""
    env = environment
    cid, qid = sent(env, conn)
    codes = [reply(env, cid, "Accept").status_code for _ in range(7)]
    assert codes[:6] == [200] * 6 and codes[6] == 429


def test_refused_answer_never_raises_into_the_inbox(environment, conn):
    """answer_quote reports a refusal as a value, so the inbox row is `done` and the customer gets the notice."""
    env = environment
    cid = create_request(env)
    with database(worker=True) as session:
        current = conversation(session, env["company"], cid, lock=True)
        result = service.answer_quote(session, env["company"], current, "accept", "reply", provider_id="x:1")
    assert result == {"outcome": "refused", "reason": "no_quotation"}
    with pytest.raises(DomainError), database(worker=True) as session:
        conversation(session, env["company"], uuid4(), lock=True)


def test_caption_and_local_text_tell_the_customer_how_to_answer(environment, conn):
    """The delivered quotation text ends with the reply instruction."""
    env = environment
    cid, qid = sent(env, conn)
    last = one(conn, "select body from luma.messages where conversation_id=%s and actor='assistant'", cid)[-1]["body"]
    assert last.endswith("Reply ACCEPT to accept or DECLINE to decline.")
    assert outbound.ANSWER_HINT == "Reply ACCEPT to accept or DECLINE to decline."


def test_retention_keeps_a_conversation_that_has_an_order_and_deletes_refusal_alerts(environment, conn):
    """An old conversation with an order is skipped (a business record); one with only an alert is deleted."""
    env = environment
    kept, qid = sent(env, conn)
    assert reply(env, kept, "Accept").status_code == 200
    refused = create_request(env)
    assert reply(env, refused, "Accept").status_code == 200
    old = datetime.now(UTC) - timedelta(days=100)
    conn.execute("update luma.conversations set updated_at=%s where company_id=%s", (old, env["company"]))
    conn.execute("update luma.audit set created_at=%s where company_id=%s", (old, env["company"]))
    conn.execute("update luma.jobs set status='done' where company_id=%s", (env["company"],))
    conn.execute("update luma.outbox set status='local_delivered' where company_id=%s and status='queued'", (env["company"],))
    conn.commit()
    report = retention.run(UUID(str(env["company"])), datetime.now(UTC), execute=True)
    assert report["conversations"]["conversations"] == 1 and report["skipped_unfinished_conversations"] == 1
    assert len(one(conn, "select 1 from luma.orders where quote_id=%s", qid)) == 1
    assert one(conn, "select 1 from luma.conversations where id=%s", kept)
    assert one(conn, "select 1 from luma.conversations where id=%s", refused) == []
    assert one(conn, "select 1 from luma.stock_alerts where conversation_id=%s", refused) == []


# ---- Telegram buttons ------------------------------------------------------------------------


def callback(update_id, quote_id, *, action="acc", user=USER, chat_type="private", callback_id=None, **override):
    """Build one Telegram callback_query Update for a button press."""
    query = {
        "id": callback_id or f"cb{update_id}",
        "from": {"id": int(user), "is_bot": False, "first_name": "Synthetic", "last_name": "Customer"},
        "message": {"message_id": 50, "date": 1_700_000_000, "chat": {"id": int(user), "type": chat_type}},
        "chat_instance": "1",
        "data": f"{action}:{quote_id}",
    }
    query.update(override)
    return {"update_id": update_id, "callback_query": query}


def telegram_quote(env, bot_):
    """Approve and deliver a quotation to the Telegram test user; return (conversation id, quote id)."""
    cid = start(env, bot_)
    with psycopg.connect(env["dsn"]) as c:
        c.execute("update luma.snapshots set source='google_sheets',observed_at=now() where company_id=%s", (env["company"],))
    quote = make_draft(env, cid)
    assert approve(env, cid).status_code == 200
    with psycopg.connect(env["dsn"]) as c:
        c.execute("update luma.snapshots set observed_at=now() where company_id=%s", (env["company"],))
    assert deliver_one(env["company"]) is True
    return cid, quote["id"]


def test_callback_updates_reduce_only_when_well_formed():
    """Only a private human button press with acc:/dec: and a UUID reduces to a quote_answer event."""
    qid = str(uuid4())
    identity, kind, event = reduce_update(callback(1, qid, callback_id="777"))
    assert (identity, kind) == ("tgcb:777", "message")
    assert event == {
        "id": "tgcb:777",
        "from": USER,
        "name": "Synthetic Customer",
        "provider": "telegram",
        "channel": "telegram",
        "type": "quote_answer",
        "answer": "accept",
        "quote_id": qid,
        "callback_id": "777",
    }
    assert reduce_update(callback(2, qid, action="dec"))[2]["answer"] == "decline"
    bad_message = callback(3, qid)
    del bad_message["callback_query"]["message"]
    robot = callback(4, qid)
    robot["callback_query"]["from"]["is_bot"] = True
    other_chat = callback(5, qid)
    other_chat["callback_query"]["message"]["chat"]["id"] = 111
    for rejected in (
        callback(6, qid, chat_type="group"),
        callback(7, qid, action="del"),
        callback(8, "not-a-uuid"),
        callback(9, qid, callback_id="bad id!"),
        callback(10, qid, data=None),
        callback(11, qid, data="acc:" + qid.upper()),
        bad_message,
        robot,
        other_chat,
        {"update_id": 12, "callback_query": "x"},
    ):
        assert reduce_update(rejected) is None


def test_quotation_is_sent_with_inline_buttons_and_the_hint(environment, bot):  # noqa: F811
    """sendDocument carries a JSON reply_markup string with acc:/dec: callback data and the caption hint."""
    env = environment
    cid, qid = telegram_quote(env, bot)
    [upload] = bot.calls("sendDocument")
    body = upload.content.decode("latin-1")
    assert 'name="reply_markup"' in body
    markup = body.split('name="reply_markup"')[1].split("\r\n\r\n", 1)[1].split("\r\n--", 1)[0]
    assert json.loads(markup) == {
        "inline_keyboard": [
            [{"text": "Accept", "callback_data": f"acc:{qid}"}, {"text": "Decline", "callback_data": f"dec:{qid}"}]
        ]
    }
    assert all(len(f"{p}:{qid}".encode()) <= 64 for p in ("acc", "dec"))
    assert "Reply ACCEPT to accept or DECLINE to decline." in body


def test_accept_button_creates_the_order_and_answers_the_callback(environment, bot, conn):  # noqa: F811
    """A genuine Accept press is stored as '[Button] Accept', accepts the quote, queues the notice and answers once."""
    env = environment
    cid, qid = telegram_quote(env, bot)
    bot.updates = [callback(20, qid)]
    assert poll_once(None, timeout=0) == 21
    assert json.loads(bot.calls("getUpdates")[0].content)["allowed_updates"] == ["message", "callback_query"]
    drain()
    assert quote_status(conn, qid) == "accepted"
    [order] = one(conn, "select * from luma.orders where quote_id=%s", qid)
    assert (order["accepted_via"], order["status"]) == ("telegram_button", "pending")
    assert reservations(conn, qid) == [("held", None)]
    [stored] = one(conn, "select * from luma.messages where provider_id='tgcb:cb20'")
    assert (stored["actor"], stored["body"]) == ("customer", "[Button] Accept")
    assert one(conn, "select status from luma.inbox where provider_id='tgcb:cb20'")[0]["status"] == "done"
    [answer] = bot.calls("answerCallbackQuery")
    assert json.loads(answer.content) == {"callback_query_id": "cb20", "text": "Recorded"}
    assert notices(conn, cid)[-1].startswith("Thank you. Your acceptance of quotation")
    # Telegram redelivers the same press: stored once, no second order.
    bot.updates = [callback(20, qid)]
    poll_once(None, timeout=0)
    drain()
    assert len(one(conn, "select 1 from luma.orders where quote_id=%s", qid)) == 1


def test_decline_button_releases_the_hold(environment, bot, conn):  # noqa: F811
    """A Decline press declines the quotation and frees its stock."""
    env = environment
    cid, qid = telegram_quote(env, bot)
    bot.updates = [callback(30, qid, action="dec")]
    poll_once(None, timeout=0)
    drain()
    assert quote_status(conn, qid) == "declined"
    assert reservations(conn, qid) == [("released", "declined")]
    assert one(conn, "select body from luma.messages where provider_id='tgcb:cb30'")[0]["body"] == "[Button] Decline"


def test_forged_or_old_button_for_another_chats_quote_is_refused(environment, bot, conn):  # noqa: F811
    """A button naming another conversation's quotation, or a random id, binds nothing and raises an alert."""
    env = environment
    cid, qid = telegram_quote(env, bot)
    other_cid, other_qid = sent(env, conn)  # a different (local test) conversation with its own live quotation
    for update_id, forged in ((40, other_qid), (41, str(uuid4()))):
        bot.updates = [callback(update_id, forged)]
        poll_once(None, timeout=0)
        drain()
    assert quote_status(conn, other_qid) == "approved" and quote_status(conn, qid) == "approved"
    assert one(conn, "select 1 from luma.orders where company_id=%s", env["company"]) == []
    assert reservations(conn, other_qid) == [("held", None)] and reservations(conn, qid) == [("held", None)]
    alerts = one(conn, "select conversation_id from luma.stock_alerts where company_id=%s", env["company"])
    assert {str(a["conversation_id"]) for a in alerts} == {cid} and len(alerts) == 2
    reasons = [r["detail"]["reason"] for r in one(conn, "select detail from luma.audit where action='order.acceptance_refused' and company_id=%s", env["company"])]
    assert reasons == ["not_current_quotation"] * 2
    assert REFUSED in notices(conn, cid)
    assert get_detail(env, other_cid)["conversation"]["status"] != "needs_staff"


def test_a_button_from_a_user_off_the_allowlist_is_ignored_but_still_answered(environment, bot, conn, monkeypatch):  # noqa: F811
    """A non-allowlisted presser opens nothing and changes nothing; the spinner is still stopped."""
    env = environment
    cid, qid = telegram_quote(env, bot)
    bot.updates = [callback(50, qid, user="555")]
    poll_once(None, timeout=0)
    drain()
    row = one(conn, "select status,error_code from luma.inbox where provider_id='tgcb:cb50'")[0]
    assert (row["status"], row["error_code"]) == ("ignored", "sender_not_allowed")
    assert quote_status(conn, qid) == "approved"
    assert json.loads(bot.calls("answerCallbackQuery")[0].content) == {"callback_query_id": "cb50", "text": ""}


def test_callback_answer_failure_is_best_effort_and_logs_only_a_code(environment, bot, conn, caplog):  # noqa: F811
    """A failing answerCallbackQuery never fails the inbox row, is not retried and leaks neither token nor id."""
    env = environment
    cid, qid = telegram_quote(env, bot)
    bot.fail_answer = True
    caplog.set_level("WARNING")
    bot.updates = [callback(60, qid)]
    poll_once(None, timeout=0)
    drain()
    assert one(conn, "select status from luma.inbox where provider_id='tgcb:cb60'")[0]["status"] == "done"
    assert quote_status(conn, qid) == "accepted"
    assert len(bot.calls("answerCallbackQuery")) == 1
    assert "Telegram callback answer failed: telegram_400" in caplog.text
    assert "cb60" not in caplog.text and "123456789" not in caplog.text


# ---- Gmail replies ---------------------------------------------------------------------------


def test_gmail_reply_with_quoted_history_accepts_the_quotation(environment, script, conn):  # noqa: F811
    """A reply 'Accept' above the quoted quotation mail, with a 'Re:' subject, accepts it; the subject plays no part."""
    env = environment
    first = gmail()
    script.push(first)
    process(env, first["message_id"])
    cid = str(conversation_for(env)["id"])
    fresh = "update luma.snapshots set source='google_sheets',observed_at=now() where company_id=%s"
    with psycopg.connect(env["dsn"]) as c:
        c.execute(fresh, (env["company"],))
    quote = make_draft(env, cid)
    env["files"].append(f"{env['company']}/quotes/{quote['id']}.pdf")
    assert approve(env, cid).status_code == 200
    with psycopg.connect(env["dsn"]) as c:
        c.execute(fresh, (env["company"],))
    while deliver_one(env["company"]):
        pass
    claimed = script.claim().json()["mail"]
    assert claimed["body"].endswith("Reply ACCEPT to accept or DECLINE to decline.")
    assert base64.b64decode(claimed["attachment"]["pdf_base64"])
    assert script.receipt(claimed).json() == {"status": "sent"}
    body = (
        "Accept\n\nOn Sat, Nov 8, 2026 at 9:00 AM Luma <me@example.org> wrote:\n"
        "> Quotation LQ, revision 1. Reply ACCEPT to accept or DECLINE to decline."
    )
    answer = gmail(body=body, subject=f"Re: Quotation {quote['number']}")
    script.push(answer)
    assert process(env, answer["message_id"])["status"] == "done"
    assert quote_status(conn, quote["id"]) == "accepted"
    [order] = one(conn, "select * from luma.orders where quote_id=%s", quote["id"])
    assert order["accepted_via"] == "reply"
    assert reservations(conn, quote["id"]) == [("held", None)]
    assert datetime.now(UTC) - timedelta(minutes=5) < order["accepted_at"]
