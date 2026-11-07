from datetime import UTC, datetime, timedelta
from uuid import uuid4

from psycopg.types.json import Jsonb

from luma.core.audit import audit
from luma.core.contracts import digest
from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation
from luma.features.inventory import ledger

from .repository import latest_quote
from .rules import calculate
from .schemas import DraftInput


def draft(conn, member, user, cid, body: DraftInput):
    """Create a reviewable revision from scoped authoritative records, not client prices.

    Lock the conversation, reject an obsolete expected version, resolve all
    products/current sources and require one commercial snapshot. Deterministic
    rules validate money, stock, packs and the supplied member's discount role.
    The new canonical content captures reviewed customer labels and its hash;
    previous revisions and affected queued intents are superseded/blocked in this
    transaction, and a review or approved previous revision releases its stock
    reservation (D49). Return the latest persisted quote. The caller supplies a
    verified member and owns transaction commit; no approval or send occurs here.
    """
    company = member["company_id"]
    current = conversation(conn, company, cid, lock=True)
    if current["version"] != body.expected_version:
        raise DomainError("This request changed. Refresh before saving a revision.")
    previous = latest_quote(conn, company, cid, lock=True)
    if previous and previous["status"] in ("review", "approved"):
        # The old revision's own hold must not count against the new lines (D49); the release
        # is part of this transaction and rolls back with it if the new revision is refused.
        ledger.release_quote(conn, company, previous["id"], "superseded")
    ids = [line.product_id for line in body.lines]
    products = conn.execute(
        "select p.*,coalesce(sl.on_hand-sl.reserved,0) as available from luma.products p join luma.sources s on s.id=p.source_id and s.company_id=p.company_id left join luma.stock_levels sl on sl.company_id=p.company_id and sl.product_id=p.id where p.company_id=%s and p.id=any(%s) and s.retired_at is null",
        (company, ids),
    ).fetchall()
    lookup = {str(p["id"]): p for p in products}
    if any(str(line.product_id) not in lookup for line in body.lines):
        raise DomainError("One or more selected products are unavailable.", 422)
    snapshot_ids = {p["snapshot_id"] for p in products}
    if len(snapshot_ids) != 1:
        raise DomainError("Synchronize a consistent price and stock snapshot.")
    snapshot_id = snapshot_ids.pop()
    totals = calculate(
        [
            {**lookup[str(line.product_id)], "product_id": line.product_id, "quantity": line.quantity}
            for line in body.lines
        ],
        body.discount_percent,
        body.shipping,
        member["role"],
    )
    totals["terms"] = body.terms
    totals["customer_name"] = current["customer_name"]
    totals["customer_company"] = current["customer_company"]
    conn.execute(
        """update luma.outbox set status='blocked',error_code='quotation_prepared',updated_at=now()
        where company_id=%s and conversation_id=%s and kind='reply' and status='queued'""",
        (company, cid),
    )
    revision = previous["revision"] + 1 if previous else 1
    if previous:
        conn.execute("update luma.quotes set status='superseded' where id=%s", (previous["id"],))
        conn.execute(
            "update luma.outbox set status='blocked',error_code='revision_changed' where quote_id=%s and status='queued'",
            (previous["id"],),
        )
    qid = uuid4()
    conn.execute(
        """insert into luma.quotes(id,company_id,conversation_id,number,revision,recipient,snapshot_id,
        content,content_hash,valid_until) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            qid,
            company,
            cid,
            f"LQ-{str(cid)[:8].upper()}",
            revision,
            current["recipient"],
            snapshot_id,
            Jsonb(totals),
            digest(totals),
            datetime.now(UTC) + timedelta(days=7),
        ),
    )
    conn.execute(
        "update luma.conversations set status='review',version=version+1,updated_at=now() where id=%s", (cid,)
    )
    audit(conn, company, user, "quotation.revised", qid, revision=revision)
    return latest_quote(conn, company, cid)
