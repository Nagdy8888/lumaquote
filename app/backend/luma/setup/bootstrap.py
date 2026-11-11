"""Idempotent, local-only setup. Does not reset data or contact paid providers."""

import json
import secrets
from datetime import UTC, datetime
from io import BytesIO
from uuid import UUID, uuid5

import httpx
import psycopg
from dotenv import dotenv_values, set_key
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from luma.core.config import ROOT, settings
from luma.core.contracts import digest
from luma.core.storage import put_file
from luma.features.inventory.ledger import seed_opening

NAMESPACE = UUID("19a71aa1-1970-4525-ad66-77eda4770091")
COMPANY = uuid5(NAMESPACE, "luma-company")
FAMILIES = [
    ("Downlights", "DL", "Recessed commercial downlight", 18, 1800, 32),
    ("Linear systems", "LN", "Continuous linear luminaire", 36, 4200, 79),
    ("Track lighting", "TR", "Adjustable retail track spotlight", 25, 2500, 58),
    ("High bays", "HB", "Industrial high-bay luminaire", 120, 18000, 145),
    ("Outdoor lighting", "OD", "Weather-resistant exterior floodlight", 50, 6000, 94),
    ("Emergency lighting", "EM", "Maintained emergency bulkhead", 8, 700, 48),
]


def stable(name):
    """Derive reproducible synthetic fixture identities from the project namespace without using real customer identifiers."""
    return uuid5(NAMESPACE, name)


def main():
    """Provision only this local project, migrations, restricted credentials, private synthetic catalogs, and staff access idempotently."""
    config = settings()
    connection = config.database_url.get_secret_value()
    params = conninfo_to_dict(connection)
    if params.get("host") not in ("127.0.0.1", "localhost") or params.get("port") != "55322":
        raise SystemExit("Setup is restricted to this project at 127.0.0.1:55322.")
    local = ROOT / ".local"
    local.mkdir(exist_ok=True)
    env = ROOT / ".env.local"
    values = dotenv_values(env)
    with psycopg.connect(connection, row_factory=dict_row) as conn:
        conn.execute("create table if not exists public.luma_migrations(name text primary key)")
        for migration in sorted((ROOT / "supabase/migrations").glob("*.sql")):
            if not conn.execute(
                "select 1 from public.luma_migrations where name=%s", (migration.name,)
            ).fetchone():
                # The CLI may already have applied a migration during initial startup.
                applied = conn.execute(
                    "select 1 from supabase_migrations.schema_migrations where version=%s",
                    (migration.name.split("_")[0],),
                ).fetchone()
                if not applied:
                    conn.execute(migration.read_text(encoding="utf-8"))
                conn.execute("insert into public.luma_migrations values(%s)", (migration.name,))
        for role, key in [("luma_api", "LUMA_API_DATABASE_URL"), ("luma_worker", "LUMA_WORKER_DATABASE_URL")]:
            existing = values.get(key)
            password = conninfo_to_dict(existing)["password"] if existing else secrets.token_urlsafe(32)
            conn.execute(
                sql.SQL("alter role {} password {}").format(sql.Identifier(role), sql.Literal(password))
            )
            dsn = make_conninfo(**{**params, "user": role, "password": password})
            set_key(str(env), key, dsn)
        conn.execute(
            "insert into luma.companies(id,name) values(%s,%s) on conflict do nothing",
            (COMPANY, "Luma Supply Co."),
        )
    access_file = local / "staff-access.json"
    access = (
        json.loads(access_file.read_text())
        if access_file.exists()
        else {"email": "sales@lumaquote.local", "password": secrets.token_urlsafe(20)}
    )
    headers = {
        "apikey": config.supabase_service_role_key.get_secret_value(),
        "Authorization": f"Bearer {config.supabase_service_role_key.get_secret_value()}",
    }
    with httpx.Client(timeout=15) as client:
        if not access.get("user_id"):
            response = client.post(
                f"{config.supabase_url}/auth/v1/admin/users",
                headers=headers,
                json={**access, "email_confirm": True},
            )
            if response.status_code not in (200, 201):
                raise SystemExit(
                    f"Staff provisioning failed ({response.status_code}); inspect local Auth settings."
                )
            access["user_id"] = response.json()["id"]
            access_file.write_text(json.dumps(access, indent=2), encoding="utf-8")
    with psycopg.connect(connection, row_factory=dict_row) as conn:
        conn.execute(
            """insert into luma.memberships(user_id,company_id,role) values(%s,%s,'admin')
            on conflict do nothing""",
            (access["user_id"], COMPANY),
        )
        snapshot = stable("initial-snapshot")
        conn.execute(
            """insert into luma.snapshots(id,company_id,source,observed_at,digest)
            values(%s,%s,'synthetic',%s,%s) on conflict do nothing""",
            (snapshot, COMPANY, datetime.now(UTC), digest("synthetic-v1")),
        )
        styles = getSampleStyleSheet()
        for family, prefix, label, watts, lumens, base_price in FAMILIES:
            sid = stable(f"source:{prefix}")
            path = f"{COMPANY}/catalogs/{prefix}-v1.pdf"
            conn.execute(
                """insert into luma.sources(id,company_id,title,object_path) values(%s,%s,%s,%s)
                on conflict do nothing""",
                (sid, COMPANY, f"{family} / Technical catalog", path),
            )
            story = [
                Paragraph(f"Luma Supply / {family}", styles["Title"]),
                Paragraph(
                    "Synthetic catalog for portfolio evaluation. Not a real manufacturer specification.",
                    styles["Normal"],
                ),
                Spacer(1, 20),
            ]
            for i in range(12):
                sku = f"{prefix}-{i + 1:03d}"
                cct = [3000, 4000, 5000][i % 3]
                power = watts + (i // 3) * 3
                light = lumens + (i // 3) * 250
                price = base_price + (i // 3) * 8
                ip = "IP65" if prefix in ("OD", "HB") else "IP44"
                name = f"{label} {power}W / {cct}K"
                description = f"{light} lm, {ip}, {cct}K. Fictional technical data; electrical compatibility requires staff confirmation."
                conn.execute(
                    """insert into luma.products(id,company_id,sku,name,family,description,watts,lumens,cct,
                    ip_rating,price,discontinued,source_id,page,snapshot_id)
                    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s) on conflict do nothing""",
                    (
                        stable(sku),
                        COMPANY,
                        sku,
                        name,
                        family,
                        description,
                        power,
                        light,
                        cct,
                        ip,
                        price,
                        i == 11,
                        sid,
                        snapshot,
                    ),
                )
                # Opening stock enters the ledger once; a rerun leaves the current stock alone.
                seed_opening(conn, COMPANY, stable(sku), 0 if i == 10 else 180 - i * 9, "seed")
                story.extend(
                    [
                        Paragraph(sku + " / " + name, styles["Heading3"]),
                        Paragraph(description, styles["Normal"]),
                        Spacer(1, 6),
                    ]
                )
            output = BytesIO()
            SimpleDocTemplate(output, title=f"Luma {family}", topMargin=30, bottomMargin=30).build(story)
            put_file(path, output.getvalue(), "application/pdf")
        requests = [
            (
                "Avery Morgan",
                "Northline Studios",
                "We need 24 DL-002 downlights for our new studio. Please quote 4000K.",
                "review",
            ),
            (
                "Jordan Ellis",
                "Forma Retail",
                "Looking for track lights for a retail fit-out. Can you help choose the right model?",
                "clarifying",
            ),
            (
                "Taylor Reed",
                "Atlas Warehousing",
                "Please quote 18 HB-002 high bays for our warehouse extension.",
                "new",
            ),
        ]
        for name, customer, text, status in requests:
            cid = stable(customer)
            conn.execute(
                """insert into luma.conversations(id,company_id,customer_name,customer_company,recipient,channel,status)
                values(%s,%s,%s,%s,%s,'local_test',%s) on conflict do nothing""",
                (cid, COMPANY, name, customer, f"local:{cid}", status),
            )
            conn.execute(
                """insert into luma.messages(id,company_id,conversation_id,actor,body)
                values(%s,%s,%s,'customer',%s) on conflict(id) do nothing""",
                (stable(f"message:{customer}"), COMPANY, cid, text),
            )
    settings.cache_clear()
    # Seed one genuine reviewable revision through the same business interface
    # used by staff. Never fabricate an approval, send, or delivery outcome.
    from luma.core.database import database
    from luma.features.conversations.repository import conversation
    from luma.features.quotations.drafting import draft
    from luma.features.quotations.repository import latest_quote
    from luma.features.quotations.schemas import DraftInput, Selection

    with database(access["user_id"]) as conn:
        member = {"company_id": COMPANY, "role": "admin"}
        cid = stable("Northline Studios")
        current = conversation(conn, COMPANY, cid, lock=True)
        if not latest_quote(conn, COMPANY, cid):
            draft(
                conn,
                member,
                access["user_id"],
                cid,
                DraftInput(
                    expected_version=current["version"],
                    lines=[Selection(product_id=stable("DL-002"), quantity=24)],
                ),
            )
        conn.execute(
            """update luma.conversations c set status='new'
            where c.id=any(%s) and not exists(select 1 from luma.quotes q where q.conversation_id=c.id)
            and not exists(select 1 from luma.messages m where m.conversation_id=c.id and m.actor<>'customer')""",
            ([stable("Forma Retail"), stable("Atlas Warehousing")],),
        )
    # Checkpoint DDL is a migration task and must not run in every worker startup.
    from langgraph.checkpoint.postgres import PostgresSaver

    with PostgresSaver.from_conn_string(connection) as saver:
        saver.setup()
    with psycopg.connect(connection) as conn:
        conn.execute(
            "grant select,insert,update,delete on public.checkpoints,public.checkpoint_blobs,public.checkpoint_writes to luma_worker"
        )
        conn.execute("grant select on public.checkpoint_migrations to luma_worker")
    print("Local setup complete: 72 synthetic products, six private catalogs, three requests.")
    print("Staff sign-in credentials are in ignored .local/staff-access.json (not printed).")


if __name__ == "__main__":
    main()
