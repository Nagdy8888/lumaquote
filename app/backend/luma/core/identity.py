from .errors import DomainError


def membership(conn, user_id: str):
    """Resolve the verified user's current active company and role; reject missing or revoked membership."""
    row = conn.execute(
        "select * from luma.memberships where user_id=%s and active order by company_id limit 1", (user_id,)
    ).fetchone()
    if not row:
        raise DomainError("An active staff membership is required.", 403)
    return row
