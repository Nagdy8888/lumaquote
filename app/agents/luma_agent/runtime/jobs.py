"""Atomic job claiming and fenced status transitions."""

from luma.core.database import database

from .recovery import recover_expired


def claim_job():
    """Claim the next conversation-serialized job while enforcing the two-worker global capacity."""
    with database(worker=True) as conn:
        conn.execute("select pg_advisory_xact_lock(hashtextextended('luma:worker-capacity',0))")
        recover_expired(conn)
        active = conn.execute("select count(*) n from luma.jobs where status='running'").fetchone()["n"]
        if active >= 2:
            return None
        row = conn.execute("""select j.* from luma.jobs j where j.status='queued'
            and not exists(select 1 from luma.jobs r where r.conversation_id=j.conversation_id and r.status='running')
            order by j.created_at for update skip locked limit 1""").fetchone()
        if not row:
            return None
        return conn.execute(
            """update luma.jobs set status='running',fence=fence+1,
            attempts=attempts+1,lease_until=now()+interval '120 seconds'
            where id=%s returning *""",
            (row["id"],),
        ).fetchone()


def finish_job(job, status, error_code=None):
    """Commit an outcome only if this worker still owns the claimed fenced job."""
    with database(worker=True) as conn:
        conn.execute(
            """update luma.jobs set status=%s,error_code=%s,lease_until=null
            where id=%s and fence=%s and status='running'""",
            (status, error_code, job["id"], job["fence"]),
        )
