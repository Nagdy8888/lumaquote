"""The one formula-injection guard of the stock exports (D49, T5), without a database.

Customer names, product names, suppliers and reasons are untrusted text. Excel and Google Sheets
evaluate a cell that starts with `=`, `+`, `-`, `@`, tab or carriage return, so `safe_text` must
turn each into plain text, and the Excel and Sheets builders must route every text cell through it.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from io import BytesIO

import pytest
from luma.features.inventory.exports import (
    COLUMNS,
    MAX_CELL_CHARS,
    ExportTable,
    build_workbook,
    export_filename,
    safe_text,
    sheet_payload,
    stock_status,
)
from openpyxl import load_workbook

CANARIES = ['=HYPERLINK("http://x","y")', "@SUM(1)", "+1", "-2+3", "\t=1", "\r=1+1", "=cmd|' /C calc'!A0"]


@pytest.mark.parametrize("value", CANARIES)
def test_every_formula_lead_gets_a_leading_apostrophe(value):
    """A string starting with a formula character is stored as text behind one apostrophe, unchanged otherwise."""
    assert safe_text(value) == "'" + value


@pytest.mark.parametrize("value", ["", "DL-001", "Downlight 18W", "a=b", "x+y", "name - suffix", " =padded", "'=already"])
def test_ordinary_text_is_untouched(value):
    """Text that does not start with a formula character is returned exactly."""
    assert safe_text(value) == value


def test_non_strings_stay_what_they_are():
    """Numbers, dates and None are returned unchanged so numeric cells remain numeric."""
    stamp = datetime(2026, 11, 8, tzinfo=UTC)
    for value in (0, -5, 7, 3.5, Decimal("-1.25"), True, None, stamp, date(2026, 11, 8)):
        assert safe_text(value) is value


def test_control_characters_are_removed_and_length_is_bounded():
    """NUL and other C0 characters (which a spreadsheet file cannot store) go; tab, newline and CR stay."""
    assert safe_text("a\x00b\x07c\x1fd") == "abcd"
    assert safe_text("line1\nline2") == "line1\nline2"
    assert safe_text("\x00=1") == "'=1"  # the guard looks at the cleaned text
    assert len(safe_text("x" * (MAX_CELL_CHARS + 500))) == MAX_CELL_CHARS
    assert len(safe_text("=" + "x" * (MAX_CELL_CHARS + 500))) == MAX_CELL_CHARS + 1


def tables():
    """Build one table per tab with canary text in every text column and typed numbers elsewhere."""
    stamp = datetime(2026, 11, 8, 13, 45, tzinfo=UTC)
    out = {}
    for name, columns in COLUMNS.items():
        row = []
        for index, (_, kind) in enumerate(columns):
            row.append(
                {
                    "text": CANARIES[index % len(CANARIES)],
                    "int": 7,
                    "money": Decimal("12.50"),
                    "datetime": stamp,
                    "date": date(2026, 12, 1),
                }[kind]
            )
        out[name] = ExportTable([h for h, _ in columns], [row, [None] * len(columns)], False)
    return out


def test_sheet_payload_guards_text_and_keeps_numbers_numeric():
    """Sheets rows hold guarded strings, ints, floats and UTC date text only; blanks are empty strings."""
    payload = sheet_payload(tables())
    stock = payload["Stock"]
    assert stock[0] == [h for h, _ in COLUMNS["Stock"]]
    assert stock[1][0] == "'" + CANARIES[0] and stock[1][3] == 7 and isinstance(stock[1][3], int)
    assert stock[2] == [""] * len(COLUMNS["Stock"])
    orders = payload["Customer Orders"][1]
    assert orders[2] == "2026-11-08 13:45" and orders[9] == 12.5 and isinstance(orders[9], float)
    assert payload["Purchase Orders"][1][3] == "2026-12-01"
    flat = [cell for rows in payload.values() for row in rows[1:] for cell in row if isinstance(cell, str)]
    assert all(not cell.startswith(("=", "+", "-", "@", "\t", "\r")) for cell in flat)


def test_workbook_cells_are_typed_and_text_is_never_a_formula():
    """The .xlsx has the four sheets, bold frozen headers, numeric numbers, datetimes and text canaries."""
    book = load_workbook(BytesIO(build_workbook(tables())))
    assert book.sheetnames == ["Stock", "Movements", "Customer Orders", "Purchase Orders"]
    for sheet in book:
        assert sheet.freeze_panes == "A2" and all(cell.font.bold for cell in sheet[1])
    stock = book["Stock"]
    assert stock["A2"].value == "'" + CANARIES[0] and stock["A2"].data_type == "s"
    assert stock["D2"].value == 7 and stock["D2"].data_type == "n"
    assert stock["A3"].value is None  # blank stays blank
    orders = book["Customer Orders"]
    assert orders["C2"].value == datetime(2026, 11, 8, 13, 45) and orders["C2"].number_format == "yyyy-mm-dd hh:mm"
    assert orders["J2"].value == 12.5 and orders["J2"].data_type == "n"
    for sheet in book:
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                assert cell.data_type != "f", f"{sheet.title}!{cell.coordinate} is a formula"


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"available": 0, "low": False}, "Out"),
        ({"available": -1, "low": True}, "Out"),
        ({"available": 5, "low": True}, "Low"),
        ({"available": 50, "low": False}, "OK"),
    ],
)
def test_stock_status(row, expected):
    """Out beats Low; Low follows the live flag; otherwise OK."""
    assert stock_status(row) == expected


def test_export_filename_uses_the_utc_day():
    """The download name carries the date as YYYYMMDD."""
    assert export_filename(datetime(2026, 11, 8, 23, 59, tzinfo=UTC)) == "lumaquote-stock-20261108.xlsx"
