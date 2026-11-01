"""Shared PostgreSQL estimated allowance is conservative across midnight and duplicate work."""

from decimal import Decimal
from uuid import uuid4

import psycopg
import pytest
from luma.core.errors import DomainError
from luma_agent.budget import reserve, usage_totals
from psycopg.rows import dict_row


@pytest.mark.parametrize("status", ["reserved", "unknown"])
def test_unresolved_prior_day_call_still_consumes_daily_allowance(environment, status):
    """An in-flight or uncertain provider call must not disappear when UTC changes day."""
    env = environment
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        before = usage_totals(conn)
        conn.execute(
            """insert into luma.usage(id,company_id,job_id,reserved,status,created_at)
            values(%s,%s,%s,0.25,%s,now()-interval '2 days')""",
            (uuid4(), env["company"], uuid4(), status),
        )
        after = usage_totals(conn)
        assert after["daily"] - before["daily"] == Decimal("0.25")
        assert after["total"] - before["total"] == Decimal("0.25")
        conn.rollback()


def test_duplicate_paid_operation_never_reserves_again(environment):
    """A retry cannot silently authorize another provider call using the same durable job identity."""
    env = environment
    job = uuid4()
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        reserve(conn, env["company"], job)
        with pytest.raises(DomainError, match="reconciliation"):
            reserve(conn, env["company"], job)
        assert conn.execute("select count(*) n from luma.usage where job_id=%s", (job,)).fetchone()["n"] == 1
        conn.rollback()


def test_retrieval_requires_settled_room_and_cannot_repeat(environment):
    """A child embedding shares the run allowance and cannot reuse an unresolved primary reservation."""
    env = environment
    job = uuid4()
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        reserve(conn, env["company"], job)
        with pytest.raises(DomainError, match="no remaining"):
            reserve(conn, env["company"], job, operation="retrieval")
        conn.execute("update luma.usage set status='settled',estimated=0.001 where job_id=%s", (job,))
        reserve(conn, env["company"], job, operation="retrieval")
        with pytest.raises(DomainError, match="reconciliation"):
            reserve(conn, env["company"], job, operation="retrieval")
        rows = conn.execute(
            "select operation,reserved from luma.usage where job_id=%s order by operation", (job,)
        ).fetchall()
        assert rows == [
            {"operation": "primary", "reserved": Decimal("0.25")},
            {"operation": "retrieval", "reserved": Decimal("0.01")},
        ]
        conn.rollback()
