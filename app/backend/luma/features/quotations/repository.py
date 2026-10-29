def latest_quote(conn, company, cid, lock=False):
    """Return the highest immutable revision for a scoped conversation, optionally locking the result."""
    return conn.execute(
        """select * from luma.quotes where company_id=%s and conversation_id=%s
        order by revision desc limit 1"""
        + (" for update" if lock else ""),
        (company, cid),
    ).fetchone()
