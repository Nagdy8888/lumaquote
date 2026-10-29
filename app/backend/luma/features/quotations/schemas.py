from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field

from luma.core.contracts import StrictModel


class Selection(StrictModel):
    """A staff-selected product identity and bounded integral quantity; prices always come from the server."""

    product_id: UUID
    quantity: int = Field(ge=1, le=10000, strict=True)


class DraftInput(StrictModel):
    """Validated quotation-edit command with optimistic version, product selections, and bounded commercial adjustments."""

    expected_version: int = Field(ge=1)
    lines: list[Selection] = Field(min_length=1, max_length=40)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=10, max_digits=4, decimal_places=2)
    shipping: Decimal = Field(default=Decimal("0"), ge=0, le=10000, max_digits=9, decimal_places=2)
    terms: str = Field(default="Delivery date subject to staff confirmation.", max_length=1200)


class Decision(StrictModel):
    """Staff review command bound to the expected immutable quotation revision."""

    expected_revision: int = Field(ge=1)
    decision: Literal["approve", "reject"]
