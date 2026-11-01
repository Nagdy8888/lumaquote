"""Actual leased retrieval/clarification nodes with only the paid provider response replaced."""

from decimal import Decimal

import psycopg
import pytest
from luma.core.config import settings
from luma_agent.nodes import retrieval
from luma_agent.nodes.workflow import ask
from psycopg.rows import dict_row
from test_manual_workflow import get_detail, post
from test_semantic_catalog import publish_fixture


@pytest.mark.parametrize("outcome", ["success", "lost", "takeover", "retired"])
def test_agent_semantic_fallback_preserves_action_and_source_boundaries(environment, monkeypatch, outcome):
    """Only current candidates become clarification; ownership change or uncertain provider response cannot create final lines."""
    env = environment
    created = post(
        env,
        "/conversations",
        {
            "customer_name": "Synthetic retrieval customer",
            "customer_company": "Fixture",
            "text": "Need ceiling fittings.",
        },
    )
    assert created.status_code == 200
    cid = created.json()["id"]
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        vector = publish_fixture(conn, env["company"])
        job = conn.execute(
            """update luma.jobs set status='running',fence=fence+1,
            lease_until=now()+interval '120 seconds' where company_id=%s returning *""",
            (env["company"],),
        ).fetchone()
    state = {
        "company_id": str(env["company"]),
        "conversation_id": cid,
        "job_id": str(job["id"]),
        "fence": job["fence"],
        "observed_version": get_detail(env, cid)["conversation"]["version"],
        "extraction": {"lines": []},
        "clarification": "Which model and quantity do you need?",
    }
    calls = []

    def validate_fixture(config):
        """Simulate a takeover between initial lookup and admission when requested; no provider is contacted."""
        if outcome == "takeover":
            with psycopg.connect(env["dsn"]) as conn:
                conn.execute("update luma.conversations set owner='staff' where id=%s", (cid,))

    def embed_fixture(config, texts):
        """Supply deterministic vectors or a lost-response failure at the real adapter seam."""
        calls.append(len(texts))
        if outcome == "lost":
            raise TimeoutError("Synthetic lost query response")
        return [vector], Decimal("0.000001")

    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    settings.cache_clear()
    monkeypatch.setattr(retrieval, "validate_embedding_provider", validate_fixture)
    monkeypatch.setattr(retrieval, "embed_texts", embed_fixture)
    result = retrieval.retrieve(state)
    if outcome == "takeover":
        assert calls == [] and result["catalog_candidates"] == []
    elif outcome == "lost":
        assert result["retrieval_status"] == "unavailable"
        assert retrieval.retrieve(state)["retrieval_status"] == "unavailable"
        assert calls == [1]
    else:
        assert result["retrieval_status"] == "semantic" and len(result["catalog_candidates"]) == 3
        if outcome == "retired":
            with psycopg.connect(env["dsn"]) as conn:
                conn.execute("update luma.sources set retired_at=now() where id=%s", (env["source"],))
        question = ask({**state, **result})["clarification"]
        assert ("DL-001" in question) == (outcome == "success")
        if outcome == "success":
            assert "catalog v1, page 1" in question
    current = get_detail(env, cid)
    assert current["quote"] is None
    assert all(item["kind"] == "reply" for item in current["delivery"])
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        usage = conn.execute("select status from luma.usage where job_id=%s", (job["id"],)).fetchone()
        assert usage == (
            None if outcome == "takeover" else {"status": "unknown" if outcome == "lost" else "settled"}
        )
