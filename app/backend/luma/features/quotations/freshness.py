from datetime import UTC, datetime, timedelta
from decimal import Decimal

from luma.core.errors import DomainError


def check_snapshot(conn, quote, current):
    """Validate the stored offer against current commercial and source records.

    Synthetic observations are eligible only on local_test; other observations
    must be at most 90 seconds old. Each line must retain its snapshot, active
    source/page, price, valid pack quantity and sufficient available stock, with
    no discontinued product. Raise DomainError before approval/dispatch on any
    mismatch. This check neither reserves stock nor mutates/reprices an offer;
    the caller must require a new reviewed revision when evidence changed.
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
        "select p.*,s.retired_at from luma.products p join luma.sources s on s.id=p.source_id and s.company_id=p.company_id where p.company_id=%s and p.id=any(%s::uuid[])",
        (quote["company_id"], ids),
    ).fetchall()
    lookup = {str(p["id"]): p for p in products}
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
            or p["available"] < line["quantity"]
        ):
            raise DomainError("Price or availability changed. Create and approve a new revision.")
