from luma.core.errors import DomainError


def assert_job(conn, state):
    """Reject side effects when the persisted job no longer holds the matching live fenced lease."""
    row = conn.execute(
        "select 1 from luma.jobs where id=%s and fence=%s and status='running' and lease_until>now()",
        (state["job_id"], state["fence"]),
    ).fetchone()
    if not row:
        raise DomainError("Worker lease no longer valid.")
