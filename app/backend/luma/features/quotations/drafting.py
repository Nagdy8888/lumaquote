from datetime import UTC, datetime, timedelta
from uuid import uuid4

from psycopg.types.json import Jsonb

from luma.core.audit import audit
from luma.core.contracts import digest
from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation

from .repository import latest_quote
from .rules import calculate
from .schemas import DraftInput


def draft(conn, member, user, cid, body: DraftInput):
    """Validate an expected conversation version and authoritative products, then create a new immutable quotation revision."""
    company = member["company_id"]
    current = conversation(conn, company, cid, lock=True)
    if current["version"] != body.expected_version:
        raise DomainError("This request changed. Refresh before saving a revision.")
    ids = [line.product_id for line in body.lines]
    products = conn.execute(
        "select * from luma.products where company_id=%s and id=any(%s)", (company, ids)
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
    previous = latest_quote(conn, company, cid, lock=True)
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
