"""Stock exports: the Excel workbook and the Google Sheets tab rows (decision D49, task T5).

Authority: read only. Callers pass an open connection already scoped to one company (the staff
download route uses the staff connection; the signed Apps Script gateway uses the worker
connection after verifying its envelope). Nothing here writes, queues or sends anything.

One definition of the tables feeds both outputs, so the Excel file and the Sheets tabs cannot
drift apart. Every text cell passes through `safe_text`, the single formula-injection guard:
customer names, product names, suppliers and reasons come from chats, Gmail and staff typing
and are untrusted when a spreadsheet opens them.
"""

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from . import queries

MAX_CELL_CHARS = 30000
"""Longest text kept in one cell; Excel stops at 32767, and the guard may add one character."""
MOVEMENT_ROWS = 5000
"""Newest stock movements in the workbook."""
XLSX_ROW_CAP = 20000
"""Safety bound on rows per workbook sheet so a very large history cannot exhaust memory."""
SHEET_ROW_CAP = 5000
"""Data rows per Google Sheets tab; a tab beyond it is truncated and reported."""
SHEET_TABS = ("Stock", "Customer Orders", "Purchase Orders")
"""The tabs Apps Script may write; Products, Prices, Policies and Quote Register are never touched."""
XLSX_TABS = ("Stock", "Movements", "Customer Orders", "Purchase Orders")

# Column definitions: (header, kind). Kinds: text, int, money, datetime, date.
COLUMNS: dict[str, tuple[tuple[str, str], ...]] = {
    "Stock": (
        ("sku", "text"),
        ("name", "text"),
        ("family", "text"),
        ("on_hand", "int"),
        ("reserved", "int"),
        ("available", "int"),
        ("reorder_level", "int"),
        ("status", "text"),
    ),
    "Movements": (
        ("date_utc", "datetime"),
        ("sku", "text"),
        ("kind", "text"),
        ("delta", "int"),
        ("reason", "text"),
        ("reference", "text"),
    ),
    "Customer Orders": (
        ("order_number", "text"),
        ("status", "text"),
        ("accepted_at", "datetime"),
        ("confirmed_at", "datetime"),
        ("customer_name", "text"),
        ("customer_company", "text"),
        ("sku", "text"),
        ("name", "text"),
        ("quantity", "int"),
        ("unit_price", "money"),
        ("line_total", "money"),
        ("order_total", "money"),
    ),
    "Purchase Orders": (
        ("po_number", "text"),
        ("status", "text"),
        ("supplier", "text"),
        ("expected_on", "date"),
        ("sku", "text"),
        ("quantity_ordered", "int"),
        ("quantity_received", "int"),
        ("unit_cost", "money"),
    ),
}

_FORMULA_LEADS = ("=", "+", "-", "@", "\t", "\r")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def safe_text(value):
    """Neutralize spreadsheet formula injection in one cell value; the only such guard in the app.

    Inputs: any value. A non-string (number, date, None) is returned unchanged, so numbers stay
    numeric. A string loses control characters that spreadsheet files cannot hold (NUL and most of
    the C0 range, but not tab, line feed or carriage return), is cut to `MAX_CELL_CHARS`, and gets
    a leading apostrophe when it starts with `=`, `+`, `-`, `@`, tab or carriage return, so Excel
    and Google Sheets show it as text instead of evaluating it. The apostrophe stays visible in
    the cell; that is the accepted cost of a guard that cannot be bypassed by the reader.
    Side effects and errors: none.
    """
    if not isinstance(value, str):
        return value
    text = _CONTROL_CHARS.sub("", value)[:MAX_CELL_CHARS]
    return "'" + text if text.startswith(_FORMULA_LEADS) else text


@dataclass
class ExportTable:
    """One exported table: header names, data rows of raw values (str, int, Decimal, date, datetime,
    None) in the order of `COLUMNS`, and whether older rows were cut by the row cap."""

    headers: list[str]
    rows: list[list]
    truncated: bool


def stock_status(row) -> str:
    """Name a product's stock state: Out when nothing is available, Low at or below its reorder level, else OK."""
    if row["available"] <= 0:
        return "Out"
    return "Low" if row["low"] else "OK"


def _stock_rows(conn, company, cap: int) -> list[list]:
    """Return the stock table as export rows (family then SKU order), cut to `cap`+1 rows by the caller."""
    return [
        [
            row["sku"],
            row["name"],
            row["family"],
            row["on_hand"],
            row["reserved"],
            row["available"],
            row["reorder_level"],
            stock_status(row),
        ]
        for row in queries.stock_rows(conn, company)[: cap + 1]
    ]


def _movement_rows(conn, company, cap: int) -> list[list]:
    """Return the newest `cap`+1 stock movements, newest first, with SKU and the reference id as text."""
    rows = conn.execute(
        """select m.created_at,p.sku,m.kind,m.delta,m.reason,m.reference_id
        from luma.stock_movements m join luma.products p on p.company_id=m.company_id and p.id=m.product_id
        where m.company_id=%s order by m.created_at desc,m.id desc limit %s""",
        (company, cap + 1),
    ).fetchall()
    return [
        [r["created_at"], r["sku"], r["kind"], r["delta"], r["reason"], str(r["reference_id"] or "")]
        for r in rows
    ]


def _order_rows(conn, company, cap: int) -> list[list]:
    """Return customer order lines (one row per line, newest order first), at most `cap`+1 rows."""
    rows = conn.execute(
        """select o.number,o.status,o.accepted_at,o.confirmed_at,o.customer_name,o.customer_company,
        l.sku,l.name,l.quantity,l.unit_price,l.line_total,o.total
        from luma.orders o join luma.order_lines l on l.company_id=o.company_id and l.order_id=o.id
        where o.company_id=%s order by o.accepted_at desc,o.number desc,l.sku limit %s""",
        (company, cap + 1),
    ).fetchall()
    return [
        [
            r["number"],
            r["status"],
            r["accepted_at"],
            r["confirmed_at"],
            r["customer_name"],
            r["customer_company"],
            r["sku"],
            r["name"],
            r["quantity"],
            r["unit_price"],
            r["line_total"],
            r["total"],
        ]
        for r in rows
    ]


def _purchase_rows(conn, company, cap: int) -> list[list]:
    """Return supplier purchase order lines (one row per line, newest order first), at most `cap`+1 rows."""
    rows = conn.execute(
        """select po.number,po.status,po.supplier,po.expected_on,p.sku,
        l.quantity_ordered,l.quantity_received,l.unit_cost
        from luma.purchase_orders po
        join luma.purchase_order_lines l on l.company_id=po.company_id and l.purchase_order_id=po.id
        join luma.products p on p.company_id=l.company_id and p.id=l.product_id
        where po.company_id=%s order by po.created_at desc,po.number desc,p.sku limit %s""",
        (company, cap + 1),
    ).fetchall()
    return [
        [
            r["number"],
            r["status"],
            r["supplier"],
            r["expected_on"],
            r["sku"],
            r["quantity_ordered"],
            r["quantity_received"],
            r["unit_cost"],
        ]
        for r in rows
    ]


_LOADERS = {
    "Stock": _stock_rows,
    "Movements": _movement_rows,
    "Customer Orders": _order_rows,
    "Purchase Orders": _purchase_rows,
}


def collect(conn, company, tabs, row_cap: int, movement_cap: int | None = None) -> dict[str, ExportTable]:
    """Read the named tabs for one company (read only) and return raw values per tab.

    `tabs` are keys of `COLUMNS`; `row_cap` bounds data rows per tab (Movements uses `movement_cap`
    when given). One extra row is fetched to learn whether the tab was truncated, then dropped.
    Every query filters by `company`, so another tenant's rows cannot appear.
    """
    tables = {}
    for name in tabs:
        cap = movement_cap if name == "Movements" and movement_cap else row_cap
        rows = _LOADERS[name](conn, company, cap)
        tables[name] = ExportTable([h for h, _ in COLUMNS[name]], rows[:cap], len(rows) > cap)
    return tables


def _utc_naive(value: datetime) -> datetime:
    """Convert a timestamp to naive UTC, the only form Excel can store (it has no time zones)."""
    return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value


def build_workbook(tables: dict[str, ExportTable]) -> bytes:
    """Render tables as an .xlsx file and return its bytes (no file or network is touched).

    One sheet per table in the given order. The header row is bold and frozen; widths follow
    the content; numbers are numeric cells; date-times are UTC date-time cells; text cells are
    guarded by `safe_text` and written with an explicit string type so a value can never become
    a formula. Empty values stay empty cells.
    """
    book = Workbook()
    book.remove(book.active)
    for name, table in tables.items():
        sheet = book.create_sheet(name)
        kinds = [kind for _, kind in COLUMNS[name]]
        sheet.append(table.headers)
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        sheet.freeze_panes = "A2"
        widths = [len(h) for h in table.headers]
        for row in table.rows:
            out = []
            for index, (value, kind) in enumerate(zip(row, kinds, strict=True)):
                if kind == "datetime" and isinstance(value, datetime):
                    value = _utc_naive(value)
                if kind == "text":
                    value = safe_text(value)
                out.append(value)
                if value is not None:
                    widths[index] = max(widths[index], min(len(str(value)), 60))
            sheet.append(out)
        for row_cells in sheet.iter_rows(min_row=2):
            for cell, kind in zip(row_cells, kinds, strict=True):
                if kind == "text" and isinstance(cell.value, str):
                    cell.data_type = "s"
                elif kind == "datetime":
                    cell.number_format = "yyyy-mm-dd hh:mm"
                elif kind == "date":
                    cell.number_format = "yyyy-mm-dd"
                elif kind == "money":
                    cell.number_format = "#,##0.00"
        for index, width in enumerate(widths, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = min(max(width + 2, 8), 62)
    buffer = BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def export_filename(now: datetime | None = None) -> str:
    """Return the download name `lumaquote-stock-YYYYMMDD.xlsx` for the given (default current) UTC day."""
    return f"lumaquote-stock-{(now or datetime.now(UTC)):%Y%m%d}.xlsx"


def _sheet_cell(value, kind: str):
    """Convert one raw value to a JSON cell for Apps Script: guarded text, numbers, or UTC text dates.

    Text passes through `safe_text`; ints stay ints; money becomes a float; date-times and dates
    become `YYYY-MM-DD HH:MM` (UTC) and `YYYY-MM-DD` text; missing values become an empty string
    (JSON has no spreadsheet blank, and an empty string clears the cell).
    """
    if value is None:
        return ""
    if kind == "text":
        return safe_text(str(value))
    if kind == "int":
        return int(value)
    if kind == "money":
        return float(Decimal(value))
    if kind == "datetime":
        return _utc_naive(value).strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.isoformat()
    return safe_text(str(value))


def sheet_payload(tables: dict[str, ExportTable]) -> dict[str, list[list]]:
    """Return `{tab: [header_row, *data_rows]}` for the Sheets export, every text cell guarded.

    Pure and side-effect free; the result is JSON-serializable and holds only strings, ints and
    floats, so Apps Script can write it without interpreting any value.
    """
    payload = {}
    for name, table in tables.items():
        kinds = [kind for _, kind in COLUMNS[name]]
        payload[name] = [table.headers] + [
            [_sheet_cell(value, kind) for value, kind in zip(row, kinds, strict=True)] for row in table.rows
        ]
    return payload
