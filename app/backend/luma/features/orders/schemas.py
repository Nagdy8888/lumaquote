"""Request and response contracts of the staff order routes (decision D49)."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import StringConstraints

from luma.core.contracts import ResponseModel, StrictModel

CancelReason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]


class CancelInput(StrictModel):
    """Staff command to cancel an order; the reason (3-200 characters) is stored and audited."""

    reason: CancelReason


class OrderLineRow(ResponseModel):
    """One order line copied from the accepted quotation: prices are the quoted ones, never recomputed."""

    product_id: UUID
    sku: str
    name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class OrderRow(ResponseModel):
    """A customer order with its lines and lifecycle stamps (pending, confirmed or cancelled)."""

    id: UUID
    number: str
    conversation_id: UUID
    quote_id: UUID
    revision: int
    status: Literal["pending", "confirmed", "cancelled"]
    accepted_via: Literal["telegram_button", "reply", "staff"]
    accepted_at: datetime
    confirmed_at: datetime | None
    cancelled_at: datetime | None
    cancel_reason: str | None
    currency: str
    total: Decimal
    customer_name: str
    customer_company: str
    created_at: datetime
    lines: list[OrderLineRow]


class OrdersView(ResponseModel):
    """Orders newest first (at most 200), pending ones included, each with its lines."""

    items: list[OrderRow]
