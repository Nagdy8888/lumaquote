from uuid import uuid4

from psycopg.types.json import Jsonb

from .errors import DomainError


def rate_limit(conn, key: str, limit: int):
    """Atomically count shared minute-window admission and reject excess requests while preserving the counter."""
    row = conn.execute(
        """insert into luma.rate_windows(key,bucket_window,count)
        values(%s,floor(extract(epoch from now())/60)::bigint,1)
        on conflict(key,bucket_window) do update set count=rate_windows.count+1 returning count""",
        (key,),
    ).fetchone()
    if row["count"] > limit:
        # Caller must commit this denial to retain shared admission accounting.
        conn.commit()
        raise DomainError("Too many requests. Try again in one minute.", 429)


def enqueue(conn, company, cid, kind="agent", payload=None):
    """Create a durable scoped job under the queue-capacity lock; raise a recoverable error when full."""
    conn.execute("select pg_advisory_xact_lock(hashtextextended('luma:queue',0))")
    count = conn.execute("select count(*) n from luma.jobs where status in ('queued','running')").fetchone()[
        "n"
    ]
    if count >= 100:
        raise DomainError("The work queue is full. Try again shortly.", 503)
    jid = uuid4()
    conn.execute(
        "insert into luma.jobs(id,company_id,conversation_id,kind,payload) values(%s,%s,%s,%s,%s)",
        (jid, company, cid, kind, Jsonb(payload or {})),
    )
    return jid
