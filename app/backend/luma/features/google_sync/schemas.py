"""Bounded supplier input contracts for the GAS-only transport."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Positive = Annotated[int, Field(strict=True, gt=0, le=1000000)]
Text = Annotated[str, Field(min_length=1, max_length=250)]


class InputRecord(BaseModel):
    """Reject unknown input columns rather than silently misinterpreting a changed Sheet schema."""

    model_config = ConfigDict(extra="forbid")


class ProductInput(InputRecord):
    """A SKU's descriptive fields must still match its independently ingested catalog evidence."""

    sku: Annotated[str, Field(pattern=r"^[A-Z0-9][A-Z0-9-]{1,39}$")]
    name: Text
    family: Text
    watts: Positive
    lumens: Positive
    cct: Positive
    ip_rating: Annotated[str, Field(pattern=r"^IP[0-6][0-9]$")]
    pack_size: Positive
    discontinued: Annotated[bool, Field(strict=True)]


class PriceInput(InputRecord):
    """USD decimal unit prices with an effective calendar date; no hidden rounding or future prices."""

    sku: Text
    currency: Literal["USD"]
    unit_price: Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2, allow_inf_nan=False)]
    effective_from: date


class InventoryInput(InputRecord):
    """Available stock at one named location, never a reservation or delivery promise."""

    sku: Text
    available: Annotated[int, Field(strict=True, ge=0, le=10000000)]
    location: Text


class PolicyInput(InputRecord):
    """Primitive policy cells are checked against the approved fixed commercial defaults."""

    key: Text
    value: str | int | bool


class SupplierTables(InputRecord):
    """Complete bounded tables; empty or partial snapshots cannot retire or overwrite existing records."""

    Products: Annotated[list[ProductInput], Field(min_length=1, max_length=1000)]
    Prices: Annotated[list[PriceInput], Field(min_length=1, max_length=1000)]
    Inventory: Annotated[list[InventoryInput], Field(min_length=1, max_length=1000)]
    Policies: Annotated[list[PolicyInput], Field(min_length=1, max_length=50)]


class SnapshotEnvelope(InputRecord):
    """Signed full-snapshot envelope with source observation time and replay identity."""

    schema_version: Literal[1]
    company_id: UUID
    spreadsheet_id: Text
    timestamp: Annotated[int, Field(strict=True)]
    nonce: UUID
    event: Literal["supplier_snapshot"]
    tables: SupplierTables
