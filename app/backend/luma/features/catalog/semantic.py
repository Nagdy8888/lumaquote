"""Version-bound semantic candidates supplement exact/lexical lookup without changing commercial authority."""

import json
import math

from luma.core.errors import DomainError

from .criteria import query_constraints
from .retrieval import search_catalog
from .schemas import CatalogHit, CatalogSearch


def vector_literal(values: list[float]) -> str:
    """Validate a bounded nonzero 1536-dimensional provider vector before sending a parameterized pgvector literal."""
    if len(values) != 1536 or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or abs(value) > 1
        for value in values
    ):
        raise DomainError("The embedding provider returned an invalid vector.", 503)
    if sum(value * value for value in values) < 1e-12:
        raise DomainError("The embedding provider returned an empty vector.", 503)
    return json.dumps(values, allow_nan=False, separators=(",", ":"))


def semantic_search(conn, company, request: CatalogSearch, vector: list[float]) -> list[CatalogHit]:
    """Return at most five candidates from current, matching descriptive evidence, preserving all explicit constraints.

    Exact codes never use semantic substitution. A conservative cosine-distance
    ceiling bounds suggestions; it is not a calibrated correctness probability.
    Stale source/content/page/model vectors are excluded in the database query.
    """
    criteria = query_constraints(request)
    if criteria is None:
        return []
    if criteria.codes:
        return search_catalog(conn, company, request)
    literal = vector_literal(vector)
    rows = conn.execute(
        """select p.id as product_id,p.sku,p.name,p.description,p.watts,p.cct,p.ip_rating,
        s.id as source_id,s.title as source_title,s.version as source_version,p.page
        from luma.catalog_embeddings e join luma.products p on p.company_id=e.company_id and p.id=e.product_id
        join luma.sources s on s.company_id=p.company_id and s.id=p.source_id
        where p.company_id=%s and s.retired_at is null and not p.discontinued
        and e.source_id=p.source_id and e.source_version=s.version and e.page=p.page
        and e.content=luma.catalog_evidence_text(p) and e.model='text-embedding-3-small'
        and (%s::integer is null or p.watts=%s) and (%s::integer is null or p.cct=%s)
        and (%s::text is null or p.ip_rating=%s)
        and (e.embedding <=> %s::extensions.vector)<=0.45
        order by e.embedding <=> %s::extensions.vector,p.sku limit 5""",
        (
            company,
            criteria.watts,
            criteria.watts,
            criteria.cct,
            criteria.cct,
            criteria.ip_rating,
            criteria.ip_rating,
            literal,
            literal,
        ),
    ).fetchall()
    return [CatalogHit.model_validate(row) for row in rows]


def embedding_inputs(conn, company) -> list[dict]:
    """Read current descriptive records for a bounded operator index run; prices/stock and customer data are excluded."""
    rows = conn.execute(
        """select p.id as product_id,p.source_id,s.version as source_version,p.page,
        luma.catalog_evidence_text(p) as content from luma.products p join luma.sources s on s.id=p.source_id and s.company_id=p.company_id
        where p.company_id=%s and s.retired_at is null and not p.discontinued order by p.sku limit 501""",
        (company,),
    ).fetchall()
    if (
        not rows
        or len(rows) > 500
        or any(len(row["content"].encode()) > 8000 for row in rows)
        or sum(len(row["content"].encode()) for row in rows) > 100000
    ):
        raise DomainError("Catalog indexing exceeds its bounded input policy or has no current records.", 422)
    return rows


def has_current_embeddings(conn, company) -> bool:
    """Avoid a paid query embedding when the tenant has no currently usable descriptive vector evidence."""
    return bool(
        conn.execute(
            """select 1 from luma.catalog_embeddings e
        join luma.products p on p.company_id=e.company_id and p.id=e.product_id
        join luma.sources s on s.company_id=p.company_id and s.id=p.source_id
        where p.company_id=%s and s.retired_at is null and not p.discontinued
        and e.source_id=p.source_id and e.source_version=s.version and e.page=p.page
        and e.content=luma.catalog_evidence_text(p) and e.model='text-embedding-3-small' limit 1""",
            (company,),
        ).fetchone()
    )


def publish_embeddings(conn, company, records, vectors):
    """Upsert a bounded batch only when its descriptive input bindings still match.

    Re-read ordered current inputs and reject changed records or vector count
    before writing. Validate every vector, then upsert the company/product cache
    with source/version/page/model/content identity. The caller must own the
    transaction: any later validation failure must roll back the whole batch.
    Future edits also invalidate rows at retrieval time. No commercial fields or
    source documents are modified, and this is not a distributed provider commit.
    """
    current = embedding_inputs(conn, company)
    if current != records or len(vectors) != len(records):
        raise DomainError("The catalog changed during indexing. Review the new source before another run.")
    for record, vector in zip(records, vectors, strict=True):
        literal = vector_literal(vector)
        conn.execute(
            """insert into luma.catalog_embeddings(company_id,product_id,source_id,source_version,page,model,content,embedding)
            values(%s,%s,%s,%s,%s,'text-embedding-3-small',%s,%s::extensions.vector)
            on conflict(company_id,product_id) do update set source_id=excluded.source_id,source_version=excluded.source_version,
            page=excluded.page,model=excluded.model,content=excluded.content,embedding=excluded.embedding,indexed_at=now()""",
            (
                company,
                record["product_id"],
                record["source_id"],
                record["source_version"],
                record["page"],
                record["content"],
                literal,
            ),
        )
