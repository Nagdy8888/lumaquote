"""GAS-only snapshot contract tested through HTTP and actual isolated PostgreSQL."""

import hashlib
import hmac
import json
import time
from copy import deepcopy
from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient
from luma.core.config import settings
from luma.features.google_sync.validation import POLICIES
from luma.google_gateway import app
from psycopg.rows import dict_row


def test_complete_snapshot_import_and_rejections(environment, monkeypatch):
    """Atomic imports update price, preserve catalog identity, refresh unchanged data and reject unsafe input.

    Stock belongs to the ledger (D49): the Inventory table is ignored and never changes stock.
    """
    company = environment["company"]
    secret = "synthetic-gas-key-" + "x" * 32
    monkeypatch.setenv("GOOGLE_COMPANY_ID", str(company))
    monkeypatch.setenv("GOOGLE_SHEET_ID", "fixture-workbook")
    monkeypatch.setenv("GOOGLE_CALLBACK_SECRET", secret)
    settings.cache_clear()
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as conn:
        rows = conn.execute(
            """select p.*,coalesce(sl.on_hand-sl.reserved,0) as available from luma.products p
            left join luma.stock_levels sl on sl.company_id=p.company_id and sl.product_id=p.id
            where p.company_id=%s order by p.sku""",
            (company,),
        ).fetchall()
    fields = ("sku", "name", "family", "watts", "lumens", "cct", "ip_rating", "pack_size", "discontinued")
    tables = dict(
        Products=[{key: row[key] for key in fields} for row in rows],
        Prices=[
            dict(sku=row["sku"], currency="USD", unit_price=str(row["price"]), effective_from="2026-01-01")
            for row in rows
        ],
        Inventory=[
            dict(sku=row["sku"], available=row["available"], location="Synthetic warehouse") for row in rows
        ],
        Policies=[dict(key=key, value=value) for key, value in POLICIES.items()],
    )
    envelope = dict(
        schema_version=1,
        company_id=str(company),
        spreadsheet_id="fixture-workbook",
        timestamp=int(time.time()) - 3,
        nonce=str(uuid4()),
        event="supplier_snapshot",
        tables=tables,
    )

    def send(value, valid=True):
        """Sign a fixture envelope and submit it through the callback-only gateway."""
        body = json.dumps(value).encode()
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest() if valid else "0" * 64
        with TestClient(app) as client:
            return client.post(
                "/callbacks/google/snapshot", content=body, headers={"X-Luma-Signature": signature}
            )

    assert send(envelope, False).status_code == 401
    result = send(envelope)
    assert result.status_code == 202, result.json()
    assert result.json()["sync_status"] == "validated"
    assert send(envelope).json()["sync_status"] == "duplicate"
    with psycopg.connect(environment["dsn"]) as conn:
        first = conn.execute(
            "select snapshot_id from luma.google_sync_state where company_id=%s", (company,)
        ).fetchone()[0]
    heartbeat = {**envelope, "nonce": str(uuid4()), "timestamp": envelope["timestamp"] + 1}
    assert send(heartbeat).status_code == 202
    with psycopg.connect(environment["dsn"]) as conn:
        assert (
            conn.execute(
                "select snapshot_id from luma.google_sync_state where company_id=%s", (company,)
            ).fetchone()[0]
            == first
        )
    changed = deepcopy(envelope)
    changed.update(nonce=str(uuid4()), timestamp=envelope["timestamp"] + 2)
    changed["tables"]["Prices"][0]["unit_price"] = "47.29"
    changed["tables"]["Inventory"][0]["available"] = 17
    assert send(changed).status_code == 202
    with psycopg.connect(environment["dsn"]) as conn:
        row = conn.execute(
            """select p.price,coalesce(sl.on_hand-sl.reserved,0),p.snapshot_id,
            (select count(*) from luma.stock_movements m where m.company_id=p.company_id) from luma.products p
            left join luma.stock_levels sl on sl.company_id=p.company_id and sl.product_id=p.id
            where p.company_id=%s and p.sku=%s""",
            (company, rows[0]["sku"]),
        ).fetchone()
        # The changed Inventory value (17) is ignored: stock stays what the ledger holds.
        assert str(row[0]) == "47.29" and row[1] == rows[0]["available"] != 17 and row[2] != first
        assert row[3] == 2  # only the two fixture opening movements (DL-011 has no stock)
    assert send({**heartbeat, "nonce": str(uuid4())}).status_code == 409
    for mutation in ("duplicate", "missing", "policy", "future", "specification"):
        bad = deepcopy(changed)
        bad.update(nonce=str(uuid4()), timestamp=envelope["timestamp"] + 3)
        if mutation == "duplicate":
            bad["tables"]["Prices"].append(bad["tables"]["Prices"][0])
        elif mutation == "missing":
            bad["tables"]["Prices"].pop()
        elif mutation == "policy":
            bad["tables"]["Policies"][0]["value"] = "Unsupported policy"
        elif mutation == "future":
            bad["tables"]["Prices"][0]["effective_from"] = "2099-01-01"
        else:
            bad["tables"]["Products"][0]["watts"] += 1
        assert send(bad).status_code == 422
    assert send({**changed, "timestamp": changed["timestamp"] + 1}).status_code == 409


def sender(environment, monkeypatch):
    """Configure the gateway for the isolated company; return (a valid full envelope, a signed `send`)."""
    company = environment["company"]
    secret = "synthetic-gas-key-" + "w" * 32
    monkeypatch.setenv("GOOGLE_COMPANY_ID", str(company))
    monkeypatch.setenv("GOOGLE_SHEET_ID", "fixture-workbook")
    monkeypatch.setenv("GOOGLE_CALLBACK_SECRET", secret)
    settings.cache_clear()
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as conn:
        rows = conn.execute("select * from luma.products where company_id=%s order by sku", (company,)).fetchall()
    fields = ("sku", "name", "family", "watts", "lumens", "cct", "ip_rating", "pack_size", "discontinued")
    envelope = dict(
        schema_version=1,
        company_id=str(company),
        spreadsheet_id="fixture-workbook",
        timestamp=int(time.time()) - 3,
        nonce=str(uuid4()),
        event="supplier_snapshot",
        tables=dict(
            Products=[{key: row[key] for key in fields} for row in rows],
            Prices=[
                dict(sku=row["sku"], currency="USD", unit_price=str(row["price"]), effective_from="2026-01-01")
                for row in rows
            ],
            Policies=[dict(key=key, value=value) for key, value in POLICIES.items()],
        ),
    )

    def send(value):
        """Sign a fixture envelope and submit it through the callback-only gateway."""
        body = json.dumps(value).encode()
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        with TestClient(app) as client:
            return client.post(
                "/callbacks/google/snapshot", content=body, headers={"X-Luma-Signature": signature}
            )

    return envelope, send


def sync_state(environment):
    """Return (snapshot id, digest, stored source table names) of the company's latest validated snapshot."""
    with psycopg.connect(environment["dsn"]) as conn:
        row = conn.execute(
            "select snapshot_id,digest,source_tables from luma.google_sync_state where company_id=%s",
            (environment["company"],),
        ).fetchone()
    return row[0], row[1], sorted(row[2])


def test_inventory_table_is_optional_ignored_and_outside_the_digest(environment, monkeypatch):
    """D49: a snapshot without Inventory is accepted; a sent Inventory (even junk) is ignored and never hashed.

    Editing the Inventory tab in the Sheet therefore produces the same snapshot id, the stored source
    tables never contain it, and no stock level or movement changes.
    """
    envelope, send = sender(environment, monkeypatch)
    with psycopg.connect(environment["dsn"]) as conn:
        before = conn.execute(
            "select count(*),coalesce(sum(delta),0) from luma.stock_movements where company_id=%s",
            (environment["company"],),
        ).fetchone()
    first = send(envelope)  # no Inventory key at all
    assert first.status_code == 202, first.json()
    assert first.json()["sync_status"] == "validated"
    sid, digest, tables = sync_state(environment)
    assert tables == ["Policies", "Prices", "Products"]
    second = {**envelope, "nonce": str(uuid4()), "timestamp": envelope["timestamp"] + 1}
    second["tables"] = {
        **envelope["tables"],
        "Inventory": [dict(sku="DL-001", available=17, location="Old warehouse")],  # old Apps Script shape
    }
    assert send(second).status_code == 202
    assert sync_state(environment) == (sid, digest, tables)
    third = {**envelope, "nonce": str(uuid4()), "timestamp": envelope["timestamp"] + 2}
    third["tables"] = {**envelope["tables"], "Inventory": [dict(sku="UNKNOWN", whatever="x"), {}]}  # junk is not read
    assert send(third).status_code == 202
    assert sync_state(environment) == (sid, digest, tables)
    fourth = {**envelope, "nonce": str(uuid4()), "timestamp": envelope["timestamp"] + 3}
    fourth["tables"] = {**envelope["tables"], "Inventory": None}
    assert send(fourth).status_code == 202
    assert sync_state(environment)[0] == sid
    fifth = {**envelope, "nonce": str(uuid4()), "timestamp": envelope["timestamp"] + 4}
    fifth["tables"] = {**envelope["tables"], "Inventory": [{}] * 1001}
    assert send(fifth).status_code == 422  # still bounded
    with psycopg.connect(environment["dsn"]) as conn:
        after = conn.execute(
            "select count(*),coalesce(sum(delta),0) from luma.stock_movements where company_id=%s",
            (environment["company"],),
        ).fetchone()
    assert after == before
    # A price edit still creates a new snapshot id, so Prices keep syncing.
    changed = {**envelope, "nonce": str(uuid4()), "timestamp": envelope["timestamp"] + 5}
    changed["tables"] = {**envelope["tables"], "Prices": [dict(p) for p in envelope["tables"]["Prices"]]}
    changed["tables"]["Prices"][0]["unit_price"] = "51.10"
    assert send(changed).status_code == 202
    assert sync_state(environment)[0] != sid
