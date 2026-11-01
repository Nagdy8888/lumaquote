"""Expired jobs retain uncertain cost and visible staff recovery without provider replay."""

from uuid import uuid4

import psycopg
import pytest
from luma.core.database import database
from luma.core.errors import DomainError
from luma_agent.budget import reserve
from luma_agent.lease import assert_job
from luma_agent.runtime.jobs import finish_job
from luma_agent.runtime.recovery import recover_expired
from psycopg.rows import dict_row
from test_manual_workflow import create_request, get_detail
from test_photo_intake import photo_job, upload_photo


@pytest.mark.parametrize("media", [False, True])
def test_expired_operation_is_fenced_visible_and_not_retried(environment, media):
    """Recovery is tenant-scoped/idempotent, preserves uncertain reservations, and rejects stale worker completion."""
    env = environment
    cid = create_request(env)
    if media:
        uploaded = upload_photo(env, cid)
        mid = uploaded.json()["message_id"]
        job = photo_job(env, cid)
    else:
        with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
            job = conn.execute(
                """update luma.jobs set status='running',fence=fence+1,
                lease_until=now()+interval '120 seconds' where company_id=%s returning *""",
                (env["company"],),
            ).fetchone()
    with database(worker=True) as conn:
        reserve(conn, env["company"], job["id"])
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute("update luma.jobs set lease_until=now()-interval '1 second' where id=%s", (job["id"],))
        if media:
            conn.execute("update luma.media set status='processing' where message_id=%s", (mid,))
    with database(worker=True) as conn:
        assert recover_expired(conn, uuid4()) == 0
        assert recover_expired(conn, env["company"]) == 1
        assert recover_expired(conn, env["company"]) == 0
    with database(worker=True) as conn:
        with pytest.raises(DomainError, match="lease no longer valid"):
            assert_job(conn, {"job_id": job["id"], "fence": job["fence"]})
    finish_job(job, "done")
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        current = conn.execute("select status,fence from luma.jobs where id=%s", (job["id"],)).fetchone()
        assert current["status"] == "failed" and current["fence"] == job["fence"] + 1
        assert (
            conn.execute("select status from luma.usage where job_id=%s", (job["id"],)).fetchone()["status"]
            == "unknown"
        )
        assert (
            conn.execute(
                "select count(*) n from luma.audit where resource_id=%s and action='job.interrupted'",
                (job["id"],),
            ).fetchone()["n"]
            == 1
        )
    detail = get_detail(env, cid)
    assert detail["quote"] is None and detail["delivery"] == []
    if media:
        attachment = next(message for message in detail["messages"] if message["id"] == mid)
        assert attachment["media_status"] == "unknown" and "interrupted" in attachment["body"]
    else:
        assert any(
            message["actor"] == "system" and "interrupted" in message["body"]
            for message in detail["messages"]
        )


def test_expiry_recovery_skips_another_transactions_locked_job(environment):
    """Two actual connections cannot recover a job while another transaction holds its shared job lock."""
    env = environment
    cid = create_request(env)
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        job = conn.execute(
            """update luma.jobs set status='running',fence=fence+1,
            lease_until=now()-interval '1 second' where company_id=%s returning *""",
            (env["company"],),
        ).fetchone()
    with database(worker=True) as owner:
        owner.execute("select id from luma.jobs where id=%s for share", (job["id"],))
        with database(worker=True) as recovery:
            recovery.execute("set local statement_timeout='2s'")
            assert recover_expired(recovery, env["company"]) == 0
    with database(worker=True) as recovery:
        assert recover_expired(recovery, env["company"]) == 1
    assert get_detail(env, cid)["conversation"]["status"] == "needs_staff"
