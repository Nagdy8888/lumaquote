from decimal import Decimal
from uuid import uuid4

from luma.core.config import settings
from luma.core.errors import DomainError


def reserve(conn, company, jid, *, operation="primary"):
    """Reserve shared estimated allowance per operation while keeping all operations within the run cap.

    Primary calls reserve the full configured run allowance. Retrieval can reserve
    at most one cent only after enough earlier consumption has settled; neither
    retries nor child calls increase the run maximum.
    """
    if operation not in ("primary", "retrieval"):
        raise DomainError("Unknown paid operation class.")
    config = settings()
    conn.execute("select pg_advisory_xact_lock(hashtextextended('luma:budget',0))")
    previous = conn.execute(
        "select * from luma.usage where job_id=%s and operation=%s", (jid, operation)
    ).fetchone()
    if previous:
        raise DomainError("This paid operation requires reconciliation before another provider call.")
    totals = usage_totals(conn)
    maximum = Decimal(str(config.reservation))
    amount = maximum if operation == "primary" else min(maximum, Decimal("0.01"))
    consumed = conn.execute(
        """select coalesce(sum(case when status in ('reserved','unknown') then reserved
        when status='settled' then estimated else 0 end),0) amount from luma.usage where job_id=%s""",
        (jid,),
    ).fetchone()["amount"]
    if consumed + amount > maximum:
        raise DomainError("This run has no remaining estimated allowance for another operation.", 429)
    if totals["total"] + amount > Decimal(str(config.total_budget)) or totals["daily"] + amount > Decimal(
        str(config.daily_budget)
    ):
        raise DomainError("Estimated AI allowance exhausted. Staff can continue manually.", 429)
    conn.execute(
        "insert into luma.usage(id,company_id,job_id,reserved,operation) values(%s,%s,%s,%s,%s)",
        (uuid4(), company, jid, amount, operation),
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
