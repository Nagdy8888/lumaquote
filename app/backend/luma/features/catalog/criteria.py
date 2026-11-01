"""Shared conservative specification parsing for lexical and semantic candidate lookup."""

import re
from dataclasses import dataclass

from .schemas import CatalogSearch

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


@dataclass(frozen=True)
class SearchCriteria:
    """Carry one conservatively parsed query shared by lexical and semantic search.

    codes retain exact model precedence; lexical contains bounded OR-ranked words.
    watts/cct/ip_rating are unambiguous positive filters, not model suggestions.
    browse_specs permits a specification-only lookup when descriptive terms are
    absent. A refused/ambiguous parse is represented by None from the parser,
    never by an instance with silently weakened constraints.
    """

    codes: list[str]
    lexical: str
    watts: int | None
    cct: int | None
    ip_rating: str | None
    browse_specs: bool


def query_constraints(request: CatalogSearch) -> SearchCriteria | None:
    """Return shared filters or refuse ambiguous/negated requirements; no semantic caller may relax these conditions."""
    query = request.query
    if re.search(r"\b(not|except|avoid|without|instead)\b", query, re.I):
        return None
    codes = list(dict.fromkeys(re.findall(r"\b[A-Z]{2}-\d{3}\b", query.upper())))
    watts = {int(v) for v in re.findall(r"\b(\d{1,4})\s*(?:w|watts?)\b", query, re.I)}
    temperatures = {int(v) for v in re.findall(r"\b(\d{4,5})\s*k\b", query, re.I)}
    ratings = set(re.findall(r"\bIP[0-6][0-9]\b", query.upper()))
    if len(watts) > 1 or len(temperatures) > 1 or len(ratings) > 1:
        return None
    power = request.watts if request.watts is not None else next(iter(watts), None)
    cct = request.cct if request.cct is not None else next(iter(temperatures), None)
    rating = request.ip_rating or next(iter(ratings), None)
    if (
        (watts and power not in watts)
        or (temperatures and cct not in temperatures)
        or (ratings and rating not in ratings)
    ):
        return None
    words = list(
        dict.fromkeys(
            word.lower() for word in re.findall(r"\b[a-zA-Z]{3,30}\b", query) if word.lower() not in NOISE
        )
    )[:24]
    if not codes and not words and power is None and cct is None and rating is None:
        return None
    return SearchCriteria(codes, " OR ".join(words), power, cct, rating, not bool(words))
