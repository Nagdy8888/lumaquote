from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from luma.core.errors import DomainError

CENT = Decimal("0.01")


def calculate(lines: list[dict], discount: Decimal, shipping: Decimal, role: str) -> dict:
    """Return canonical USD line and order totals from validated products using Decimal arithmetic and role-bound discounts."""
    if not discount.is_finite() or not shipping.is_finite() or not 0 <= discount <= 10 or shipping < 0:
        raise DomainError("Invalid commercial values.", 422)
    if discount and role != "admin":
        raise DomainError("Only an administrator can authorize a discount.", 403)
    if not lines or len({str(line["product_id"]) for line in lines}) != len(lines):
        raise DomainError("Select distinct products.", 422)
    result = []
    for line in lines:
        quantity = line["quantity"]
        if type(quantity) is not int or not 1 <= quantity <= 10000:
            raise DomainError("Quantity must be an integer from 1 to 10,000.", 422)
        if line["discontinued"] or quantity > line["available"] or quantity % line["pack_size"]:
            raise DomainError(f"{line['sku']}: check availability and pack size.", 422)
        price = Decimal(str(line["price"]))
        if not price.is_finite() or price < 0:
            raise DomainError("Invalid source price.", 422)
        result.append(
            {
                "product_id": str(line["product_id"]),
                "sku": line["sku"],
                "name": line["name"],
                "quantity": quantity,
                "unit": "each",
                "unit_price": str(price.quantize(CENT)),
                "line_total": str((price * quantity).quantize(CENT, rounding=ROUND_HALF_UP)),
                "source_id": str(line["source_id"]),
                "page": line["page"],
            }
        )
    subtotal = sum((Decimal(line["line_total"]) for line in result), Decimal(0))
    discount_value = (subtotal * discount / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    shipping = shipping.quantize(CENT, rounding=ROUND_HALF_UP)
    return {
        "lines": result,
        "currency": "USD",
        "tax": "Excluded",
        "subtotal": str(subtotal),
        "discount_percent": str(discount),
        "discount": str(discount_value),
        "shipping": str(shipping),
        "total": str(subtotal - discount_value + shipping),
        # Content is immutable and hashed at draft time, before approval reserves anything, so this
        # stays False. The real hold lives in `luma.stock_reservations` (inventory ledger, D49).
        "stock_reserved": False,
    }


def assert_dispatchable(quote: dict, approval: dict | None, conversation: dict, now: datetime):
    """Reject unapproved, expired, mismatched, or staff-paused quotation sends without modifying state."""
    if quote["status"] != "approved" or quote["valid_until"] <= now:
        raise DomainError("This quotation is not approved or has expired.")
    if (
        not approval
        or approval["content_hash"] != quote["content_hash"]
        or approval["recipient"] != quote["recipient"]
    ):
        raise DomainError("Approval does not match this revision and recipient.")
    if conversation["owner"] != "agent":
        raise DomainError("Staff takeover has paused automated delivery.")
    if conversation["recipient"] != quote["recipient"]:
        raise DomainError("Customer changed; review a new revision.")
