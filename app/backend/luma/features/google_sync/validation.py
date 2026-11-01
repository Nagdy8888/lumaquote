"""Deterministic whole-snapshot validation before any commercial writes."""

from datetime import datetime
from zoneinfo import ZoneInfo

from luma.core.errors import DomainError

from .schemas import SnapshotEnvelope

POLICIES = {
    "dataset": "Synthetic supplier records for portfolio testing",
    "currency": "USD",
    "tax": "excluded",
    "quote_valid_days": 7,
    "max_admin_discount_percent": 10,
    "stock_reserved": False,
    "delivery": "Staff confirmation required",
}


def unique_records(records, key):
    """Index records by stable identity, rejecting duplicate rows instead of choosing an arbitrary winner."""
    indexed = {getattr(row, key): row for row in records}
    if len(indexed) != len(records):
        raise DomainError("Duplicate supplier record identity.", 422)
    return indexed


def validate_tables(envelope: SnapshotEnvelope):
    """Require matching SKU sets, effective prices and unchanged approved policies; return indexed records."""
    tables = envelope.tables
    products = unique_records(tables.Products, "sku")
    prices = unique_records(tables.Prices, "sku")
    inventory = unique_records(tables.Inventory, "sku")
    if products.keys() != prices.keys() or products.keys() != inventory.keys():
        raise DomainError("Products, Prices and Inventory must contain the same complete SKU set.", 422)
    policies = unique_records(tables.Policies, "key")
    actual = {key: row.value for key, row in policies.items()}
    if actual.keys() != POLICIES.keys() or any(
        type(actual[key]) is not type(value) or actual[key] != value for key, value in POLICIES.items()
    ):
        raise DomainError("Supplier policies do not match the approved commercial defaults.", 422)
    today = datetime.now(ZoneInfo("Africa/Cairo")).date()
    if any(price.effective_from > today for price in prices.values()):
        raise DomainError("Future supplier prices cannot become current.", 422)
    return products, prices, inventory
