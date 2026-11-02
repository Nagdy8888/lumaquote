"""Operator retention tool: seven-day runtime media and 90-day business data for one explicit company.

Default is a dry run that only counts. `--execute` deletes. It uses the privileged local setup DSN
(`DATABASE_URL`), refuses anything but this project's isolated local database, and requires an
explicit company id, so it can never be pointed at another tenant or an unknown server. It is
an operator command, not a scheduled job: nothing runs it automatically yet.

Policy (from the approved plan):
- Runtime media (private original and normalized objects): deleted after 7 days. The row is kept with
  `purged_at`; its transcript/reading text is business data and follows the 90-day rule below.
- Business data: a conversation idle for more than 90 days is deleted with its messages, quotes,
  approvals, outbox, jobs, Drive exports, media rows, idempotency responses (they embed the
  conversation), quote PDFs, private media and LangGraph checkpoint thread. A conversation with unfinished work (queued/running jobs, queued/submitting sends)
  is skipped and reported. Audit events and WhatsApp inbox rows older than 90 days are deleted.
- Preserved on purpose: `luma.usage` (financial/budget accounting holds only opaque ids and amounts)
  and the catalog, snapshots and sources (commercial reference data, not customer data).
- Not covered: provider-side copies (OpenAI, LangSmith, Meta, Google Drive/Sheets), database backups
  and the local Docker volume. Deleting a Drive copy of a quotation is not done here.
"""

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from uuid import UUID

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from luma.core.config import settings
from luma.core.storage import delete_files
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

MEDIA_DAYS = 7
BUSINESS_DAYS = 90


def connect():
    """Open the privileged connection, refusing any target but this project's local database."""
    dsn = settings().database_url.get_secret_value()
    params = conninfo_to_dict(dsn)
    if params.get("host") not in ("127.0.0.1", "localhost") or params.get("port") != "55322":
        raise RuntimeError("Retention is restricted to this project's isolated local database.")
    return psycopg.connect(dsn, row_factory=dict_row)


def expired_media(conn, company: UUID, now: datetime) -> list[dict]:
    """Return media rows older than seven days whose private objects have not been purged yet."""
    return conn.execute(
        """select message_id,original_path,normalized_path from luma.media
        where company_id=%s and purged_at is null and created_at < %s""",
        (company, now - timedelta(days=MEDIA_DAYS)),
    ).fetchall()


def purge_media(conn, company: UUID, now: datetime, execute: bool) -> dict:
    """Delete expired runtime media objects, then stamp their rows; a rerun is a no-op."""
    rows = expired_media(conn, company, now)
    paths = [p for row in rows for p in (row["original_path"], row["normalized_path"]) if p]
    if execute and rows:
        delete_files(str(company), paths)
        conn.execute(
            "update luma.media set purged_at=now() where company_id=%s and message_id=any(%s)",
            (company, [row["message_id"] for row in rows]),
        )
    return {"media_rows": len(rows), "objects": len(paths)}


def idle_conversations(conn, company: UUID, now: datetime) -> tuple[list[UUID], list[UUID]]:
    """Split conversations idle for 90+ days into (deletable, skipped because work is unfinished)."""
    rows = conn.execute(
        """select c.id,
        exists(select 1 from luma.jobs j where j.conversation_id=c.id and j.status in ('queued','running'))
        or exists(select 1 from luma.outbox o where o.conversation_id=c.id and o.status in ('queued','submitting'))
        or exists(select 1 from luma.drive_exports d join luma.quotes q on q.id=d.quote_id and q.company_id=d.company_id
                  where q.conversation_id=c.id and d.status in ('queued','claimed')) as busy
        from luma.conversations c where c.company_id=%s and c.updated_at < %s""",
        (company, now - timedelta(days=BUSINESS_DAYS)),
    ).fetchall()
    return [r["id"] for r in rows if not r["busy"]], [r["id"] for r in rows if r["busy"]]


def purge_conversations(conn, company: UUID, ids: list[UUID], execute: bool) -> dict:
    """Delete the listed conversations and everything that hangs off them, children before parents."""
    if not ids:
        return {"conversations": 0, "objects": 0}
    quotes = [
        r["id"]
        for r in conn.execute("select id from luma.quotes where conversation_id=any(%s)", (ids,)).fetchall()
    ]
    media = conn.execute(
        "select original_path,normalized_path from luma.media where conversation_id=any(%s)", (ids,)
    ).fetchall()
    paths = [f"{company}/quotes/{q}.pdf" for q in quotes] + [
        p for row in media for p in (row["original_path"], row["normalized_path"]) if p
    ]
    if execute:
        statements = [
            ("delete from luma.operations where company_id=%s and split_part(action,':',2)=any(%s)", None),
            ("delete from luma.drive_exports where quote_id=any(%s)", quotes),
            ("delete from luma.approvals where quote_id=any(%s)", quotes),
            ("delete from luma.outbox where conversation_id=any(%s)", ids),
            ("delete from luma.jobs where conversation_id=any(%s)", ids),
            ("delete from luma.media where conversation_id=any(%s)", ids),
            ("delete from luma.messages where conversation_id=any(%s)", ids),
            ("delete from luma.quotes where conversation_id=any(%s)", ids),
            ("delete from luma.conversations where id=any(%s)", ids),
        ]
        for statement, values in statements:
            if values is None:  # idempotency responses embed the conversation detail, so they go with it
                conn.execute(statement, (company, [str(cid) for cid in ids]))
            else:
                conn.execute(statement, (values,))
        conn.commit()
        delete_files(str(company), paths)
        with PostgresSaver.from_conn_string(settings().luma_worker_database_url.get_secret_value()) as saver:
            for cid in ids:
                saver.delete_thread(f"{company}:{cid}")
    return {"conversations": len(ids), "objects": len(paths)}


def purge_records(conn, company: UUID, now: datetime, execute: bool) -> dict:
    """Delete audit events and WhatsApp inbox rows older than 90 days (counts only in a dry run)."""
    cutoff = now - timedelta(days=BUSINESS_DAYS)
    counts = {}
    for name, table, column in (("audit", "luma.audit", "created_at"), ("inbox", "luma.inbox", "created_at")):
        query = f"{'delete' if execute else 'select count(*) n'} from {table} where company_id=%s and {column} < %s"
        result = conn.execute(query + (" returning 1" if execute else ""), (company, cutoff))
        counts[name] = len(result.fetchall()) if execute else result.fetchone()["n"]
    return counts


def run(company: UUID, now: datetime, execute: bool) -> dict:
    """Plan or perform every retention step for one company and return a count-only report."""
    with connect() as conn:
        found = conn.execute("select id from luma.companies where id=%s", (company,)).fetchone()
        if not found:
            raise RuntimeError("Unknown company.")
        media = purge_media(conn, company, now, execute)
        deletable, skipped = idle_conversations(conn, company, now)
        business = purge_conversations(conn, company, deletable, execute)
        records = purge_records(conn, company, now, execute)
        conn.commit()
    return {
        "mode": "execute" if execute else "dry-run",
        "as_of": now.isoformat(),
        "media": media,
        "conversations": business,
        "skipped_unfinished_conversations": len(skipped),
        "records_older_than_90_days": records,
        "preserved": ["luma.usage", "catalog/snapshots/sources"],
    }


def main() -> int:
    """Parse arguments and print the report; `--now` exists so tests and drills can age data deterministically."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", type=UUID, required=True)
    parser.add_argument("--execute", action="store_true", help="delete instead of counting")
    parser.add_argument("--now", help="ISO timestamp to treat as the current time (testing)")
    args = parser.parse_args()
    now = datetime.fromisoformat(args.now) if args.now else datetime.now(UTC)
    print(json.dumps(run(args.company, now, args.execute), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
