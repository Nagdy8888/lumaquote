"""Gap-tolerant, lock-serialized document numbers per company (decision D49).

Sales orders are `SO-0001` and purchase orders `PO-0001`. The counters live in
`luma.document_counters`; this module is the only writer of that table.
"""

PREFIXES = {"order": "SO", "purchase_order": "PO"}


def next_number(conn, company, kind: str) -> str:
    """Return the next number of `kind` (`order` or `purchase_order`) for the company, such as `SO-0001`.

    The counter row is created on first use and advanced by one upsert, so two concurrent
    transactions queue on the row lock and receive different numbers. Numbers are gap-tolerant:
    a rolled-back transaction rolls the increment back with it, a committed one never repeats.
    Runs inside the caller's transaction and never commits. Raises KeyError for an unknown kind.
    """
    prefix = PREFIXES[kind]
    row = conn.execute(
        """insert into luma.document_counters(company_id,kind,next_value) values(%s,%s,2)
        on conflict(company_id,kind) do update set next_value=document_counters.next_value+1
        returning next_value""",
        (company, kind),
    ).fetchone()
    return f"{prefix}-{row['next_value'] - 1:04d}"
