"""Paid conversational brain (D45) through the real lease, reservation, graph and draft seams.

Only OpenAI's response is replaced by an in-process fixture; no network call, paid usage or
trace export occurs. These prove that model output can phrase replies and propose an order but
cannot confirm one: only a deterministic YES that directly answers the restatement does.
Label: local-substitute.
"""

from types import SimpleNamespace

import psycopg
import pytest
from luma.core.config import settings
from luma_agent.nodes import extraction
from luma_agent.runtime.conversations import process_conversation
from luma_agent.runtime.delivery import deliver_one
from luma_agent.runtime.jobs import finish_job
from luma_agent.schemas import Extraction
from psycopg.rows import dict_row
from test_graph_restart import pending
from test_manual_workflow import get_detail, post


@pytest.fixture
def brain(monkeypatch):
    """Enable paid AI against a scripted provider; `brain.replies` queues outputs, `brain.calls` records inputs."""
    state = SimpleNamespace(replies=[], calls=[])

    def parse_fixture(**kwargs):
        """Return the next scripted typed output with zero simulated tokens; fail when none is queued."""
        state.calls.append(kwargs["input"])
        if not state.replies:
            pytest.fail("The model must not be called for this turn.")
        return SimpleNamespace(output_parsed=state.replies.pop(0), usage=SimpleNamespace(input_tokens=0, output_tokens=0))

    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-local-provider-seam")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    settings.cache_clear()
    monkeypatch.setattr(extraction, "OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse_fixture)))
    yield state
    settings.cache_clear()


def turn(lines, reply, uncertain=False):
    """Build one scripted model output; `lines` are (sku, quantity) pairs."""
    return Extraction(
        lines=[{"sku": sku, "quantity": quantity} for sku, quantity in lines],
        clarification=reply,
        uncertain_critical_fields=uncertain,
    )


def run(env, cid):
    """Lease this conversation's oldest queued job and process it in-process with the scripted provider."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        job = conn.execute(
            """update luma.jobs set status='running',fence=fence+1,attempts=attempts+1,
            lease_until=now()+interval '120 seconds'
            where id=(select id from luma.jobs where company_id=%s and conversation_id=%s
            and status='queued' order by created_at limit 1) returning *""",
            (env["company"], cid),
        ).fetchone()
    assert job
    process_conversation(job)
    finish_job(job, "done")


def start(env, text):
    """Create a staff-entered customer request and return its conversation id."""
    created = post(env, "/conversations", {"customer_name": "Synthetic brain", "text": text})
    assert created.status_code == 200
    return created.json()["id"]


def reply_texts(env, cid):
    """Return the reply previews oldest first (the detail endpoint lists newest first)."""
    return [item["preview"] for item in reversed(get_detail(env, cid)["delivery"]) if item["kind"] == "reply"]


def test_free_wording_is_restated_then_yes_prepares_review(environment, brain):
    """'i want 5 dl-001' gets the model's reply plus a code-built restatement; YES prepares without a model call."""
    env = environment
    cid = start(env, "i want 5 dl-001")
    brain.replies.append(turn([("DL-001", 5)], "Sure, DL-001 is our 18W downlight."))
    run(env, cid)
    replies = reply_texts(env, cid)
    assert "Sure, DL-001 is our 18W downlight." in replies[-1]
    assert "To confirm, your order is: 5 x DL-001. Reply YES to confirm" in replies[-1]
    assert get_detail(env, cid)["quote"] is None and pending(env, cid) == ("clarify",)
    assert post(env, f"/conversations/{cid}/customer-reply", {"text": "Yes"}).status_code == 200
    run(env, cid)
    assert len(brain.calls) == 1
    quote = get_detail(env, cid)["quote"]
    assert [(line["sku"], line["quantity"]) for line in quote["content"]["lines"]] == [("DL-001", 5)]
    assert quote["status"] == "review" and pending(env, cid) == ("review",)


def test_yes_after_a_newer_change_does_not_confirm_the_old_order(environment, brain):
    """A YES that follows another customer message is not an answer to the restatement."""
    env = environment
    cid = start(env, "i want 5 dl-001")
    brain.replies.append(turn([("DL-001", 5)], None))
    run(env, cid)
    assert post(env, f"/conversations/{cid}/customer-reply", {"text": "actually make it ten"}).status_code == 200
    assert post(env, f"/conversations/{cid}/customer-reply", {"text": "yes"}).status_code == 200
    brain.replies.append(turn([("DL-001", 10)], None))
    run(env, cid)
    assert len(brain.calls) == 2
    assert get_detail(env, cid)["quote"] is None
    assert "10 x DL-001" in reply_texts(env, cid)[-1]


def test_written_order_matching_the_model_prepares_directly(environment, brain):
    """An exact written order that the model reads the same way needs no YES (D20 path kept)."""
    env = environment
    cid = start(env, "Please quote 4 DL-002")
    brain.replies.append(turn([("DL-002", 4)], "Thanks!"))
    run(env, cid)
    quote = get_detail(env, cid)["quote"]
    assert [(line["sku"], line["quantity"]) for line in quote["content"]["lines"]] == [("DL-002", 4)]


def test_written_pairs_win_over_a_different_model_reading(environment, brain):
    """When the model misreads a written order, the restatement shows the customer's own pairs."""
    env = environment
    cid = start(env, "3 DL-001")
    brain.replies.append(turn([("DL-001", 30)], None))
    run(env, cid)
    assert get_detail(env, cid)["quote"] is None
    assert "To confirm, your order is: 3 x DL-001." in reply_texts(env, cid)[-1]


@pytest.mark.parametrize("unsafe", [
    "DL-001 costs $20 each.",
    "We can give you a 10% discount.",
    "Your quotation is approved.",
    "See https://example.invalid/offer",
])
def test_unsafe_model_reply_is_replaced_by_the_fixed_question(environment, brain, unsafe):
    """Money, percentages, links and approval claims never reach the customer."""
    env = environment
    cid = start(env, "how much are your downlights?")
    brain.replies.append(turn([], unsafe, uncertain=True))
    run(env, cid)
    assert reply_texts(env, cid)[-1] == "Please confirm each product SKU and quantity, for example: 3 DL-001."


def test_unknown_sku_is_not_restated_and_yes_then_asks_the_model(environment, brain):
    """A SKU outside the current catalog gets a fixed reply and leaves nothing for YES to confirm."""
    env = environment
    cid = start(env, "i want 2 zz-999")
    brain.replies.append(turn([("ZZ-999", 2)], "Sure."))
    run(env, cid)
    assert reply_texts(env, cid)[-1] == "I could not find ZZ-999 in our current catalog. Please check the product code."
    assert post(env, f"/conversations/{cid}/customer-reply", {"text": "yes"}).status_code == 200
    brain.replies.append(turn([], "Which product do you need?", uncertain=True))
    run(env, cid)
    assert len(brain.calls) == 2 and get_detail(env, cid)["quote"] is None


def test_model_reads_conversation_and_catalog_without_prices(environment, brain):
    """The prompt carries earlier turns and catalog specifications, never prices or stock."""
    env = environment
    cid = start(env, "hello, I need downlights")
    brain.replies.append(turn([], "Which wattage do you need?", uncertain=True))
    run(env, cid)
    assert deliver_one(env["company"])  # local channel records the agent reply as a message
    assert post(env, f"/conversations/{cid}/customer-reply", {"text": "18W please"}).status_code == 200
    brain.replies.append(turn([], "How many?", uncertain=True))
    run(env, cid)
    prompt = brain.calls[-1]
    assert "Customer: hello, I need downlights" in prompt and "Agent: Which wattage do you need?" in prompt
    assert prompt.endswith("Customer: 18W please")
    assert "DL-001 | Synthetic downlight | 18W" in prompt
    assert "price" not in prompt.lower() and "stock" not in prompt.lower()
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        rows = conn.execute(
            "select distinct price::text p from luma.products where company_id=%s", (env["company"],)
        ).fetchall()
    assert rows and all(row["p"] not in prompt for row in rows)
