"""Excel download and the signed Google Sheets stock export on real PostgreSQL (D49, task T5).

The Excel file is fetched through the real staff route and opened with openpyxl. The Sheets export
is driven through the real staff queue routes and the real callback gateway, with a Python stand-in
for Apps Script that signs envelopes exactly as `gas/Exports.gs` does. This proves the backend
protocol and the formula guard. It does NOT prove `gas/Stock.gs` runs inside Google or that the
tabs look right there; that needs the live step in docs/MORNING_ACTIONS.md. Label: local.
"""

import re
import time
from contextlib import contextmanager
from io import BytesIO
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from luma.core.config import settings
from luma.features.inventory import exports as stock_tables
from luma.features.inventory.ledger import seed_opening
from luma.google_gateway import app as gateway
from openpyxl import load_workbook
from psycopg.rows import dict_row
from test_drive_exports import SHEET, Poller
from test_stock_staff_routes import (
    DL1,
    as_salesperson,
    get,
    pending_order,
    po_body,
    post,
)


@pytest.fixture
def conn(environment):
    """Owner connection (bypasses row security) used to arrange and inspect; callers commit explicitly."""
    with psycopg.connect(environment["dsn"], row_factory=dict_row) as connection:
        yield connection


CANARY_NAME = '=HYPERLINK("http://x","y")'
CANARY_CUSTOMER = "@SUM(1)"
CANARY_SUPPLIER = "+1"
CANARY_REASON = "-2+3"
CANARY_COMPANY = "\t=1"
TABS = ["Stock", "Customer Orders", "Purchase Orders"]


def arrange(env, conn_):
    """Create a confirmed order, a purchase order and an adjustment whose text fields carry canaries."""
    cid, qid, oid = pending_order(env, conn_)
    assert post(env, f"/orders/{oid}/confirm", {}).status_code == 200
    created = post(env, "/purchase-orders", po_body(env, expected_on="2026-12-01"))
    assert created.status_code == 200, created.text
    conn_.execute("update luma.purchase_orders set supplier=%s where company_id=%s", (CANARY_SUPPLIER, env["company"]))
    conn_.execute(
        "update luma.orders set customer_name=%s,customer_company=%s where company_id=%s",
        (CANARY_CUSTOMER, CANARY_COMPANY, env["company"]),
    )
    conn_.execute("update luma.order_lines set name=%s where company_id=%s", (CANARY_NAME, env["company"]))
    conn_.execute(
        "update luma.products set name=%s where company_id=%s and id=%s",
        (CANARY_NAME, env["company"], env["products"][DL1]),
    )
    conn_.commit()
    adjusted = post(
        env,
        "/inventory/adjustments",
        {"product_id": str(env["products"][DL1]), "delta": 2, "reason": CANARY_REASON},
    )
    assert adjusted.status_code == 200, adjusted.text
    return oid


@contextmanager
def other_company(env):
    """Create a second tenant with stock, a movement and a purchase order; remove it afterwards."""
    company, source, snapshot, product = uuid4(), uuid4(), uuid4(), uuid4()
    with psycopg.connect(env["dsn"], row_factory=dict_row) as c:
        c.execute("insert into luma.companies(id,name) values(%s,'Other tenant')", (company,))
        c.execute(
            "insert into luma.sources(id,company_id,title,object_path) values(%s,%s,'Other',%s)",
            (source, company, f"{company}/catalogs/o.pdf"),
        )
        c.execute(
            "insert into luma.snapshots(id,company_id,source,observed_at,digest) values(%s,%s,'synthetic',now(),'x')",
            (snapshot, company),
        )
        c.execute(
            """insert into luma.products(id,company_id,sku,name,family,description,watts,lumens,cct,ip_rating,price,source_id,page,snapshot_id)
            values(%s,%s,'ZZ-OTHER-1','OTHER-TENANT-PRODUCT','Other family','x',18,1800,4000,'IP44',9.99,%s,1,%s)""",
            (product, company, source, snapshot),
        )
        seed_opening(c, company, product, 50, "test")
        po = uuid4()
        c.execute(
            "insert into luma.purchase_orders(id,company_id,number,supplier,created_by) values(%s,%s,'PO-0001','OTHER-TENANT-SUPPLIER',%s)",
            (po, company, env["user"]),
        )
        c.execute(
            "insert into luma.purchase_order_lines(company_id,purchase_order_id,product_id,quantity_ordered,unit_cost) values(%s,%s,%s,5,1)",
            (company, po, product),
        )
    try:
        yield company
    finally:
        with psycopg.connect(env["dsn"]) as c:
            for table in (
                "audit",
                "sheet_exports",
                "purchase_order_lines",
                "purchase_orders",
                "stock_movements",
                "stock_levels",
                "products",
                "sources",
                "snapshots",
            ):
                c.execute(f"delete from luma.{table} where company_id=%s", (company,))  # noqa: S608
            c.execute("delete from luma.companies where id=%s", (company,))


def workbook_of(response):
    """Open a downloaded workbook with openpyxl."""
    return load_workbook(BytesIO(response.content))


def all_text(book):
    """Return every string cell of a workbook."""
    return [c.value for sheet in book for row in sheet.iter_rows() for c in row if isinstance(c.value, str)]


# ----------------------------------------------------------------------------- Excel


def test_excel_download_has_four_typed_sheets_and_guarded_text(environment, conn):
    """Four sheets with bold frozen headers; numbers numeric, dates datetimes, canary text stored as text."""
    env = environment
    arrange(env, conn)
    response = get(env, "/inventory/export.xlsx")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == stock_tables_type()
    assert re.fullmatch(
        r'attachment; filename="lumaquote-stock-\d{8}\.xlsx"', response.headers["content-disposition"]
    )
    book = workbook_of(response)
    assert book.sheetnames == ["Stock", "Movements", "Customer Orders", "Purchase Orders"]
    for sheet in book:
        assert sheet.freeze_panes == "A2" and all(cell.font.bold for cell in sheet[1])
        assert [c.value for c in sheet[1]] == [h for h, _ in stock_tables.COLUMNS[sheet.title]]
    stock = {row[0].value: row for row in book["Stock"].iter_rows(min_row=2)}
    assert set(stock) == {"DL-001", "DL-002", "DL-011"}
    dl1 = stock["DL-001"]
    assert dl1[1].value == "'" + CANARY_NAME and dl1[1].data_type == "s"
    assert [c.value for c in dl1[3:8]] == [99, 0, 99, 20, "OK"]  # 100, the confirmed order took 3, the adjustment added 2
    assert all(isinstance(c.value, int) for c in dl1[3:7])
    assert stock["DL-011"][7].value == "Out"
    moves = list(book["Movements"].iter_rows(min_row=2))
    assert {m[2].value for m in moves} >= {"opening", "adjustment", "order"}
    adjustment = next(m for m in moves if m[2].value == "adjustment")
    assert adjustment[4].value == "'" + CANARY_REASON and adjustment[3].value == 2
    assert hasattr(adjustment[0].value, "year") and adjustment[0].number_format == "yyyy-mm-dd hh:mm"
    [order] = list(book["Customer Orders"].iter_rows(min_row=2))
    values = [c.value for c in order]
    assert values[0] == "SO-0001" and values[1] == "confirmed"
    assert hasattr(values[2], "year") and hasattr(values[3], "year")
    assert values[4] == "'" + CANARY_CUSTOMER and values[5] == "'" + CANARY_COMPANY
    assert values[6] == "DL-001" and values[7] == "'" + CANARY_NAME
    assert (values[8], values[9], values[10], values[11]) == (3, 32.35, 97.05, 97.05)
    assert all(order[i].data_type == "n" for i in (8, 9, 10, 11))
    purchase = list(book["Purchase Orders"].iter_rows(min_row=2))
    assert len(purchase) == 2
    assert purchase[0][0].value == "PO-0001" and purchase[0][2].value == "'" + CANARY_SUPPLIER
    assert hasattr(purchase[0][3].value, "year") and purchase[0][3].number_format == "yyyy-mm-dd"
    assert sorted((p[4].value, p[5].value, p[6].value, p[7].value) for p in purchase) == [
        ("DL-001", 10, 0, 5.5),
        ("DL-002", 4, 0, 6.0),
    ]
    for sheet in book:
        for row in sheet.iter_rows():
            for cell in row:
                assert cell.data_type != "f", f"{sheet.title}!{cell.coordinate} became a formula"
    conn.commit()
    [event] = conn.execute(
        "select detail from luma.audit where company_id=%s and action='inventory.exported'", (env["company"],)
    ).fetchall()
    assert event["detail"]["format"] == "xlsx" and event["detail"]["rows"]["Stock"] == 3


def stock_tables_type():
    """Return the OOXML spreadsheet media type the route must use."""
    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_salesperson_can_download_and_other_tenants_are_absent(environment, conn):
    """A salesperson may download; the workbook holds this company's rows only."""
    env = environment
    with other_company(env):
        as_salesperson(conn, env)
        response = get(env, "/inventory/export.xlsx")
        assert response.status_code == 200, response.text
        text = " ".join(all_text(workbook_of(response)))
        assert "DL-001" in text
        assert "OTHER-TENANT" not in text and "ZZ-OTHER" not in text


def test_download_needs_a_staff_token_and_has_its_own_rate_bucket(environment):
    """No token is 401/403; the export bucket (10 a minute) answers 429 without touching the read bucket."""
    env = environment
    assert env["api"].get("/api/inventory/export.xlsx").status_code in (401, 403)
    codes = [get(env, "/inventory/export.xlsx").status_code for _ in range(11)]
    assert codes[:10] == [200] * 10 and codes[10] == 429
    assert get(env, "/inventory/stock").status_code == 200


# ----------------------------------------------------------------------------- queue routes


def test_queue_dedupes_and_latest_reports_progress(environment, conn):
    """One open export per company: a second press returns the same row; an idempotent replay too."""
    env = environment
    none = get(env, "/inventory/sheet-exports/latest").json()
    assert none["status"] == "none" and none["id"] is None
    key = uuid4()
    first = post(env, "/inventory/sheet-exports", None, key)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["status"] == "queued" and body["completed_at"] is None and body["row_counts"] is None
    assert post(env, "/inventory/sheet-exports", None, key).json() == body
    again = post(env, "/inventory/sheet-exports", None)
    assert again.status_code == 200 and again.json()["id"] == body["id"]
    conn.commit()
    assert len(conn.execute("select 1 from luma.sheet_exports where company_id=%s", (env["company"],)).fetchall()) == 1
    assert get(env, "/inventory/sheet-exports/latest").json()["id"] == body["id"]
    queued = conn.execute(
        "select count(*) n from luma.audit where company_id=%s and action='inventory.sheet_export_queued'",
        (env["company"],),
    ).fetchone()
    assert queued["n"] == 1  # the deduped press wrote no second event
    conn.commit()
    as_salesperson(conn, env)  # any staff role may queue and read
    assert post(env, "/inventory/sheet-exports", None).json()["id"] == body["id"]
    assert get(env, "/inventory/sheet-exports/latest").status_code == 200


def test_a_new_export_can_be_queued_after_the_last_one_finished(environment, conn):
    """The one-open rule ends with the export: after `done` a new press creates a second row."""
    env = environment
    first = post(env, "/inventory/sheet-exports", None).json()
    conn.execute("update luma.sheet_exports set status='done',completed_at=now() where id=%s", (first["id"],))
    conn.commit()
    second = post(env, "/inventory/sheet-exports", None).json()
    assert second["id"] != first["id"] and second["status"] == "queued"
    assert get(env, "/inventory/sheet-exports/latest").json()["id"] == second["id"]


# ----------------------------------------------------------------------------- gateway protocol


class StockPoller(Poller):
    """Apps Script stand-in for the stock claim and receipt endpoints."""

    def claim(self, **kwargs):
        """Ask for the next stock export."""
        return self.send("/callbacks/google/stock/claim", "stock_export_claim", **kwargs)

    def receipt(self, claimed, outcome="stored", **overrides):
        """Report an outcome for a claimed export; stored reports the row counts the tabs held."""
        fields = {"export_id": claimed["export_id"], "claim_token": claimed["claim_token"], "outcome": outcome}
        if outcome == "stored":
            fields["row_counts"] = {name: len(rows) - 1 for name, rows in claimed.get("tabs", {}).items()}
        else:
            fields["error_code"] = "sheet_error"
        return self.send("/callbacks/google/stock/receipt", "stock_export_receipt", **{**fields, **overrides})


@pytest.fixture
def poller(environment, monkeypatch):
    """Configure the gateway for the isolated company and return the signing stand-in."""
    monkeypatch.setenv("GOOGLE_COMPANY_ID", str(environment["company"]))
    monkeypatch.setenv("GOOGLE_SHEET_ID", SHEET)
    monkeypatch.setenv("GOOGLE_CALLBACK_SECRET", "test-only-stock-key-" + "z" * 32)
    settings.cache_clear()
    return StockPoller(environment["company"], settings().google_callback_secret.get_secret_value())


def exports_of(env):
    """Read this tenant's stock export rows, oldest first."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as c:
        return c.execute(
            "select * from luma.sheet_exports where company_id=%s order by created_at", (env["company"],)
        ).fetchall()


def queue(env):
    """Queue an export through the real staff route; return its id."""
    response = post(env, "/inventory/sheet-exports", None)
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_idle_until_queued_then_claim_and_receipt_happy_path(environment, conn, poller):
    """Nothing queued is idle; a claim returns the three guarded tabs; the receipt completes the export."""
    env = environment
    arrange(env, conn)
    assert poller.claim().json() == {"status": "idle"}
    export_id = queue(env)
    response = poller.claim()
    assert response.status_code == 200, response.text
    claimed = response.json()
    assert claimed["status"] == "claimed" and claimed["export_id"] == export_id and claimed["truncated"] == []
    assert list(claimed["tabs"]) == TABS  # Movements and every other tab are never sent
    stock = claimed["tabs"]["Stock"]
    assert stock[0] == ["sku", "name", "family", "on_hand", "reserved", "available", "reorder_level", "status"]
    rows = {row[0]: row for row in stock[1:]}
    assert set(rows) == {"DL-001", "DL-002", "DL-011"}
    assert rows["DL-001"][1] == "'" + CANARY_NAME
    assert rows["DL-001"][3:7] == [99, 0, 99, 20] and all(isinstance(v, int) for v in rows["DL-001"][3:7])
    orders = claimed["tabs"]["Customer Orders"]
    assert len(orders) == 2 and orders[1][4] == "'" + CANARY_CUSTOMER and orders[1][5] == "'" + CANARY_COMPANY
    assert orders[1][9] == 32.35 and orders[1][8] == 3 and re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d", orders[1][2])
    pos = claimed["tabs"]["Purchase Orders"]
    assert len(pos) == 3 and pos[1][2] == "'" + CANARY_SUPPLIER and pos[1][3] == "2026-12-01"
    for tab in claimed["tabs"].values():
        for row in tab[1:]:
            for cell in row:
                assert not (isinstance(cell, str) and cell.startswith(("=", "+", "-", "@", "\t", "\r")))
    [row] = exports_of(env)
    assert (row["status"], row["attempts"], str(row["claim_token"])) == ("claimed", 1, claimed["claim_token"])
    assert poller.claim().json() == {"status": "idle"}  # leased, not available to a second poller
    done = poller.receipt(claimed)
    assert done.status_code == 200 and done.json() == {"status": "done"}
    [row] = exports_of(env)
    assert row["status"] == "done" and row["claim_token"] is None and row["completed_at"] is not None
    assert row["row_counts"] == {"Stock": 3, "Customer Orders": 1, "Purchase Orders": 2}
    latest = get(env, "/inventory/sheet-exports/latest").json()
    assert latest["status"] == "done" and latest["row_counts"] == row["row_counts"] and latest["error_code"] is None
    assert poller.claim().json() == {"status": "idle"}
    assert poller.receipt(claimed).json() == {"status": "done"}  # identical replay is idempotent
    assert poller.receipt(claimed, row_counts={"Stock": 1, "Customer Orders": 1, "Purchase Orders": 1}).status_code == 409
    conn.commit()
    events = conn.execute(
        "select action from luma.audit where company_id=%s and action like 'inventory.sheet_export%%'",
        (env["company"],),
    ).fetchall()
    assert sorted(e["action"] for e in events) == ["inventory.sheet_export_queued", "inventory.sheet_exported"]


def test_claim_carries_this_company_only(environment, poller):
    """Another tenant's stock, orders and purchase orders never appear in the signed claim."""
    env = environment
    with other_company(env):
        queue(env)
        claimed = poller.claim().json()
    text = repr(claimed["tabs"])
    assert "OTHER-TENANT" not in text and "ZZ-OTHER" not in text and "DL-001" in text


def test_rows_beyond_the_cap_are_cut_and_reported(environment, poller, monkeypatch):
    """A tab over the row cap sends the first rows and names the tab in `truncated`."""
    monkeypatch.setattr(stock_tables, "SHEET_ROW_CAP", 2)
    queue(environment)
    claimed = poller.claim().json()
    assert claimed["truncated"] == ["Stock"] and len(claimed["tabs"]["Stock"]) == 3


def test_forged_stale_cross_company_wrong_workbook_and_replayed_envelopes_are_rejected(environment, poller):
    """Signature, timestamp, company and workbook binding, schema and nonce rules apply to both endpoints."""
    queue(environment)
    assert poller.claim(valid=False).status_code == 401
    assert poller.claim(timestamp=int(time.time()) - 600).status_code == 401
    assert poller.claim(company_id=str(uuid4())).status_code == 403
    assert poller.claim(spreadsheet_id="another-workbook").status_code == 403
    assert poller.claim(schema_version=2).status_code == 422
    assert poller.claim(unexpected="field").status_code == 422
    assert poller.send("/callbacks/google/stock/claim", "drive_export_claim").status_code == 422  # wrong event
    assert poller.receipt({"export_id": str(uuid4()), "claim_token": str(uuid4()), "tabs": {}}, valid=False).status_code == 401
    envelope = {
        "schema_version": 1,
        "company_id": poller.company,
        "spreadsheet_id": SHEET,
        "timestamp": int(time.time()),
        "nonce": str(uuid4()),
        "event": "stock_export_claim",
    }
    first = poller.raw("/callbacks/google/stock/claim", envelope)
    assert first.status_code == 200 and first.json()["status"] == "claimed"
    assert poller.raw("/callbacks/google/stock/claim", envelope).status_code == 409
    with TestClient(gateway) as client:
        assert client.post("/callbacks/google/stock/claim", content=b"x" * 1025).status_code == 413
        assert client.post("/callbacks/google/stock/receipt", content=b"x" * 2049).status_code == 413


def test_receipt_needs_the_current_claim_token_and_valid_fields(environment, poller):
    """A stale token, unknown export, early receipt or malformed counts cannot complete an export."""
    env = environment
    queue(env)
    early = {"export_id": exports_of(env)[0]["id"], "claim_token": uuid4()}
    assert poller.receipt({k: str(v) for k, v in early.items()}, row_counts={t: 0 for t in TABS}).status_code == 409
    claimed = poller.claim().json()
    assert poller.receipt(claimed, claim_token=str(uuid4())).status_code == 409
    assert poller.receipt(claimed, export_id=str(uuid4())).status_code == 404
    assert poller.receipt(claimed, row_counts={"Stock": 1}).status_code == 422  # a tab is missing
    assert poller.receipt(claimed, row_counts={**{t: 0 for t in TABS}, "Products": 1}).status_code == 422
    assert poller.receipt(claimed, row_counts={**{t: 0 for t in TABS}, "Stock": 5001}).status_code == 422
    assert poller.receipt(claimed, row_counts={**{t: 0 for t in TABS}, "Stock": -1}).status_code == 422
    assert poller.receipt(claimed, outcome="failed", error_code="Has Spaces").status_code == 422
    assert poller.receipt(claimed, outcome="failed", error_code=None).status_code == 422
    assert poller.receipt(claimed, outcome="stored", row_counts=None).status_code == 422
    assert poller.receipt(claimed, extra="x").status_code == 422
    assert exports_of(env)[0]["status"] == "claimed"  # nothing above changed the row


def test_failures_retry_then_fail_and_expired_leases_are_reclaimed(environment, poller, conn):
    """Reported failures requeue up to five attempts, then fail; a silent client's lease expires and is reclaimed."""
    env = environment
    queue(env)
    for attempt in range(1, 5):
        claimed = poller.claim().json()
        assert poller.receipt(claimed, "failed").json() == {"status": "queued"}
        [row] = exports_of(env)
        assert (row["status"], row["attempts"], row["error_code"]) == ("queued", attempt, "sheet_error")
        assert get(env, "/inventory/sheet-exports/latest").json()["error_code"] == "sheet_error"
    claimed = poller.claim().json()
    assert poller.receipt(claimed, "failed").json() == {"status": "failed"}
    [row] = exports_of(env)
    assert (row["status"], row["attempts"], row["completed_at"] is not None) == ("failed", 5, True)
    assert poller.claim().json() == {"status": "idle"}
    again = post(env, "/inventory/sheet-exports", None).json()  # a failed export no longer blocks a new press
    assert again["status"] == "queued"
    # A silent client: the lease expires, the next poll reclaims with a fresh token.
    first = poller.claim().json()
    conn.execute(
        "update luma.sheet_exports set lease_until=now()-interval '1 minute' where id=%s", (first["export_id"],)
    )
    conn.commit()
    second = poller.claim().json()
    assert second["status"] == "claimed" and second["claim_token"] != first["claim_token"]
    assert poller.receipt(first).status_code == 409  # the first holder's token is stale now
    assert exports_of(env)[-1]["attempts"] == 2
    # Attempts used up: an expired lease at the limit becomes failed instead of being leased again.
    conn.execute(
        "update luma.sheet_exports set lease_until=now()-interval '1 minute',attempts=5 where id=%s",
        (second["export_id"],),
    )
    conn.commit()
    assert poller.claim().json() == {"status": "idle"}
    last = exports_of(env)[-1]
    assert (last["status"], last["error_code"], last["claim_token"]) == ("failed", "attempts_exhausted", None)


def test_concurrent_pollers_cannot_claim_the_same_export(environment, poller):
    """Several simultaneous claims for one queued export yield exactly one lease and one attempt."""
    from concurrent.futures import ThreadPoolExecutor

    env = environment
    queue(env)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: poller.claim().json(), range(6)))
    leased = [r for r in results if r["status"] == "claimed"]
    assert len(leased) == 1 and sum(r["status"] == "idle" for r in results) == 5
    [row] = exports_of(env)
    assert (row["status"], row["attempts"]) == ("claimed", 1)
