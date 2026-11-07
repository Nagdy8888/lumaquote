from uuid import UUID

from fastapi import APIRouter, Query

from luma.core.admission import rate_limit
from luma.core.database import database
from luma.core.http import OperationKey, Staff
from luma.core.idempotency import operation
from luma.core.identity import membership

from . import management
from .schemas import CancelInput, OrderRow, OrdersView

router = APIRouter()


@router.get("/api/orders", response_model=OrdersView)
def orders(user: Staff, status: str | None = Query(None, max_length=20)):
    """Read the company's customer orders with their lines, newest first, optionally filtered by status."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:stock-read", 120)
        return management.list_orders(conn, member, status)


@router.post("/api/orders/{order_id}/confirm", response_model=OrderRow)
def confirm(order_id: UUID, user: Staff, key: OperationKey):
    """Idempotently confirm a pending order so its reserved stock leaves on-hand (any staff role)."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn,
            member,
            user,
            f"order-confirm:{order_id}",
            key,
            {},
            lambda: management.confirm(conn, member, user, order_id),
        )


@router.post("/api/orders/{order_id}/cancel", response_model=OrderRow)
def cancel(order_id: UUID, body: CancelInput, user: Staff, key: OperationKey):
    """Idempotently cancel a pending or confirmed order with a reason; its stock is released or returned."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn,
            member,
            user,
            f"order-cancel:{order_id}",
            key,
            body.model_dump(),
            lambda: management.cancel(conn, member, user, order_id, body.reason),
        )
