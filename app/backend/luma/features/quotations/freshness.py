from datetime import UTC, datetime, timedelta
from decimal import Decimal

from luma.core.errors import DomainError
from luma.features.inventory.ledger import held_quantities


def check_snapshot(conn, quote, current, *, dispatch: bool = False):
    """Validate the stored offer against current commercial and source records.

    Synthetic observations are eligible only on local_test; other observations
    must be at most 90 seconds old. Each line must retain its snapshot, active
    source/page, price, valid pack quantity and a non-discontinued product. Stock
    depends on the phase (decision D49):
    - Approval (`dispatch=False`, quote in review, no reservation yet): every line needs
      `available >= quantity`, available being on hand minus reserved from the stock ledger.
      The approval then reserves the stock in the same transaction.
    - Dispatch (`dispatch=True`, called with the quote row locked for an already-approved
      quote): its own hold already lowered available, so instead every product must have a
      `held` reservation for this quote equal to the summed line quantity. A released,
      converted or missing reservation is a mismatch.
    Raise DomainError before approval/dispatch on any mismatch. This check neither reserves
    stock nor mutates/reprices an offer; the caller must require a new reviewed revision when
    evidence changed.
    """
    source = conn.execute(
        "select * from luma.snapshots where id=%s and company_id=%s",
        (quote["snapshot_id"], quote["company_id"]),
    ).fetchone()
    if not source:
        raise DomainError("Commercial source not found.")
    # Synthetic records are an explicitly local test source and cannot reach WhatsApp.
    if source["source"] == "synthetic":
        if current["channel"] != "local_test":
            raise DomainError("Connect a validated Google Sheets snapshot before live quotation delivery.")
    elif datetime.now(UTC) - source["observed_at"] > timedelta(seconds=90):
        raise DomainError("Price and stock sync is stale. Refresh Google Sheets before finalizing.")
    ids = [line["product_id"] for line in quote["content"]["lines"]]
    products = conn.execute(
        "select p.*,s.retired_at,coalesce(sl.on_hand-sl.reserved,0) as available from luma.products p join luma.sources s on s.id=p.source_id and s.company_id=p.company_id left join luma.stock_levels sl on sl.company_id=p.company_id and sl.product_id=p.id where p.company_id=%s and p.id=any(%s::uuid[])",
        (quote["company_id"], ids),
    ).fetchall()
    lookup = {str(p["id"]): p for p in products}
    held = None
    if dispatch:
        wanted: dict[str, int] = {}
        for line in quote["content"]["lines"]:
            wanted[line["product_id"]] = wanted.get(line["product_id"], 0) + line["quantity"]
        reserved = {str(key): value for key, value in held_quantities(conn, quote["company_id"], quote["id"]).items()}
        if reserved != wanted:
            raise DomainError("Price or availability changed. Create and approve a new revision.")
        held = reserved
    for line in quote["content"]["lines"]:
        p = lookup.get(line["product_id"])
        if (
            not p
            or p["snapshot_id"] != quote["snapshot_id"]
            or p["retired_at"] is not None
            or str(p["source_id"]) != line["source_id"]
            or p["page"] != line["page"]
            or p["price"] != Decimal(line["unit_price"])
            or line["quantity"] % p["pack_size"] != 0
            or p["discontinued"]
            or (held is None and p["available"] < line["quantity"])
        ):
            raise DomainError("Price or availability changed. Create and approve a new revision.")
