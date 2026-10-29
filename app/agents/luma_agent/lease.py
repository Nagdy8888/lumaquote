from luma.core.errors import DomainError


def assert_request_version(current, state):
    """Reject preparation or clarification based on a request changed since extraction began, preserving staff/customer edits."""
    if current["version"] != state.get("observed_version"):
        raise DomainError(
            "The request changed during preparation. Review the latest conversation before retrying."
        )


def assert_job(conn, state):
    """Reject side effects when the persisted job no longer holds the matching live fenced lease."""
    row = conn.execute(
        "select 1 from luma.jobs where id=%s and fence=%s and status='running' and lease_until>now()",
        (state["job_id"], state["fence"]),
    ).fetchone()
    if not row:
        raise DomainError("Worker lease no longer valid.")
