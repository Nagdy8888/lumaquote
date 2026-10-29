"""Independent arithmetic and commercial-authorization regression tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st
from luma.core.errors import DomainError
from luma.features.quotations.rules import assert_dispatchable, calculate


def product(price="32.35", quantity=3, **overrides):
    """Build a bounded product line with independent fixture commercial values."""
    return {
        "product_id": uuid4(),
        "sku": "DL-002",
        "name": "Synthetic downlight",
        "quantity": quantity,
        "price": Decimal(price),
        "available": 10000,
        "pack_size": 1,
        "discontinued": False,
        "source_id": uuid4(),
        "page": 1,
        **overrides,
    }


def test_independently_calculated_discount_and_shipping():
    """Three 32.35 items minus 7.5% rounded half-up plus 12.99 shipping must total 102.76 USD."""
    result = calculate([product()], Decimal("7.5"), Decimal("12.99"), "admin")
    assert result["subtotal"] == "97.05"
    assert result["discount"] == "7.28"
    assert result["total"] == "102.76"
    assert result["tax"] == "Excluded"
    assert result["stock_reserved"] is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"quantity": 0},
        {"quantity": -1},
        {"quantity": 2.5},
        {"quantity": True},
        {"quantity": 4, "available": 3},
        {"quantity": 3, "pack_size": 2},
        {"discontinued": True},
        {"price": Decimal("NaN")},
        {"price": Decimal("-1")},
    ],
)
def test_invalid_commercial_input_cannot_be_quoted(overrides):
    """Invalid quantities, availability, packs, and prices reject before a draft can become authoritative."""
    with pytest.raises(DomainError):
        calculate([product(**overrides)], Decimal(0), Decimal(0), "admin")


def test_salesperson_cannot_grant_discount():
    """A non-admin cannot authorize even a small nonzero discount."""
    with pytest.raises(DomainError) as error:
        calculate([product()], Decimal("0.01"), Decimal(0), "salesperson")
    assert error.value.status == 403


@given(st.integers(min_value=0, max_value=100000), st.integers(min_value=1, max_value=1000))
def test_integral_minor_unit_totals_remain_exact(cents, quantity):
    """No-discount totals equal independent integer-minor-unit arithmetic over many valid inputs."""
    result = calculate(
        [product(price=str(Decimal(cents) / 100), quantity=quantity)], Decimal(0), Decimal(0), "salesperson"
    )
    assert Decimal(result["total"]) * 100 == cents * quantity


@pytest.mark.parametrize("change", ["expired", "hash", "recipient", "takeover", "unapproved"])
def test_dispatch_rejects_invalid_approval_bindings(change):
    """Persisted approval cannot authorize a different revision, recipient, ownership, or expired state."""
    now = datetime.now(UTC)
    quote = {
        "status": "approved",
        "valid_until": now + timedelta(days=1),
        "content_hash": "current",
        "recipient": "local:customer",
    }
    approval = {"content_hash": "current", "recipient": "local:customer"}
    conversation = {"owner": "agent", "recipient": "local:customer"}
    if change == "expired":
        quote["valid_until"] = now
    if change == "hash":
        approval["content_hash"] = "older"
    if change == "recipient":
        approval["recipient"] = "other-customer"
    if change == "takeover":
        conversation["owner"] = "staff"
    if change == "unapproved":
        quote["status"] = "review"
    with pytest.raises(DomainError):
        assert_dispatchable(quote, approval, conversation, now)
