"""Request and response contracts of the stock, adjustment and alert routes (decision D49).

Requests reject undeclared fields and use strict integers with the bounds of the plan. Responses
are the shapes the staff web app reads; quantities are integers and dates are ISO timestamps.
"""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints, field_validator

from luma.core.contracts import ResponseModel, StrictModel

Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]


class AdjustmentInput(StrictModel):
    """Admin command to correct one product's on-hand stock by a signed, non-zero amount with a reason."""

    product_id: UUID
    delta: int = Field(ge=-100000, le=100000, strict=True)
    reason: Reason

    @field_validator("delta")
    @classmethod
    def non_zero(cls, value: int) -> int:
        """Reject a zero adjustment, which would append a movement that changes nothing."""
        if value == 0:
            raise ValueError("The adjustment must change the quantity.")
        return value


class ReorderLevelInput(StrictModel):
    """Admin command to set the low-stock threshold of one product (0..100000)."""

    product_id: UUID
    reorder_level: int = Field(ge=0, le=100000, strict=True)


class StockRow(ResponseModel):
    """One product's stock position: available is on_hand minus reserved, `low` means at or below its reorder level."""

    product_id: UUID
    sku: str
    name: str
    family: str
    discontinued: bool
    on_hand: int
    reserved: int
    available: int
    reorder_level: int
    low: bool


class StockView(ResponseModel):
    """The stock table plus how many products are low."""

    items: list[StockRow]
    low_count: int


class LevelView(ResponseModel):
    """A product's ledger position after an adjustment or a reorder-level change."""

    product_id: UUID
    on_hand: int
    reserved: int
    available: int
    reorder_level: int


class MovementRow(ResponseModel):
    """One append-only stock movement with its product identity and optional reference (order or purchase order)."""

    id: UUID
    product_id: UUID
    sku: str
    name: str
    delta: int
    kind: Literal["opening", "adjustment", "receipt", "order", "order_cancel"]
    reference_id: UUID | None
    reference: str | None  # PO number for a receipt, SO number for an order movement; null otherwise
    reason: str | None
    actor: str
    created_at: datetime


class MovementsPage(ResponseModel):
    """A newest-first page of movements; `next` is the opaque `before` cursor of the following page, or null."""

    items: list[MovementRow]
    next: str | None


class AlertRow(ResponseModel):
    """A stored alert (shortage or refused acceptance) with the product and conversation it names."""

    id: UUID
    kind: Literal["shortage", "acceptance_refused"]
    status: Literal["open", "acknowledged"]
    product_id: UUID | None
    sku: str | None
    name: str | None
    conversation_id: UUID | None
    quote_id: UUID | None
    requested: int | None
    available: int | None
    created_at: datetime


class AlertCounts(ResponseModel):
    """Open alert totals for the navigation badge: stored alerts by kind, live low-stock products, and their sum."""

    shortage: int
    acceptance_refused: int
    low_stock: int
    total: int


class AlertsView(ResponseModel):
    """Open stored alerts, the live low-stock list and the counts."""

    alerts: list[AlertRow]
    low_stock: list[StockRow]
    counts: AlertCounts


class AlertAck(ResponseModel):
    """Result of acknowledging an alert."""

    id: UUID
    status: Literal["acknowledged"]


class SheetExportView(ResponseModel):
    """Progress of the Google Sheets stock export: `none` before the first request, then queued,
    claimed (Apps Script is writing), done (with row counts per tab) or failed (with a short error code)."""

    id: UUID | None
    status: Literal["none", "queued", "claimed", "done", "failed"]
    requested_at: datetime | None
    completed_at: datetime | None
    row_counts: dict[str, int] | None
    error_code: str | None
