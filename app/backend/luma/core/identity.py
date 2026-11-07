from .errors import DomainError


def membership(conn, user_id: str):
    """Resolve the verified user's current active company and role; reject missing or revoked membership."""
    row = conn.execute(
        "select * from luma.memberships where user_id=%s and active order by company_id limit 1", (user_id,)
    ).fetchone()
    if not row:
        raise DomainError("An active staff membership is required.", 403)
    return row


def require_admin(member, action: str) -> None:
    """Allow only an administrator membership; raise a plain 403 "Only an administrator can <action>." otherwise.

    `member` is the row `membership()` returned for the verified user, so the role is read from the
    database and never from the request. Services call this before any write that the staff
    matrix reserves for administrators (stock adjustments, reorder levels, purchase orders).
    """
    if member["role"] != "admin":
        raise DomainError(f"Only an administrator can {action}.", 403)
