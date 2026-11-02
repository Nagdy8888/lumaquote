"""Isolated backup and restore drill for the local Supabase PostgreSQL and private Storage objects.

It dumps the `luma` and `public` schemas (the latter holds the LangGraph checkpoint tables) from this project's local
database container, restores them into a scratch database (`luma_restore_drill`) in the same
container, compares counts and content digests for one company, round-trips that company's
private Storage objects under a scratch prefix, then removes everything it created. The source
database is only read. It never resets, drops or alters source data, and it keeps no backup
file: the dump lives in the container's /tmp and is deleted at the end, so this drill does not
create a 7-day backup retention obligation.

What it proves: a dump of the current logical state restores completely into an empty database and
the recoverable content is identical (row counts, content hashes, checkpoint counts, object bytes).
What it does not prove: volume-level or point-in-time recovery, restoring into a fresh Supabase
stack, Supabase Auth itself (only user ids are stubbed), provider-side data (OpenAI, Meta, Google), or an automated scheduled backup.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import psycopg
from luma.core.config import settings
from luma.core.storage import delete_files, get_file, put_file
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

CONTAINER = "supabase_db_quotation-local-dev"
SCRATCH = "luma_restore_drill"
TABLES = (
    "conversations",
    "messages",
    "quotes",
    "approvals",
    "outbox",
    "jobs",
    "media",
    "drive_exports",
    "products",
    "audit",
)
CHECKPOINT_TABLES = ("checkpoints", "checkpoint_blobs", "checkpoint_writes")


def docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run one docker CLI command with a bounded timeout and no shell."""
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=600, check=check)


def source_params() -> dict:
    """Return the source connection parameters, refusing anything but this project's local database."""
    dsn = settings().database_url.get_secret_value()
    params = conninfo_to_dict(dsn)
    if params.get("host") not in ("127.0.0.1", "localhost") or params.get("port") != "55322":
        raise RuntimeError("The drill is restricted to this project's isolated local database.")
    return {"dsn": dsn, "user": params.get("user", "postgres")}


def snapshot(conn, company: UUID) -> dict:
    """Count rows and hash recoverable content for one company so source and restore can be compared."""
    counts = {
        table: conn.execute(
            f"select count(*) n from luma.{table} where company_id=%s", (company,)
        ).fetchone()["n"]
        for table in TABLES
    }
    digest = hashlib.sha256()
    for row in conn.execute(
        "select id,content_hash from luma.quotes where company_id=%s order by id", (company,)
    ):
        digest.update(f"{row['id']}:{row['content_hash']}".encode())
    for row in conn.execute("select id,body from luma.messages where company_id=%s order by id", (company,)):
        digest.update(f"{row['id']}:{row['body']}".encode())
    threads = f"{company}:%"
    checkpoints = {
        table: conn.execute(
            f"select count(*) n from public.{table} where thread_id like %s", (threads,)
        ).fetchone()["n"]
        for table in CHECKPOINT_TABLES
    }
    return {"rows": counts, "content_sha256": digest.hexdigest(), "checkpoint_rows": checkpoints}


def object_paths(conn, company: UUID) -> list[str]:
    """List this company's private objects recorded in the database (quote PDFs and media originals/previews)."""
    paths = [
        f"{company}/quotes/{r['id']}.pdf"
        for r in conn.execute("select id from luma.quotes where company_id=%s", (company,))
    ]
    for row in conn.execute(
        "select original_path,normalized_path from luma.media where company_id=%s and purged_at is null",
        (company,),
    ):
        paths += [p for p in (row["original_path"], row["normalized_path"]) if p]
    return paths


def prepare_scratch(dsn: str, approvers: list) -> None:
    """Give the empty scratch database what the dump references but does not contain.

    The `luma` schema uses the pgvector type and foreign-keys `auth.users`. Supabase Auth itself
    is not part of this drill, so a stub `auth.users` holding only the user ids (no emails or
    credentials) and a null `auth.uid()` stand in; this is a stated limit of the drill.
    """
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("drop schema public cascade")  # the dump recreates it
        conn.execute("create schema extensions")
        conn.execute("create extension vector with schema extensions")
        conn.execute("create schema auth")
        conn.execute("create table auth.users(id uuid primary key)")
        conn.execute("create function auth.uid() returns uuid language sql as 'select null::uuid'")
        for user in approvers:
            conn.execute("insert into auth.users(id) values(%s)", (user,))


def run(company: UUID, output: Path) -> dict:
    """Perform the drill and return a count/duration-only report; always removes scratch data."""
    source = source_params()
    report = {"company": str(company), "started": datetime.now(UTC).isoformat()}
    with psycopg.connect(source["dsn"], row_factory=dict_row) as conn:
        if not conn.execute("select 1 from luma.companies where id=%s", (company,)).fetchone():
            raise RuntimeError("Unknown company.")
        before = snapshot(conn, company)
        approvers = [r["id"] for r in conn.execute("select id from auth.users")]
        objects = {
            p: hashlib.sha256(data).hexdigest() for p in object_paths(conn, company) if (data := get_file(p))
        }
    report["source"] = before
    report["objects"] = len(objects)
    flags = ["-U", source["user"], "-d", "postgres"]
    docker("exec", CONTAINER, "psql", *flags, "-c", f"drop database if exists {SCRATCH}")
    docker("exec", CONTAINER, "psql", *flags, "-c", f"create database {SCRATCH}")
    params = conninfo_to_dict(source["dsn"])
    params["dbname"] = SCRATCH
    scratch_dsn = psycopg.conninfo.make_conninfo(**params)
    try:
        prepare_scratch(scratch_dsn, approvers)
        start = time.perf_counter()
        docker(
            "exec",
            CONTAINER,
            "pg_dump",
            "-U",
            source["user"],
            "-d",
            "postgres",
            "-Fc",
            "-n",
            "luma",
            "-n",
            "public",
            "-f",
            "/tmp/luma-drill.dump",
        )
        report["dump_seconds"] = round(time.perf_counter() - start, 2)
        size = docker("exec", CONTAINER, "sh", "-c", "wc -c < /tmp/luma-drill.dump").stdout.strip()
        report["dump_bytes"] = int(size)
        start = time.perf_counter()
        restored = docker(
            "exec",
            CONTAINER,
            "pg_restore",
            "-U",
            source["user"],
            "-d",
            SCRATCH,
            "--no-owner",
            "--no-acl",
            "--exit-on-error",
            "/tmp/luma-drill.dump",
            check=False,
        )
        report["restore_seconds"] = round(time.perf_counter() - start, 2)
        report["restore_exit_code"] = restored.returncode
        report["restore_stderr_head"] = restored.stderr[:500]
        if restored.returncode != 0:
            raise RuntimeError("pg_restore failed: " + restored.stderr[:500])
        with psycopg.connect(scratch_dsn, row_factory=dict_row) as copy:
            after = snapshot(copy, company)
        report["restored"] = after
        report["database_identical"] = after == before
    finally:
        docker("exec", CONTAINER, "rm", "-f", "/tmp/luma-drill.dump", check=False)
        docker("exec", CONTAINER, "psql", *flags, "-c", f"drop database if exists {SCRATCH}", check=False)
    scratch_prefix = f"{company}/restore-drill"
    copied, identical = [], True
    try:
        for index, (path, digest) in enumerate(objects.items()):
            target = f"{scratch_prefix}/{index}"
            put_file(target, get_file(path) or b"", "application/octet-stream")
            copied.append(target)
            identical &= hashlib.sha256(get_file(target) or b"").hexdigest() == digest
    finally:
        delete_files(str(company), copied)
    report["objects_round_trip_identical"] = identical
    report["scratch_database_removed"] = (
        SCRATCH
        not in docker("exec", CONTAINER, "psql", *flags, "-Atc", "select datname from pg_database").stdout
    )
    report["finished"] = datetime.now(UTC).isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    """Parse arguments, run the drill and exit nonzero unless the restore and object round trip were identical."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", type=UUID, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.company, args.output)
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "database_identical",
                    "objects_round_trip_identical",
                    "dump_seconds",
                    "restore_seconds",
                    "scratch_database_removed",
                )
            }
        )
    )
    ok = (
        report["database_identical"]
        and report["objects_round_trip_identical"]
        and report["restore_exit_code"] == 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
