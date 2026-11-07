"""Atomic GAS snapshot imports that preserve catalog identity and immutable quote evidence."""

import hashlib
import json
import time
from datetime import UTC, datetime
from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb
from pydantic import ValidationError

from luma.core.database import database
from luma.core.errors import DomainError

from .callbacks import verify_mapping, verify_signature
from .schemas import SnapshotEnvelope
from .validation import validate_tables


def receive_snapshot(body: bytes, signature: str):
    """Verify a complete signed snapshot, then serialize imports and replay decisions per company.

    No product is inserted without catalog evidence. Unchanged snapshots refresh
    observation time; changed business data creates a new evidence version. The
    Inventory table is still validated and part of the digest, but stock is owned
    by the web app's ledger (D49): no stock level or movement is ever written here.
    """
    verify_signature(body, signature)
    try:
        envelope = SnapshotEnvelope.model_validate_json(body)
    except ValidationError:
        raise DomainError("Invalid supplier snapshot schema.", 422) from None
    verify_mapping(envelope)
    if envelope.timestamp > time.time() + 5:
        raise DomainError("Snapshot observation is in the future.", 401)
    products, prices, inventory = validate_tables(envelope)
    canonical = {
        "products": [products[sku].model_dump(mode="json") for sku in sorted(products)],
        "prices": [prices[sku].model_dump(mode="json") for sku in sorted(prices)],
        "inventory": [inventory[sku].model_dump(mode="json") for sku in sorted(inventory)],
    }
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
    fingerprint = hashlib.sha256(body).hexdigest()
    observed = datetime.fromtimestamp(envelope.timestamp, UTC)
    company = envelope.company_id
    try:
        with database(worker=True) as conn:
            conn.execute("set local statement_timeout='5s'")
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (str(company),))
            conn.execute(
                "delete from luma.google_snapshot_receipts where received_at<now()-interval '10 minutes'"
            )
            old = conn.execute(
                "select fingerprint from luma.google_snapshot_receipts where company_id=%s and nonce=%s",
                (company, envelope.nonce),
            ).fetchone()
            if old:
                if old["fingerprint"] != fingerprint:
                    raise DomainError("Snapshot nonce reused with different content.", 409)
                return {"status": "accepted", "sync_status": "duplicate"}
            count = conn.execute(
                "select count(*) n from luma.google_snapshot_receipts where company_id=%s "
                "and received_at>now()-interval '1 minute'",
                (company,),
            ).fetchone()["n"]
            if count >= 30:
                raise DomainError("Snapshot rate exceeded.", 429)
            current = conn.execute(
                "select * from luma.google_sync_state where company_id=%s", (company,)
            ).fetchone()
            if current and observed <= current["observed_at"]:
                raise DomainError(
                    "Snapshot is older than the current observation; retry with a fresh read.", 409
                )
            catalog = conn.execute(
                "select * from luma.products where company_id=%s for update", (company,)
            ).fetchall()
            if {row["sku"] for row in catalog} != products.keys():
                raise DomainError("Snapshot SKU set must match the complete ingested catalog.", 422)
            fields = ("name", "family", "watts", "lumens", "cct", "ip_rating")
            if any(any(row[key] != getattr(products[row["sku"]], key) for key in fields) for row in catalog):
                raise DomainError(
                    "Supplier specifications differ from catalog evidence; ingest updated evidence first.",
                    422,
                )
            sid = current["snapshot_id"] if current and current["digest"] == digest else uuid4()
            conn.execute(
                "insert into luma.snapshots(id,company_id,source,observed_at,digest) values(%s,%s,'google_sheets',%s,%s) "
                "on conflict(id) do update set observed_at=excluded.observed_at",
                (sid, company, observed, digest),
            )
            for row in catalog:
                sku = row["sku"]
                conn.execute(
                    "update luma.products set price=%s,pack_size=%s,discontinued=%s,snapshot_id=%s "
                    "where id=%s and company_id=%s",
                    (
                        prices[sku].unit_price,
                        products[sku].pack_size,
                        products[sku].discontinued,
                        sid,
                        row["id"],
                        company,
                    ),
                )
            conn.execute(
                "insert into luma.google_sync_state(company_id,snapshot_id,observed_at,digest,source_tables) "
                "values(%s,%s,%s,%s,%s) on conflict(company_id) do update set snapshot_id=excluded.snapshot_id,"
                "observed_at=excluded.observed_at,digest=excluded.digest,source_tables=excluded.source_tables",
                (company, sid, observed, digest, Jsonb(envelope.tables.model_dump(mode="json"))),
            )
            conn.execute(
                "insert into luma.google_snapshot_receipts(company_id,nonce,fingerprint) values(%s,%s,%s)",
                (company, envelope.nonce, fingerprint),
            )
            conn.execute(
                "delete from luma.google_refresh_signals where company_id=%s and date_trunc('second',requested_at)<=%s",
                (company, observed),
            )
            return {"status": "accepted", "sync_status": "validated", "product_count": len(products)}
    except psycopg.Error:
        raise DomainError("Supplier snapshot storage unavailable.", 503) from None
