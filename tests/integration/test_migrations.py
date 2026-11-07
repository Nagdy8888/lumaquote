"""Clean-install and upgrade checks for `supabase/migrations/` in a disposable database.

The local Supabase database is only read. A scratch database is created next to it with just the
Supabase objects the migrations reference (`auth.users`, `auth.uid()`, `storage.buckets`, the
`extensions` schema), every migration is applied in order, and the result is compared with the live
local schema. An upgrade test applies the older migrations, plants pending synthetic work, applies
the rest and checks nothing was lost. Synthetic data only; the scratch database is always dropped.
"""

from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row

MIGRATIONS = sorted((Path(__file__).resolve().parents[2] / "supabase/migrations").glob("*.sql"))
SCRATCH = "luma_migration_check"
STUBS = """
create schema if not exists extensions;
create schema if not exists auth;
create table if not exists auth.users(id uuid primary key);
create or replace function auth.uid() returns uuid language sql stable as
  $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create schema if not exists storage;
create table if not exists storage.buckets(
  id text primary key, name text, public boolean, file_size_limit bigint);
"""
# Catalog queries that describe the luma schema; ordering makes the comparison deterministic.
SHAPE = {
    "columns": """select table_name, column_name, data_type, is_nullable, column_default
        from information_schema.columns where table_schema='luma' order by 1, 2""",
    "constraints": """select c.conrelid::regclass::text as table_name, conname, pg_get_constraintdef(c.oid) as definition
        from pg_constraint c join pg_namespace n on n.oid=c.connamespace
        where n.nspname='luma' and c.contype <> 'n' order by 1, 2""",
    "indexes": "select tablename, indexname, indexdef from pg_indexes where schemaname='luma' order by 1, 2",
    "policies": """select tablename, policyname, cmd, qual, with_check
        from pg_policies where schemaname='luma' order by 1, 2""",
    "grants": """select table_name, grantee, privilege_type from information_schema.role_table_grants
        where table_schema='luma' and grantee in ('luma_api','luma_worker','anon','authenticated')
        order by 1, 2, 3""",
    "functions": """select p.proname, pg_get_function_arguments(p.oid) as args, p.prosecdef as security_definer
        from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='luma' order by 1, 2""",
    "triggers": """select event_object_table, trigger_name, action_timing, event_manipulation
        from information_schema.triggers where trigger_schema='luma' order by 1, 2, 4""",
    "rls_enabled": """select c.relname, c.relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace
        where n.nspname='luma' and c.relkind='r' order by 1""",
}


def shape(conn) -> dict[str, list]:
    """Describe the luma schema (columns, constraints, indexes, policies, grants, functions, triggers, RLS)."""
    return {
        name: [tuple(row.values()) for row in conn.execute(sql).fetchall()] for name, sql in SHAPE.items()
    }


def apply(conn, files) -> None:
    """Run migration files in order inside one connection; a failure names the file."""
    for path in files:
        try:
            conn.execute(path.read_text(encoding="utf-8"))
            conn.commit()
        except psycopg.Error as failure:
            conn.rollback()
            pytest.fail(f"{path.name} failed: {type(failure).__name__}: {failure}")


@pytest.fixture
def scratch(environment):
    """Create an empty scratch database with Supabase stand-ins, hand back a connection, always drop it."""
    params = conninfo_to_dict(environment["dsn"])
    with psycopg.connect(environment["dsn"], autocommit=True) as admin:
        admin.execute(f'drop database if exists "{SCRATCH}" with (force)')
        admin.execute(f'create database "{SCRATCH}"')
    scratch_dsn = make_conninfo(**{**params, "dbname": SCRATCH})
    try:
        with psycopg.connect(scratch_dsn, row_factory=dict_row) as conn:
            conn.execute(STUBS)
            conn.commit()
            yield conn
    finally:
        with psycopg.connect(environment["dsn"], autocommit=True) as admin:
            admin.execute(f'drop database if exists "{SCRATCH}" with (force)')


def test_all_migrations_apply_cleanly_and_match_the_live_schema(environment, scratch):
    """A clean install reproduces exactly the schema the local stack runs, so a reset cannot drift."""
    assert len(MIGRATIONS) >= 15
    apply(scratch, MIGRATIONS)
    fresh = shape(scratch)
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as live_conn:
        live = shape(live_conn)
    for name in SHAPE:
        assert fresh[name] == live[name], f"{name} differs between a clean install and the live database"
    assert fresh["columns"] and fresh["policies"] and fresh["rls_enabled"]
    exposed = [row for row in fresh["grants"] if row[1] in ("anon", "authenticated")]
    assert exposed == [], f"browser-facing Supabase roles hold grants on luma tables: {exposed}"
    bucket = scratch.execute("select public from storage.buckets where id='luma-private'").fetchone()
    assert bucket == {"public": False}
    assert all(enabled for _, enabled in fresh["rls_enabled"] if _ not in {"rate_windows"}), fresh[
        "rls_enabled"
    ]


def test_upgrade_keeps_pending_work(scratch):
    """A pending job and its conversation, created under the first ten migrations, survive the later five."""
    base = MIGRATIONS[:10]
    later = MIGRATIONS[10:]
    apply(scratch, base)
    company, user, conversation, job = uuid4(), uuid4(), uuid4(), uuid4()
    scratch.execute("insert into auth.users(id) values(%s)", (user,))
    scratch.execute("insert into luma.companies(id,name) values(%s,'Upgrade check supplier')", (company,))
    scratch.execute(
        "insert into luma.conversations(id,company_id,customer_name,recipient,channel) values(%s,%s,'Synthetic','synthetic-recipient','local_test')",
        (conversation, company),
    )
    scratch.execute(
        "insert into luma.jobs(id,company_id,conversation_id,kind,payload) values(%s,%s,%s,'agent','{}')",
        (job, company, conversation),
    )
    scratch.commit()
    apply(scratch, later)
    kept = scratch.execute(
        "select j.status, c.customer_name from luma.jobs j join luma.conversations c on c.id=j.conversation_id "
        "where j.id=%s",
        (job,),
    ).fetchone()
    assert kept == {"status": "queued", "customer_name": "Synthetic"}
    assert scratch.execute("select count(*) n from luma.jobs").fetchone()["n"] == 1
