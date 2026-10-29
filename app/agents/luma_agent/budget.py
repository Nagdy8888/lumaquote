from decimal import Decimal
from uuid import uuid4

from luma.core.config import settings
from luma.core.errors import DomainError


def reserve(conn, company, jid):
    """Atomically reserve estimated AI allowance across all workers before any paid provider request."""
    config = settings()
    conn.execute("select pg_advisory_xact_lock(hashtextextended('luma:budget',0))")
    previous = conn.execute("select * from luma.usage where job_id=%s", (jid,)).fetchone()
    if previous:
        raise DomainError("This paid operation requires reconciliation before another provider call.")
    totals = usage_totals(conn)
    amount = Decimal(str(config.reservation))
    if totals["total"] + amount > Decimal(str(config.total_budget)) or totals["daily"] + amount > Decimal(
        str(config.daily_budget)
    ):
        raise DomainError("Estimated AI allowance exhausted. Staff can continue manually.", 429)
    conn.execute(
        "insert into luma.usage(id,company_id,job_id,reserved) values(%s,%s,%s,%s)",
        (uuid4(), company, jid, amount),
    )


def usage_totals(conn):
    """Count all unresolved reservations against both allowances, including calls crossing the UTC day boundary.

    Settled estimates count toward the day they started. Unknown provider outcomes
    remain conservatively reserved until explicit reconciliation; elapsed time
    never frees estimated allowance.
    """
    return conn.execute("""select coalesce(sum(case when status in ('reserved','unknown') then reserved
        when status='settled' then estimated else 0 end),0) total,
        coalesce(sum(case when status in ('reserved','unknown') then reserved
        when status='settled' and created_at>=date_trunc('day',now() at time zone 'UTC') at time zone 'UTC'
        then estimated else 0 end),0) daily from luma.usage""").fetchone()
