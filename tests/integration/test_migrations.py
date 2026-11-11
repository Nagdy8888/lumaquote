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


STOCK_MIGRATION = "20261107030000_stock_ledger.sql"
STOCK_TABLES = (
    "stock_levels",
    "stock_movements",
    "stock_reservations",
    "orders",
    "order_lines",
    "purchase_orders",
    "purchase_order_lines",
    "stock_alerts",
    "sheet_exports",
    "document_counters",
)


def test_stock_ledger_backfills_every_product_then_drops_available(scratch):
    """Stock copied into the ledger equals the old column per product before it is dropped (D49).

    A product with stock gets one opening movement; a product with none gets a level row and no
    movement. After the migration the column is gone and a quotation may be accepted or declined.
    """
    names = [path.name for path in MIGRATIONS]
    split = names.index(STOCK_MIGRATION)
    apply(scratch, MIGRATIONS[:split])
    company, source, snapshot, conversation = uuid4(), uuid4(), uuid4(), uuid4()
    scratch.execute("insert into luma.companies(id,name) values(%s,'Backfill check supplier')", (company,))
    scratch.execute(
        "insert into luma.sources(id,company_id,title,object_path) values(%s,%s,'Catalog','catalog.pdf')",
        (source, company),
    )
    scratch.execute(
        "insert into luma.snapshots(id,company_id,source,observed_at,digest) values(%s,%s,'synthetic',now(),'d')",
        (snapshot, company),
    )
    stock = {"BF-001": 120, "BF-002": 7, "BF-003": 0}
    ids = {}
    for sku, available in stock.items():
        ids[sku] = uuid4()
        scratch.execute(
            """insert into luma.products(id,company_id,sku,name,family,description,watts,lumens,cct,ip_rating,
            price,available,source_id,page,snapshot_id) values(%s,%s,%s,'Name','Family','Text',10,1000,4000,'IP44',
            9.50,%s,%s,1,%s)""",
            (ids[sku], company, sku, available, source, snapshot),
        )
    scratch.execute(
        "insert into luma.conversations(id,company_id,customer_name,recipient,channel) values(%s,%s,'Synthetic','r','local_test')",
        (conversation, company),
    )
    scratch.commit()
    apply(scratch, MIGRATIONS[split:])
    levels = {
        row["sku"]: row
        for row in scratch.execute(
            """select p.sku,l.on_hand,l.reserved,l.reorder_level,
            coalesce((select sum(delta) from luma.stock_movements m where m.product_id=p.id),0)::int moved,
            (select count(*) from luma.stock_movements m where m.product_id=p.id) movements
            from luma.products p join luma.stock_levels l on l.product_id=p.id where p.company_id=%s""",
            (company,),
        ).fetchall()
    }
    assert {sku: row["on_hand"] for sku, row in levels.items()} == stock
    assert {sku: row["moved"] for sku, row in levels.items()} == stock
    assert [levels[sku]["movements"] for sku in stock] == [1, 1, 0]
    assert all(row["reserved"] == 0 and row["reorder_level"] == 20 for row in levels.values())
    assert (
        scratch.execute(
            "select 1 from information_schema.columns where table_schema='luma' and table_name='products' and column_name='available'"
        ).fetchone()
        is None
    )
    for status in ("accepted", "declined"):
        scratch.execute(
            """insert into luma.quotes(id,company_id,conversation_id,number,revision,status,recipient,snapshot_id,
            content,content_hash,valid_until) values(%s,%s,%s,%s,%s,%s,'r',%s,'{}','h',now()+interval '1 day')""",
            (uuid4(), company, conversation, "LQ-" + status, 1 if status == "accepted" else 2, status, snapshot),
        )
    with pytest.raises(psycopg.errors.CheckViolation):
        scratch.execute(
            """insert into luma.quotes(id,company_id,conversation_id,number,revision,status,recipient,snapshot_id,
            content,content_hash,valid_until) values(%s,%s,%s,'LQ-bad',3,'unknown','r',%s,'{}','h',now())""",
            (uuid4(), company, conversation, snapshot),
        )
    scratch.rollback()


def test_stock_tables_are_protected_and_the_ledger_is_append_only(scratch):
    """Every new table has row-level security with both scopes and no browser-role grant; movements never change."""
    apply(scratch, MIGRATIONS)
    state = {
        row["relname"]: row["relrowsecurity"]
        for row in scratch.execute(
            """select relname,relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace
            where n.nspname='luma' and c.relkind='r'"""
        ).fetchall()
    }
    policies = {}
    for row in scratch.execute("select tablename,policyname from pg_policies where schemaname='luma'").fetchall():
        policies.setdefault(row["tablename"], set()).add(row["policyname"])
    grants = {}
    for row in scratch.execute(
        """select table_name,grantee,privilege_type from information_schema.role_table_grants
        where table_schema='luma' and table_name = any(%s)""",
        (list(STOCK_TABLES),),
    ).fetchall():
        grants.setdefault((row["table_name"], row["grantee"]), set()).add(row["privilege_type"])
    for table in STOCK_TABLES:
        assert state[table] is True, f"{table} has no row-level security"
        assert policies[table] == {"staff_scope", "worker_scope"}, table
        assert not any(who in ("anon", "authenticated", "PUBLIC") for (name, who) in grants if name == table)
    # Append-only ledger: nobody may update or delete a movement; the worker never inserts one.
    assert grants[("stock_movements", "luma_api")] == {"SELECT", "INSERT"}
    assert grants[("stock_movements", "luma_worker")] == {"SELECT"}
    # One queued or claimed Sheets export per company is a database rule, not only application logic.
    index = scratch.execute(
        "select indexdef from pg_indexes where schemaname='luma' and indexname='sheet_exports_one_open'"
    ).fetchone()
    assert index and "UNIQUE" in index["indexdef"] and "queued" in index["indexdef"]
