from luma.core.errors import DomainError


def assert_request_version(current, state):
    """Reject preparation or clarification based on a request changed since extraction began, preserving staff/customer edits."""
    if current["version"] != state.get("observed_version"):
        raise DomainError(
            "The request changed during preparation. Review the latest conversation before retrying."
        )


def assert_job(conn, state):
    """Reject stale leases and hold a shared row lock so recovery cannot fence a transaction mid-effect."""
    row = conn.execute(
        "select 1 from luma.jobs where id=%s and fence=%s and status='running' and lease_until>now() for share",
        (state["job_id"], state["fence"]),
    ).fetchone()
    if not row:
        raise DomainError("Worker lease no longer valid.")
