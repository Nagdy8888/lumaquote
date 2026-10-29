"""Exact-code-first PostgreSQL evidence retrieval, with conservative explicit specification filters."""

import re

from .schemas import CatalogHit, CatalogSearch

NOISE = {
    "please",
    "quote",
    "need",
    "needs",
    "looking",
    "want",
    "would",
    "like",
    "give",
    "some",
    "lights",
    "lighting",
    "product",
    "products",
    "supplier",
    "synthetic",
    "test",
}


def search_catalog(conn, company, request: CatalogSearch) -> list[CatalogHit]:
    """Return at most five current cited candidates; explicit model codes never fall back to a near match.

    This measured lexical baseline uses OR-ranked descriptive terms after cheap
    normalization. Watt/CCT/IP filters require unambiguous positive values.
    Negated requirements are left for clarification instead of inverting their
    meaning. No embedding distance or retrieved prose determines money, stock,
    compatibility or action authorization.
    """
    query = request.query
    if re.search(r"\b(not|except|avoid|without|instead)\b", query, re.I):
        return []
    codes = list(dict.fromkeys(re.findall(r"\b[A-Z]{2}-\d{3}\b", query.upper())))
    watts = {int(v) for v in re.findall(r"\b(\d{1,4})\s*(?:w|watts?)\b", query, re.I)}
    temperatures = {int(v) for v in re.findall(r"\b(\d{4,5})\s*k\b", query, re.I)}
    ratings = set(re.findall(r"\bIP[0-6][0-9]\b", query.upper()))
    if len(watts) > 1 or len(temperatures) > 1 or len(ratings) > 1:
        return []
    power = request.watts if request.watts is not None else next(iter(watts), None)
    cct = request.cct if request.cct is not None else next(iter(temperatures), None)
    rating = request.ip_rating or next(iter(ratings), None)
    if (
        (watts and power not in watts)
        or (temperatures and cct not in temperatures)
        or (ratings and rating not in ratings)
    ):
        return []
    words = list(
        dict.fromkeys(
            word.lower() for word in re.findall(r"\b[a-zA-Z]{3,30}\b", query) if word.lower() not in NOISE
        )
    )[:24]
    if not codes and not words and power is None and cct is None and rating is None:
        return []
    lexical = " OR ".join(words)
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
        (lexical, company, codes, codes, codes, not bool(words), power, power, cct, cct, rating, rating),
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
