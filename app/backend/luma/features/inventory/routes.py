from uuid import UUID

from fastapi import APIRouter, Query

from luma.core.admission import rate_limit
from luma.core.database import database
from luma.core.http import OperationKey, Staff
from luma.core.idempotency import operation
from luma.core.identity import membership

from . import service
from .schemas import (
    AdjustmentInput,
    AlertAck,
    AlertsView,
    LevelView,
    MovementsPage,
    ReorderLevelInput,
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
