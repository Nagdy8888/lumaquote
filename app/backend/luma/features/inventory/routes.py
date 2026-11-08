from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import Response

from luma.core.admission import rate_limit
from luma.core.audit import audit
from luma.core.database import database
from luma.core.http import OperationKey, Staff
from luma.core.idempotency import operation
from luma.core.identity import membership

from . import exports, service, sheet_queue
from .schemas import (
    AdjustmentInput,
    AlertAck,
    AlertsView,
    LevelView,
    MovementsPage,
    ReorderLevelInput,
    SheetExportView,
    StockView,
)

router = APIRouter()


@router.get("/api/inventory/stock", response_model=StockView)
def stock(user: Staff):
    """Read the company's stock table (on hand, reserved, available, reorder level, low flag) for any staff member."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:stock-read", 120)
        return service.stock_view(conn, member)


@router.get("/api/inventory/movements", response_model=MovementsPage)
def movements(
    user: Staff,
    product_id: UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    before: str | None = Query(None, max_length=80),
):
    """Read a newest-first page of stock movements, optionally for one product, using the `before` cursor."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:stock-read", 120)
        return service.movements(conn, member, product_id, limit, before)


@router.post("/api/inventory/adjustments", response_model=LevelView)
def adjustments(body: AdjustmentInput, user: Staff, key: OperationKey):
    """Idempotently apply an administrator's stock correction with a mandatory reason (403 for other roles)."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn,
            member,
            user,
            "stock-adjust",
            key,
            body.model_dump(mode="json"),
            lambda: service.adjust(conn, member, user, body),
        )


@router.post("/api/inventory/reorder-levels", response_model=LevelView)
def reorder_levels(body: ReorderLevelInput, user: Staff, key: OperationKey):
    """Idempotently set one product's low-stock threshold (administrators only)."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn,
            member,
            user,
            "stock-reorder-level",
            key,
            body.model_dump(mode="json"),
            lambda: service.set_reorder_level(conn, member, user, body),
        )


@router.get("/api/inventory/alerts", response_model=AlertsView)
def alerts(user: Staff):
    """Read open shortage and refused-acceptance alerts plus the live low-stock list for any staff member."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:stock-read", 120)
        return service.alerts(conn, member)


@router.post("/api/inventory/alerts/{alert_id}/acknowledge", response_model=AlertAck)
def acknowledge(alert_id: UUID, user: Staff, key: OperationKey):
    """Idempotently acknowledge one open alert (any staff role); an already acknowledged alert is a 409."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn,
            member,
            user,
            f"alert-ack:{alert_id}",
            key,
            {},
            lambda: service.acknowledge(conn, member, user, alert_id),
        )


XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/api/inventory/export.xlsx")
def export_xlsx(user: Staff):
    """Download the stock, movements, customer-order and purchase-order workbook (any staff member).

    Own admission bucket (10 per minute) because it reads thousands of rows. Read only apart from
    the audit event `inventory.exported`. Text cells are formula-guarded (`exports.safe_text`).
    """
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:stock-export", 10)
        tables = exports.collect(
            conn, member["company_id"], exports.XLSX_TABS, exports.XLSX_ROW_CAP, exports.MOVEMENT_ROWS
        )
        content = exports.build_workbook(tables)
        audit(
            conn,
            member["company_id"],
            user,
            "inventory.exported",
            None,
            format="xlsx",
            rows={name: len(table.rows) for name, table in tables.items()},
        )
    return Response(
        content,
        media_type=XLSX_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{exports.export_filename()}"'},
    )


@router.post("/api/inventory/sheet-exports", response_model=SheetExportView)
def queue_sheet_export(user: Staff, key: OperationKey):
    """Idempotently queue a Google Sheets stock export, or return the one already queued or running."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn, member, user, "stock-sheet-export", key, {}, lambda: sheet_queue.queue_export(conn, member, user)
        )


@router.get("/api/inventory/sheet-exports/latest", response_model=SheetExportView)
def latest_sheet_export(user: Staff):
    """Read the latest Sheets export's status, times, row counts and error code (status `none` if never requested)."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:stock-read", 120)
        return sheet_queue.latest_export(conn, member)
