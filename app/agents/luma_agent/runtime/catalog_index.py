"""Explicit local synthetic indexing with durable reservation and atomic source-bound publication."""

from decimal import Decimal

from luma.core.audit import audit
from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.catalog.semantic import embedding_inputs, publish_embeddings
from psycopg.conninfo import conninfo_to_dict

from ..adapters.embeddings import embed_texts, validate_embedding_provider
from ..budget import reserve


def index_company(company, run_id):
    """Index one synthetic local supplier under a stable paid-operation identity.

    Require this project's loopback DSN, valid fixed provider configuration and
    a synthetic tenant. Under the company lock, deny unresolved prior indexing,
    bound inputs and commit reservation/start audit before the external call.
    Publish still-current vectors with settlement/completion audit together;
    failure retains unknown usage and an unresolved audit rather than retrying.
    Return safe counts/run identity/estimated usage, never credentials or billed
    cost. Explicit operator execution is separate from routine setup/test work.
    """
    config = settings()
    params = conninfo_to_dict(config.luma_worker_database_url.get_secret_value())
    if params.get("host") not in ("127.0.0.1", "localhost") or params.get("port") != "55322":
        raise DomainError("This indexing command is restricted to the isolated local database.")
    validate_embedding_provider(config)
    with database(worker=True) as conn:
        conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (f"catalog.index:{company}",))
        tenant = conn.execute("select synthetic from luma.companies where id=%s", (company,)).fetchone()
        if not tenant or not tenant["synthetic"]:
            raise DomainError("Operator indexing requires an explicitly synthetic supplier.")
        pending = conn.execute(
            """select 1 from luma.audit a join luma.usage u on u.job_id=a.resource_id
            where a.company_id=%s and a.action='catalog.index_started' and u.status in ('reserved','unknown') limit 1""",
            (company,),
        ).fetchone()
        if pending:
            raise DomainError("A prior index run needs reconciliation before another paid batch.")
        records = embedding_inputs(conn, company)
        reserve(conn, company, run_id)
        audit(conn, company, "operator", "catalog.index_started", run_id, records=len(records))
    try:
        vectors, estimate = embed_texts(config, [record["content"] for record in records])
        if estimate > Decimal(str(config.reservation)):
            raise DomainError("Index consumption needs allowance reconciliation.")
        with database(worker=True) as conn:
            publish_embeddings(conn, company, records, vectors)
            conn.execute(
                "update luma.usage set status='settled',estimated=%s where job_id=%s and operation='primary'",
                (estimate, run_id),
            )
            audit(conn, company, "operator", "catalog.index_completed", run_id, records=len(records))
        return {
            "run_id": str(run_id),
            "records": len(records),
            "estimated_usd": str(estimate),
            "actual_billing": "not retrieved",
        }
    except Exception:
        with database(worker=True) as conn:
            conn.execute(
                "update luma.usage set status='unknown' where job_id=%s and operation='primary'", (run_id,)
            )
            audit(conn, company, "operator", "catalog.index_unresolved", run_id)
        raise
