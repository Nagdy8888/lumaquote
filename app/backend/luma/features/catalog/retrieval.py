"""Exact-code-first PostgreSQL evidence retrieval, with conservative explicit specification filters."""

from .criteria import query_constraints
from .schemas import CatalogHit, CatalogSearch


def search_catalog(conn, company, request: CatalogSearch) -> list[CatalogHit]:
    """Return at most five current cited candidates; explicit model codes never fall back to a near match.

    This measured lexical baseline uses OR-ranked descriptive terms after cheap
    normalization. Watt/CCT/IP filters require unambiguous positive values.
    Negated requirements are left for clarification instead of inverting their
    meaning. No embedding distance or retrieved prose determines money, stock,
    compatibility or action authorization.
    """
    criteria = query_constraints(request)
    if criteria is None:
        return []
    codes, lexical, power, cct, rating = (
        criteria.codes,
        criteria.lexical,
        criteria.watts,
        criteria.cct,
        criteria.ip_rating,
    )
    rows = conn.execute(
        """with q as (select websearch_to_tsquery('english',%s) terms)
        select p.id as product_id,p.sku,p.name,p.description,p.watts,p.cct,p.ip_rating,
        s.id as source_id,s.title as source_title,s.version as source_version,p.page
        from luma.products p join luma.sources s on s.company_id=p.company_id and s.id=p.source_id cross join q
        where p.company_id=%s and s.retired_at is null and not p.discontinued
        and ((cardinality(%s::text[])>0 and p.sku=any(%s::text[])) or
             (cardinality(%s::text[])=0 and (%s or to_tsvector('english',p.sku||' '||p.name||' '||p.family||' '||p.description) @@ q.terms)))
        and (%s::integer is null or p.watts=%s) and (%s::integer is null or p.cct=%s)
        and (%s::text is null or p.ip_rating=%s)
        order by ts_rank_cd(to_tsvector('english',p.sku||' '||p.name||' '||p.family||' '||p.description),q.terms) desc,p.sku limit 5""",
        (
            lexical,
            company,
            codes,
            codes,
            codes,
            criteria.browse_specs,
            power,
            power,
            cct,
            cct,
            rating,
            rating,
        ),
    ).fetchall()
    return [CatalogHit.model_validate(row) for row in rows]


def candidate_question(hits: list[CatalogHit]) -> str | None:
    """Render only validated model/specification identifiers and page provenance into a fixed confirmation question."""
    if not hits:
        return None
    evidence = "; ".join(
        f"{hit.sku} ({hit.watts}W, {hit.cct}K, {hit.ip_rating}; catalog v{hit.source_version}, page {hit.page})"
        for hit in hits
    )
    return f"Possible catalog matches: {evidence}. These are suggestions, not confirmed equivalents. Please confirm the product SKU and quantity you need in a text reply."
