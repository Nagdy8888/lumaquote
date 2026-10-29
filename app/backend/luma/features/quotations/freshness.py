from datetime import UTC, datetime, timedelta

from luma.core.errors import DomainError


def check_snapshot(conn, quote, current):
    """Block finalization when commercial evidence is absent, stale, inconsistent, or synthetic for a live channel."""
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
        "select * from luma.products where company_id=%s and id=any(%s::uuid[])", (quote["company_id"], ids)
    ).fetchall()
    lookup = {str(p["id"]): p for p in products}
    for line in quote["content"]["lines"]:
        p = lookup.get(line["product_id"])
        if (
            not p
            or p["snapshot_id"] != quote["snapshot_id"]
            or p["discontinued"]
            or p["available"] < line["quantity"]
        ):
            raise DomainError("Price or availability changed. Create and approve a new revision.")
