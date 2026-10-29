"""Bounded lookup inputs and descriptive evidence; commercial authority stays in quotation rules."""

from uuid import UUID

from pydantic import Field, StrictInt

from luma.core.contracts import StrictModel


class CatalogSearch(StrictModel):
    """A staff/agent search with optional explicit specification constraints; similarity never proves equivalence."""

    query: str = Field(min_length=1, max_length=500)
    watts: StrictInt | None = Field(default=None, ge=1, le=2000)
    cct: StrictInt | None = Field(default=None, ge=1000, le=12000)
    ip_rating: str | None = Field(default=None, pattern=r"^IP[0-6][0-9]$")


class CatalogHit(StrictModel):
    """One current tenant-scoped descriptive record with original-page and source-version provenance, without prices."""

    product_id: UUID
    sku: str = Field(pattern=r"^[A-Z]{2}-\d{3}$")
    name: str
    description: str
    watts: int
    cct: int
    ip_rating: str = Field(pattern=r"^IP[0-6][0-9]$")
    source_id: UUID
    source_title: str
    source_version: int = Field(ge=1)
    page: int = Field(ge=1)
