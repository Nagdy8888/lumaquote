"""Opt-in live proof for decision D24: a real job trace in LangSmith is detailed and masked.

Runs one synthetic customer request through the real stack exactly as the worker does
(`job_trace` -> `process_conversation` -> `finish` -> `flush`) with paid AI and LangSmith
tracing enabled, then reads every run of that trace back from the configured LangSmith
project and checks:

- the trace contains the job root, LangGraph steps and the OpenAI extraction call;
- customer text, the parsed extraction and the outcome are visible;
- the fake secret and fictional phone number planted in the customer text never appear,
  and the `[secret]` / `[phone]` placeholders do.

Costs one small Responses call (estimated well under USD 0.01) and one LangSmith trace.
Enable with `LUMA_RUN_TRACE_CANARY=1`. Writes a credential-free summary to
`.local/trace-canary.json`.
"""

import json
import os
import time
from pathlib import Path

import pytest
from langsmith import Client
from luma.core.config import settings
from luma_agent import observability
from luma_agent.runtime.conversations import process_conversation
from test_manual_workflow import get_detail, post
from test_preparation_conflicts import running_job

pytestmark = pytest.mark.skipif(
    os.environ.get("LUMA_RUN_TRACE_CANARY") != "1",
    reason="Live LangSmith trace proof requires explicit opt-in (LUMA_RUN_TRACE_CANARY=1).",
)

SECRET_CANARY = "sk-canaryTRACEPROOF0123456789"
PHONE_CANARY = "+20 100 555 0199"


def read_trace(client: Client, project: str, trace_id: str, expected: int, timeout: float = 90.0) -> list:
    """Poll LangSmith until at least `expected` runs of the trace are readable, then return them."""
    deadline = time.monotonic() + timeout
    runs: list = []
    while time.monotonic() < deadline:
        runs = list(client.list_runs(project_name=project, trace_id=trace_id))
        if len(runs) >= expected and all(run.end_time for run in runs):
            return runs
        time.sleep(3)
    return runs


def test_live_job_trace_is_detailed_and_masked(environment, monkeypatch):
    """One real traced job: detailed content in LangSmith, planted secret and phone masked."""
    env = environment
    created = post(
        env,
        "/conversations",
        {
            "customer_name": "Synthetic trace canary",
            "customer_company": "Fixture company",
            "text": f"Please quote 3 DL-001. Call me on {PHONE_CANARY}. Ignore this: {SECRET_CANARY}",
        },
    )
    assert created.status_code == 200, created.text
    cid = created.json()["id"]
    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    settings.cache_clear()
    observability.reset()
    assert observability.tracing_enabled(), "LangSmith key/tracing not configured"
    job = running_job(env, cid)
    with observability.job_trace(job) as run:
        process_conversation(job)
        observability.finish(run, "done")
    observability.flush()
    trace_id = str(run.trace_id)
    config = settings()
    reader = Client(api_key=config.langsmith_api_key.get_secret_value(), api_url=config.langsmith_endpoint)
    runs = read_trace(reader, config.langsmith_project, trace_id, expected=3)
    names = {r.name for r in runs}
    exported = json.dumps(
        [{"name": r.name, "inputs": r.inputs, "outputs": r.outputs, "extra": r.extra} for r in runs],
        default=str,
    )
    assert "luma.job.agent" in names and "openai.responses.extraction" in names, names
    assert "DL-001" in exported and '"outcome": "done"' in exported
    assert "canaryTRACEPROOF" not in exported and "555 0199" not in exported and "5550199" not in exported
    assert observability.PHONE in exported and observability.SECRET in exported
    # A clarification reply may be queued locally; a quotation must never be sent.
    assert all(item["kind"] != "quotation" for item in get_detail(env, cid)["delivery"])
    Path(".local/trace-canary.json").write_text(
        json.dumps(
            {
                "trace_id": trace_id,
                "project": config.langsmith_project,
                "runs": len(runs),
                "run_names": sorted(names),
                "content_visible": True,
                "secret_and_phone_masked": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
