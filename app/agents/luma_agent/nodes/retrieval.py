"""Exact/lexical-first agent candidates with an optional bounded semantic fallback."""

from decimal import Decimal

from luma.core.config import settings
from luma.core.database import database
from luma.features.catalog.criteria import query_constraints
from luma.features.catalog.retrieval import search_catalog
from luma.features.catalog.schemas import CatalogSearch
from luma.features.catalog.semantic import has_current_embeddings, semantic_search
from luma.features.conversations.repository import conversation

from ..adapters.embeddings import embed_texts, validate_embedding_provider
from ..budget import reserve
from ..lease import assert_job, assert_request_version


def retrieve(state):
    """Replace per-turn candidates with current scoped descriptive suggestions.

    Existing explicit lines need no discovery. For clarification, verify the
    lease/request/owner, prefer lexical hits and attempt a paid query only for a
    descriptive miss with a usable current index and paid AI enabled. Recheck
    locked ownership/version before reserving the retrieval operation. Success
    returns bounded serialized hits; denied/uncertain provider work returns an
    unavailable/no-match result and retains unresolved usage. This node cannot
    select a final quotation line or grant approval; ask rechecks each hit again.
    """
    empty = {"catalog_candidates": [], "retrieval_status": "not_needed"}
    if not state.get("clarification") or state.get("extraction", {}).get("lines"):
        return empty
    config = settings()
    with database(worker=True) as conn:
        assert_job(conn, state)
        current = conversation(conn, state["company_id"], state["conversation_id"])
        assert_request_version(current, state)
        if current["owner"] != "agent":
            return empty
        message = conn.execute(
            "select body from luma.messages where company_id=%s and conversation_id=%s and actor='customer' order by created_at desc,id desc limit 1",
            (state["company_id"], state["conversation_id"]),
        ).fetchone()
        if not message or not message["body"].strip():
            return empty
        request = CatalogSearch(query=message["body"][:500])
        criteria = query_constraints(request)
        if criteria is None:
            return empty
        hits = search_catalog(conn, state["company_id"], request)
        if hits:
            return {
                "catalog_candidates": [hit.model_dump(mode="json") for hit in hits],
                "retrieval_status": "lexical",
            }
        if (
            not config.enable_paid_ai
            or criteria.codes
            or not has_current_embeddings(conn, state["company_id"])
        ):
            return {**empty, "retrieval_status": "no_match"}
    try:
        validate_embedding_provider(config)
        with database(worker=True) as conn:
            assert_job(conn, state)
            current = conversation(conn, state["company_id"], state["conversation_id"], lock=True)
            assert_request_version(current, state)
            if current["owner"] != "agent":
                return empty
            reserve(conn, state["company_id"], state["job_id"], operation="retrieval")
        vectors, estimate = embed_texts(config, [request.query])
        if estimate > Decimal("0.01"):
            raise ValueError("Query consumption exceeds its reservation")
        with database(worker=True) as conn:
            assert_job(conn, state)
            conn.execute(
                "update luma.usage set status='settled',estimated=%s where job_id=%s and operation='retrieval'",
                (estimate, state["job_id"]),
            )
            hits = semantic_search(conn, state["company_id"], request, vectors[0])
        return {
            "catalog_candidates": [hit.model_dump(mode="json") for hit in hits],
            "retrieval_status": "semantic",
        }
    except Exception:
        with database(worker=True) as conn:
            conn.execute(
                "update luma.usage set status='unknown' where job_id=%s and operation='retrieval' and status='reserved'",
                (state["job_id"],),
            )
        return {**empty, "retrieval_status": "unavailable"}
