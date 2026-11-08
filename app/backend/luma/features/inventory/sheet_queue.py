"""Staff side of the Google Sheets stock export: queue one export and read its latest status (D49, T5).

Authority: any active staff member may queue an export and read its status. The rows are only a
request and a progress record; the Apps Script pull protocol that claims and completes them is in
`luma.features.google_sync.stock_exports`. At most one export per company is queued or claimed at a
time (a partial unique index), so pressing the button twice never creates two runs.
"""

from luma.core.audit import audit

_VIEW = "id,status,created_at as requested_at,completed_at,row_counts,error_code"


def view(row) -> dict:
    """Shape an export row for the API: id, status, requested_at, completed_at, row_counts, error_code.

    `None` (no export ever requested) becomes status "none" with empty fields.
    """
    if row is None:
        return {
            "id": None,
            "status": "none",
            "requested_at": None,
            "completed_at": None,
            "row_counts": None,
            "error_code": None,
        }
    return {
        "id": row["id"],
        "status": row["status"],
        "requested_at": row["requested_at"],
        "completed_at": row["completed_at"],
        "row_counts": row["row_counts"],
        "error_code": row["error_code"],
    }


def queue_export(conn, member, user) -> dict:
    """Queue a Sheets export for the staff member's company, or return the one already open.

    The company advisory lock plus the partial unique index decide the race: two simultaneous
    requests produce one row and both receive it. Side effects: one `sheet_exports` insert and an
    audit event `inventory.sheet_export_queued` only when a new row was created. Never commits;
    the route's `operation()` wrapper commits it with the idempotency record.
    """
    company = member["company_id"]
    conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (f"sheet-export:{company}",))
    row = conn.execute(
        f"select {_VIEW} from luma.sheet_exports where company_id=%s and status in ('queued','claimed')",
        (company,),
    ).fetchone()
    if row is None:
        row = conn.execute(
            f"insert into luma.sheet_exports(company_id,requested_by) values(%s,%s) returning {_VIEW}",
            (company, user),
        ).fetchone()
        audit(conn, company, user, "inventory.sheet_export_queued", row["id"])
    return view(row)


def latest_export(conn, member) -> dict:
    """Return the company's most recent export (any status) or status "none"; read only."""
    row = conn.execute(
        f"select {_VIEW} from luma.sheet_exports where company_id=%s order by created_at desc,id desc limit 1",
        (member["company_id"],),
    ).fetchone()
    return view(row)
