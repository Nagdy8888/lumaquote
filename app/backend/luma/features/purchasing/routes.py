from uuid import UUID

from fastapi import APIRouter

from luma.core.admission import rate_limit
from luma.core.database import database
from luma.core.http import OperationKey, Staff
from luma.core.idempotency import operation
from luma.core.identity import membership

from . import service
from .schemas import PurchaseOrderInput, PurchaseOrderRow, PurchaseOrdersView, ReceiveInput

router = APIRouter()


@router.get("/api/purchase-orders", response_model=PurchaseOrdersView)
def purchase_orders(user: Staff):
    """Read the company's purchase orders with their lines, newest first, for any staff member."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:stock-read", 120)
        return service.list_orders(conn, member)


@router.post("/api/purchase-orders", response_model=PurchaseOrderRow)
def create(body: PurchaseOrderInput, user: Staff, key: OperationKey):
    """Idempotently record a supplier purchase order in status `ordered` (administrators only)."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn,
            member,
            user,
            "purchase-order-create",
            key,
            body.model_dump(mode="json"),
            lambda: service.create(conn, member, user, body),
        )


@router.post("/api/purchase-orders/{order_id}/receive", response_model=PurchaseOrderRow)
def receive(order_id: UUID, body: ReceiveInput, user: Staff, key: OperationKey):
    """Idempotently receive goods against a purchase order, raising stock (administrators only)."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn,
            member,
            user,
            f"purchase-order-receive:{order_id}",
            key,
            body.model_dump(mode="json"),
            lambda: service.receive(conn, member, user, order_id, body),
        )


@router.post("/api/purchase-orders/{order_id}/cancel", response_model=PurchaseOrderRow)
def cancel(order_id: UUID, user: Staff, key: OperationKey):
    """Idempotently cancel a purchase order that has received nothing (administrators only)."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:mutation", 30)
        return operation(
            conn,
            member,
            user,
            f"purchase-order-cancel:{order_id}",
            key,
            {},
            lambda: service.cancel(conn, member, user, order_id),
        )
