"""Explicit paid synthetic embedding plumbing canary; not a semantic accuracy benchmark."""

import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from luma.core.config import settings
from luma.core.database import database
from luma.features.catalog.schemas import CatalogSearch
from luma.features.catalog.semantic import embedding_inputs, semantic_search
from luma_agent.adapters.embeddings import embed_texts
from luma_agent.budget import reserve
from luma_agent.runtime.catalog_index import index_company

pytestmark = pytest.mark.skipif(
    os.environ.get("LUMA_RUN_LIVE_EMBEDDINGS") != "1",
    reason="Paid synthetic embedding canary requires explicit opt-in.",
)


def test_live_embedding_index_and_query_roundtrip(environment, monkeypatch):
    """Index three synthetic records and retrieve unchanged evidence with a separately reserved real query vector."""
    env = environment
    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    settings.cache_clear()
    run = uuid4()
    indexed = index_company(env["company"], run)
    with database(worker=True) as conn:
        records = embedding_inputs(conn, env["company"])
        reserve(conn, env["company"], run, operation="retrieval")
    vectors, estimate = embed_texts(settings(), [records[0]["content"]])
    assert estimate <= 0.01
    with database(worker=True) as conn:
        conn.execute(
            "update luma.usage set status='settled',estimated=%s where job_id=%s and operation='retrieval'",
            (estimate, run),
        )
        hits = semantic_search(conn, env["company"], CatalogSearch(query="ceiling fittings"), vectors[0])
        assert any(hit.product_id == records[0]["product_id"] for hit in hits)
        assert all(hit.source_id == env["source"] and hit.source_version == 1 for hit in hits)
    Path(".local/live-embedding-canary.json").write_text(
        json.dumps(
            {
                "model": "text-embedding-3-small",
                "dimensions": 1536,
                "indexed_synthetic_records": indexed["records"],
                "index_estimated_usd": indexed["estimated_usd"],
                "query_estimated_usd": str(estimate),
                "actual_billing": "not retrieved",
                "result": "Real provider/index/query SQL roundtrip passed with unchanged synthetic descriptive evidence",
                "limitation": "Query vector embeds the same evidence text; this is plumbing validation, not natural-language recall or holdout accuracy. No quote, approval or send is created.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
