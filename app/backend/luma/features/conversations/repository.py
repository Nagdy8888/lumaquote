from luma.core.errors import DomainError


def conversation(conn, company: str, cid: str, *, lock=False):
    """Fetch a company-scoped conversation, optionally locking it; return 404 without disclosing other tenants."""
    row = conn.execute(
        "select * from luma.conversations where company_id=%s and id=%s" + (" for update" if lock else ""),
        (company, cid),
    ).fetchone()
    if not row:
        raise DomainError("Conversation not found.", 404)
    return row
