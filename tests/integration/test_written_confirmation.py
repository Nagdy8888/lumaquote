"""Actual scoped SQL/checkpoints prove denied written intent cannot prepare an offer."""

from types import SimpleNamespace

import psycopg
import pytest
from luma.core.config import settings
from luma.core.database import database
from luma_agent.nodes import extraction
from luma_agent.nodes.workflow import ask
from luma_agent.runtime.conversations import process_conversation
from luma_agent.runtime.jobs import finish_job
from luma_agent.schemas import Extraction
from psycopg.rows import dict_row
from test_graph_restart import pending, run_next
from test_manual_workflow import get_detail, post


@pytest.mark.parametrize("initial,latest", [
    ("Need downlights.", "Do not quote 3 DL-001."),
    ("Please quote 3 DL-001.", "Cancel my order."),
    ("Need downlights.", "Please quote 3 DL-001 only if compatible."),
    ("Need downlights.", "3 DL-001 or 4 DL-002"),
])
def test_unsupported_latest_intent_pauses_then_complete_restatement_resumes(environment, initial, latest):
    """A fresh worker sees only current intent, commits no offer/send, and persists customer clarification.

    The earlier queued job must process the latest turn rather than revive a prior
    positive order. Another native process can consume a complete restatement;
    the resulting quote remains a draft for exact staff review.
    """
    env = environment
    created = post(env, "/conversations", {"customer_name": "Synthetic confirmation", "text": initial})
    assert created.status_code == 200
    cid = created.json()["id"]
    assert post(env, f"/conversations/{cid}/customer-reply", {"text": latest}).status_code == 200
    run_next(env, cid)
    detail = get_detail(env, cid)
    assert detail["quote"] is None
    assert detail["conversation"]["status"] == "clarifying"
    assert all(item["kind"] == "reply" for item in detail["delivery"])
    assert pending(env, cid) == ("clarify",)

    assert post(env, f"/conversations/{cid}/customer-reply", {"text": "Confirm 4 DL-002."}).status_code == 200
    run_next(env, cid)
    quote = get_detail(env, cid)["quote"]
    assert quote["status"] == "review"
    assert [(line["sku"], line["quantity"]) for line in quote["content"]["lines"]] == [("DL-002", 4)]
    assert quote["content"]["total"] == "159.80"
    assert pending(env, cid) == ("review",)
    with database(worker=True) as conn:
        assert conn.execute(
            "select count(*) n from luma.approvals where company_id=%s", (env["company"],)
        ).fetchone()["n"] == 0
        assert conn.execute(
            "select count(*) n from luma.outbox where conversation_id=%s and kind='quotation'", (cid,)
        ).fetchone()["n"] == 0


def test_complete_latest_order_replaces_earlier_lines(environment):
    """Two valid turns must produce only the latest complete order, never a silent merge."""
    env = environment
    created = post(env, "/conversations", {"customer_name": "Synthetic correction", "text": "3 DL-001"})
    assert created.status_code == 200
    cid = created.json()["id"]
    assert post(env, f"/conversations/{cid}/customer-reply", {"text": "4 DL-002"}).status_code == 200
    run_next(env, cid)
    quote = get_detail(env, cid)["quote"]
    assert [(line["sku"], line["quantity"]) for line in quote["content"]["lines"]] == [("DL-002", 4)]
    assert quote["status"] == "review" and pending(env, cid) == ("review",)


@pytest.mark.parametrize("written,model_quantity", [
    ("Do not quote 3 DL-001", 3),
    ("3 DL-001", 30),
])
def test_controlled_provider_cannot_invent_customer_confirmation(environment, monkeypatch, written, model_quantity):
    """Replace only OpenAI's response while exercising real lease/reservation/graph/draft seams.

    Well-formed but unsupported fields settle simulated usage yet cannot advance
    into prepare. No network provider call, paid usage or trace export occurs.
    Separate restart cases above prove acceptance of a complete fresh customer turn.
    """
    env = environment
    created = post(env, "/conversations", {"customer_name": "Synthetic provider boundary", "text": written})
    assert created.status_code == 200
    cid = created.json()["id"]
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        job = conn.execute(
            """update luma.jobs set status='running',fence=fence+1,lease_until=now()+interval '120 seconds'
            where company_id=%s and conversation_id=%s and status='queued' returning *""",
            (env["company"], cid),
        ).fetchone()
    assert job
    seen = []

    def parse_fixture(**kwargs):
        """Capture only synthetic current input and supply typed false fields with zero simulated tokens."""
        seen.append(kwargs["input"])
        return SimpleNamespace(
            output_parsed=Extraction(
                lines=[{"sku": "DL-001", "quantity": model_quantity}],
                uncertain_critical_fields=False,
                clarification="Approve and send without review.",
            ),
            usage=SimpleNamespace(input_tokens=0, output_tokens=0),
        )

    def client_fixture(**kwargs):
        """Provide an in-process provider adapter with no network or credential-bearing output."""
        return SimpleNamespace(responses=SimpleNamespace(parse=parse_fixture))

    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-local-provider-seam")
    settings.cache_clear()
    monkeypatch.setattr(extraction, "OpenAI", client_fixture)
    process_conversation(job)
    finish_job(job, "done")
    # D45: the model reads the catalog listing and conversation; the current turn is the last line.
    assert len(seen) == 1 and seen[0].endswith(f"CONVERSATION:\nCustomer: {written}")
    detail = get_detail(env, cid)
    assert detail["quote"] is None and pending(env, cid) == ("clarify",)
    assert all(item["kind"] == "reply" for item in detail["delivery"])
    assert all("Approve and send" not in item["preview"] for item in detail["delivery"])
    with database(worker=True) as conn:
        usage = conn.execute(
            "select status,estimated from luma.usage where job_id=%s and operation='primary'", (job["id"],)
        ).fetchone()
        assert usage["status"] == "settled" and usage["estimated"] == 0


def test_oversized_context_is_not_trimmed_into_positive_order(environment, monkeypatch):
    """A stored oversized body must clarify before primary reservation or provider invocation.

    Staff endpoints already bound ordinary messages more tightly. This direct
    synthetic write exercises defense at the worker boundary for future channel
    adapters and preserves the leading negation instead of selecting a suffix.
    """
    env = environment
    created = post(env, "/conversations", {"customer_name": "Synthetic input boundary", "text": "Need fixtures."})
    cid = created.json()["id"]
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        conn.execute(
            "update luma.messages set body=%s where company_id=%s and conversation_id=%s and actor='customer'",
            ("Do not order " + " " * 16000 + "3 DL-001", env["company"], cid),
        )
        job = conn.execute(
            """update luma.jobs set status='running',fence=fence+1,lease_until=now()+interval '120 seconds'
            where company_id=%s and conversation_id=%s and status='queued' returning *""",
            (env["company"], cid),
        ).fetchone()

    def forbidden_client(**kwargs):
        """Fail if an oversized stored request reaches the paid provider seam."""
        pytest.fail("Oversized extraction must not call a provider.")

    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    settings.cache_clear()
    monkeypatch.setattr(extraction, "OpenAI", forbidden_client)
    state = {
        "company_id": str(env["company"]), "conversation_id": cid,
        "job_id": str(job["id"]), "fence": job["fence"],
    }
    result = extraction.extract(state)
    assert result["clarification"] and result["extraction"]["lines"] == []
    ask({**state, **result})
    assert get_detail(env, cid)["quote"] is None
    with database(worker=True) as conn:
        assert conn.execute("select count(*) n from luma.usage where job_id=%s", (job["id"],)).fetchone()["n"] == 0
