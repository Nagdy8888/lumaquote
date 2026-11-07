"""Per-user, per-conversation and queue admission limits against the real API, Auth and PostgreSQL.

Each limit is a fixed one-minute window, so every test starts early in a minute and uses its own
user (the fixture creates one) so windows never bleed between tests. Local, synthetic data only.
"""

import time
from uuid import uuid4

import psycopg
import pytest
from luma.core.admission import enqueue, rate_limit
from luma.core.database import database
from luma.core.errors import DomainError
from psycopg.rows import dict_row
from test_manual_workflow import create_request, make_draft, post
from test_staff_replies import queue_reply, take_over
from test_voice_intake import upload, wav_bytes


def early_in_minute(seconds: int = 20) -> None:
    """Wait until the current minute window has enough time left that a burst cannot straddle two windows."""
    while time.time() % 60 > seconds:
        time.sleep(1)


def first_denial(statuses: list[int]) -> int | None:
    """Return the index of the first 429 in a run of response statuses, or None."""
    return statuses.index(429) if 429 in statuses else None


def test_window_keeps_denied_attempts_and_isolates_keys(environment):
    """A denial is committed (the counter keeps rising) and one key's window never affects another's."""
    early_in_minute()
    key, other = f"test:{uuid4()}", f"test:{uuid4()}"
    for _ in range(2):
        with psycopg.connect(environment["dsn"], row_factory=dict_row) as conn:
            rate_limit(conn, key, 2)
            conn.commit()
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as conn:
        with pytest.raises(DomainError) as denied:
            rate_limit(conn, key, 2)
        assert denied.value.status == 429
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as conn:
        counts = {
            row["key"]: row["count"]
            for row in conn.execute(
                "select key,count from luma.rate_windows where key in (%s,%s)", (key, other)
            ).fetchall()
        }
        assert counts == {key: 3}
        rate_limit(conn, other, 2)
        conn.commit()


def test_read_limit_is_120_per_minute(environment):
    """The 121st workspace read in a minute is a 429; the first 120 are served."""
    early_in_minute(10)
    env = environment
    statuses = [env["api"].get("/api/workspace", headers=env["headers"]).status_code for _ in range(121)]
    assert statuses[:120] == [200] * 120 and statuses[120] == 429


def test_catalog_search_limit_is_30_per_minute(environment):
    """Paid-capable catalog search is capped at 30 per user per minute."""
    early_in_minute()
    env = environment
    statuses = [
        env["api"]
        .post("/api/catalog/search", headers=env["headers"], json={"query": "downlight"})
        .status_code
        for _ in range(31)
    ]
    assert statuses[:30] == [200] * 30 and statuses[30] == 429


def test_staff_reply_limit_is_10_per_minute(environment):
    """Human replies to a customer are capped at 10 per user per minute, stricter than the 30 mutation cap."""
    early_in_minute()
    env = environment
    cid = create_request(env)
    take_over(env, cid)
    statuses = [queue_reply(env, cid)[0].status_code for _ in range(11)]
    assert statuses[:10] == [200] * 10 and statuses[10] == 429


def test_approval_limit_is_10_per_minute(environment):
    """Staff decisions on quotation revisions are capped at 10 per user per minute."""
    early_in_minute()
    env = environment
    cid = create_request(env)
    statuses = []
    for revision in range(1, 12):
        make_draft(env, cid, quantity=revision)
        statuses.append(
            post(
                env, f"/conversations/{cid}/decision", {"expected_revision": revision, "decision": "reject"}
            ).status_code
        )
    assert statuses[:10] == [200] * 10 and statuses[10] == 429


def test_voice_upload_limit_is_6_per_minute(environment):
    """Voice uploads are capped at 6 per user per minute before bytes are accepted."""
    early_in_minute()
    env = environment
    cid = create_request(env)
    statuses = [upload(env, cid, wav_bytes()).status_code for _ in range(7)]
    assert statuses[:6] == [200] * 6 and statuses[6] == 429


def test_customer_messages_are_limited_per_conversation(environment):
    """One conversation accepts at most 6 customer messages and media per minute, whoever sends them."""
    early_in_minute()
    env = environment
    cid = create_request(env)
    statuses = []
    for number in range(8):
        statuses.append(
            post(
                env, f"/conversations/{cid}/customer-reply", {"text": f"Also 1 DL-00{1 + number % 2}"}
            ).status_code
        )
    assert first_denial(statuses) is not None and first_denial(statuses) <= 6, statuses
    assert all(code == 200 for code in statuses[: first_denial(statuses)])


def test_queue_capacity_refuses_work_at_100_with_a_recoverable_503(environment):
    """At 100 queued or running jobs the next enqueue is a 503 and nothing is inserted."""
    env = environment
    cid = create_request(env)
    inserted = []
    try:
        with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
            present = conn.execute(
                "select count(*) n from luma.jobs where status in ('queued','running')"
            ).fetchone()["n"]
            for _ in range(max(0, 100 - present)):
                inserted.append(
                    conn.execute(
                        "insert into luma.jobs(id,company_id,conversation_id,kind,payload) "
                        "values(%s,%s,%s,'agent','{}') returning id",
                        (uuid4(), env["company"], cid),
                    ).fetchone()["id"]
                )
            conn.commit()
        with database(worker=True) as conn:
            with pytest.raises(DomainError) as full:
                enqueue(conn, env["company"], cid)
            assert full.value.status == 503 and "queue is full" in full.value.message
    finally:
        with psycopg.connect(env["dsn"]) as conn:
            conn.execute("delete from luma.jobs where id = any(%s)", (inserted,))


@pytest.mark.xfail(
    strict=True,
    reason="Open gap: admission counters live in the request transaction, so a request that fails after "
    "rate_limit (409/404/422 from the business step) rolls the increment back and is never limited.",
)
def test_failed_requests_also_consume_admission(environment):
    """Flooding stale-revision decisions (all 409) should still hit the 10/minute approval limit."""
    early_in_minute()
    env = environment
    cid = create_request(env)
    make_draft(env, cid)
    statuses = [
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 99, "decision": "approve"}
        ).status_code
        for _ in range(12)
    ]
    assert 429 in statuses
