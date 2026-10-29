"""Opt-in paid provider canary; excluded unless explicitly enabled for the approved synthetic check."""

import json
import os
from pathlib import Path

import psycopg
import pytest
from luma.core.config import settings
from luma_agent.runtime.conversations import process_conversation
from psycopg.rows import dict_row
from test_manual_workflow import create_request, get_detail
from test_preparation_conflicts import running_job

pytestmark = pytest.mark.skipif(
    os.environ.get("LUMA_RUN_LIVE") != "1", reason="Paid synthetic canary requires explicit opt-in."
)


def test_live_structured_extraction_prepares_only_review(environment, monkeypatch):
    """One budget-reserved real Responses call prepares a cited draft but never creates approval or dispatch authority."""
    env = environment
    cid = create_request(env)
    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    settings.cache_clear()
    process_conversation(running_job(env, cid))
    current = get_detail(env, cid)
    assert current["quote"]["status"] == "review"
    assert current["quote"]["content"]["total"] == "97.05"
    assert current["delivery"] == []
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        usage = conn.execute(
            "select status,reserved,estimated from luma.usage where company_id=%s", (env["company"],)
        ).fetchone()
        assert usage["status"] == "settled"
        assert usage["estimated"] is not None and usage["estimated"] <= usage["reserved"]
        assert (
            conn.execute(
                "select count(*) n from luma.approvals where company_id=%s", (env["company"],)
            ).fetchone()["n"]
            == 0
        )
    Path(".local/live-model-canary.json").write_text(
        json.dumps(
            {
                "model": "gpt-6-luna",
                "processing": "Standard",
                "provider_call": "verified",
                "data": "synthetic exact-SKU request",
                "outcome": "review only; USD 97.05; no approval or send",
                "usage": "token-derived estimate, not actual provider billing",
                "estimated_usd": str(usage["estimated"]),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
