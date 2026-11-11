"""Request and response contracts of the supplier purchase-order routes (decision D49).

Bounds follow the plan: quantities 1..100000, unit cost 0..1,000,000 with two decimals, supplier 1-120
characters, notes at most 500, at most 100 lines per order and one line per product.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints, field_validator

from luma.core.contracts import ResponseModel, StrictModel

Quantity = Annotated[int, Field(ge=1, le=100000, strict=True)]
Supplier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


def _distinct(lines: list) -> list:
    """Reject a command that names the same product twice; return the lines unchanged otherwise."""
    ids = [line.product_id for line in lines]
    if len(set(ids)) != len(ids):
        raise ValueError("Each product may appear only once.")
    return lines


class PurchaseLineInput(StrictModel):
    """One ordered product: how many and what each unit costs (informational; cost does not value stock)."""

    product_id: UUID
    quantity: Quantity
    unit_cost: Decimal = Field(ge=0, le=1000000, max_digits=9, decimal_places=2)


class PurchaseOrderInput(StrictModel):
    """Admin command to record a supplier purchase order (status `ordered`)."""

    supplier: Supplier
    expected_on: date | None = None
    notes: Notes | None = None
    lines: list[PurchaseLineInput] = Field(min_length=1, max_length=100)

    @field_validator("lines")
    @classmethod
    def distinct_products(cls, lines: list[PurchaseLineInput]) -> list[PurchaseLineInput]:
        """Require distinct product ids across the lines."""
        return _distinct(lines)


class ReceiveLineInput(StrictModel):
    """Goods that arrived for one product of the purchase order in this delivery."""

    product_id: UUID
    quantity: Quantity


class ReceiveInput(StrictModel):
    """Admin command to receive part or all of a purchase order; each line adds to `quantity_received`."""

    lines: list[ReceiveLineInput] = Field(min_length=1, max_length=100)

    @field_validator("lines")
    @classmethod
    def distinct_products(cls, lines: list[ReceiveLineInput]) -> list[ReceiveLineInput]:
        """Require distinct product ids across the lines."""
        return _distinct(lines)


class PurchaseLineRow(ResponseModel):
    """A purchase-order line with ordered and received quantities."""

    product_id: UUID
    sku: str
    name: str
    quantity_ordered: int
    quantity_received: int
    unit_cost: Decimal


class PurchaseOrderRow(ResponseModel):
    """A purchase order with its lines; status moves ordered -> partially_received -> received, or ordered -> cancelled."""

    id: UUID
    number: str
    supplier: str
    status: Literal["ordered", "partially_received", "received", "cancelled"]
    expected_on: date | None
    notes: str | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseLineRow]


class PurchaseOrdersView(ResponseModel):
    """Purchase orders newest first (at most 200), each with its lines."""

    items: list[PurchaseOrderRow]
