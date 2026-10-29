"""Isolated synthetic tenants on this project's local-only Supabase stack."""

import secrets
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import psycopg
import pytest
from fastapi.testclient import TestClient
from luma.core.config import settings
from luma.main import app
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row


class TestEnvironment(dict):
    """Keep working fixture credentials available to tests while hiding them from assertion/traceback representations."""

    __test__ = False

    def __repr__(self):
        """Return an intentionally redacted fixture label instead of bearer tokens or database credentials."""
        return "<isolated local Supabase test environment; credentials redacted>"


@pytest.fixture
def environment(monkeypatch):
    """Create an actual Auth principal and separate company; clean only this fixture's exact tenant on teardown."""
    monkeypatch.setenv("ENABLE_PAID_AI", "false")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    settings.cache_clear()
    config = settings()
    dsn = config.database_url.get_secret_value()
    params = conninfo_to_dict(dsn)
    if params.get("host") not in ("127.0.0.1", "localhost") or params.get("port") != "55322":
        pytest.fail("Integration tests require the explicitly isolated local Supabase target.")
    company = uuid4()
    source = uuid4()
    snapshot = uuid4()
    email = f"test-{uuid4()}@lumaquote.local"
    password = secrets.token_urlsafe(20)
    admin_headers = {
        "apikey": config.supabase_service_role_key.get_secret_value(),
        "Authorization": f"Bearer {config.supabase_service_role_key.get_secret_value()}",
    }
    with httpx.Client(timeout=15) as auth:
        created = auth.post(
            config.supabase_url + "/auth/v1/admin/users",
            headers=admin_headers,
            json={"email": email, "password": password, "email_confirm": True},
        )
        created.raise_for_status()
        uid = created.json()["id"]
        login = auth.post(
            config.supabase_url + "/auth/v1/token?grant_type=password",
            headers={"apikey": config.supabase_anon_key.get_secret_value()},
            json={"email": email, "password": password},
        )
        login.raise_for_status()
        token = login.json()["access_token"]
        with psycopg.connect(dsn, row_factory=dict_row) as conn:
            conn.execute(
                "insert into luma.companies(id,name) values(%s,%s)", (company, "Isolated test supplier")
            )
            conn.execute(
                "insert into luma.memberships(user_id,company_id,role) values(%s,%s,'admin')", (uid, company)
            )
            conn.execute(
                "insert into luma.sources(id,company_id,title,object_path) values(%s,%s,%s,%s)",
                (source, company, "Synthetic isolated catalog", f"{company}/catalogs/test.pdf"),
            )
            conn.execute(
                "insert into luma.snapshots(id,company_id,source,observed_at,digest) values(%s,%s,'synthetic',%s,'fixture')",
                (snapshot, company, datetime.now(UTC)),
            )
            products = []
            for sku, price, available in [
                ("DL-001", "32.35", 100),
                ("DL-002", "39.95", 100),
                ("DL-011", "48.00", 0),
            ]:
                pid = uuid4()
                products.append(pid)
                conn.execute(
                    """insert into luma.products(id,company_id,sku,name,family,description,watts,lumens,cct,ip_rating,price,available,source_id,page,snapshot_id)
                    values(%s,%s,%s,'Synthetic downlight','Downlights','Synthetic test evidence',18,1800,4000,'IP44',%s,%s,%s,1,%s)""",
                    (pid, company, sku, price, available, source, snapshot),
                )
        files = []
        with TestClient(app) as api:
            yield TestEnvironment(
                {
                    "api": api,
                    "headers": {"Authorization": f"Bearer {token}"},
                    "user": uid,
                    "email": email,
                    "password": password,
                    "company": company,
                    "products": products,
                    "dsn": dsn,
                    "source": source,
                    "snapshot": snapshot,
                    "files": files,
                }
            )
        # Derive every cleanup target from this fixture's own persisted records,
        # including documents generated before an interrupted browser assertion.
        with psycopg.connect(dsn) as cleanup:
            files.extend(
                f"{company}/quotes/{row[0]}.pdf"
                for row in cleanup.execute(
                    "select id from luma.quotes where company_id=%s", (company,)
                ).fetchall()
            )
        files = list(dict.fromkeys(files))
        if files:
            assert all(name.startswith(f"{company}/") for name in files)
            auth.request(
                "DELETE",
                config.supabase_url + "/storage/v1/object/luma-private",
                headers=admin_headers,
                json={"prefixes": files},
            ).raise_for_status()
        # Cleanup uses an exact generated company identity. No reset/drop or broad
        # deletion can affect the developer's seeded supplier or another project.
        with psycopg.connect(dsn) as conn:
            for table in (
                "operations",
                "approvals",
                "outbox",
                "jobs",
                "usage",
                "inbox",
                "messages",
                "quotes",
                "conversations",
                "products",
                "sources",
                "snapshots",
                "audit",
                "memberships",
            ):
                from psycopg import sql

                conn.execute(
                    sql.SQL("delete from luma.{} where company_id=%s").format(sql.Identifier(table)),
                    (company,),
                )
            conn.execute("delete from luma.companies where id=%s", (company,))
            conn.execute("delete from luma.rate_windows where key like %s", (f"{uid}:%",))
        auth.delete(
            config.supabase_url + f"/auth/v1/admin/users/{uid}", headers=admin_headers
        ).raise_for_status()
    settings.cache_clear()
