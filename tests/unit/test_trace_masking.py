"""Decision D24 / rule R13: detailed LangSmith traces keep content but never secrets, phones or media bytes.

The capture tests use a real `langsmith.Client` with a fake HTTP session, so the assertions
inspect the exact request bodies that would be sent to LangSmith, including runs created by
LangGraph's own tracer.
"""

import json
import operator
from typing import Annotated, TypedDict

import pytest
import requests
from langgraph.graph import END, START, StateGraph
from langsmith import Client, get_tracing_context
from luma_agent import observability as obs

SECRET_CANARY = "sk-canaryABCDEFGHIJKLMNOPQRS"
PHONE_CANARY = "+20 100 555 0199"


class FakeSession(requests.Session):
    """Record request bodies instead of sending them, answering 200 to everything."""

    def __init__(self):
        """Start with an empty capture list."""
        super().__init__()
        self.bodies: list[str] = []

    def request(self, method, url, **kwargs):
        """Store the serialized payload and return an empty successful response."""
        data = kwargs.get("data") if kwargs.get("data") is not None else kwargs.get("json")
        self.bodies.append(
            data.decode("utf-8", "replace") if isinstance(data, bytes) else json.dumps(data, default=str)
        )
        response = requests.Response()
        response.status_code = 200
        response._content = b"{}"
        return response


@pytest.fixture
def captured(monkeypatch):
    """Enable tracing with a masked client whose HTTP traffic is captured locally."""
    session = FakeSession()
    client = Client(
        api_key="unit-test-key-0000",
        api_url="http://127.0.0.1:9",
        session=session,
        auto_batch_tracing=False,
        anonymizer=obs.mask,
        hide_inputs=obs.mask,
        hide_outputs=obs.mask,
        hide_metadata=obs.mask,
    )
    monkeypatch.setattr(obs, "tracing_enabled", lambda: True)
    monkeypatch.setattr(obs, "masked_client", lambda: client)
    monkeypatch.setattr(obs, "configured_secrets", lambda: ("configured-literal-secret-value",))
    return session


@pytest.mark.parametrize(
    "secret",
    [
        SECRET_CANARY,
        "lsv2_pt_0123456789abcdef0123456789",
        "EAAGm0PX4ZCpsBAJ0123456789abcdefABCD",
        "Bearer abcdefghijklmnop.qrstuvwx",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3OCJ9.c2lnbmF0dXJlLXZhbHVl",
        "sha256=" + "a" * 64,
        "https://x.supabase.co/storage/v1/object/sign/a.wav?token=abc.def.ghi",
        "configured-literal-secret-value",
    ],
)
def test_secrets_are_masked(monkeypatch, secret):
    """Known key formats, signatures, signed-URL tokens and configured literals never survive."""
    monkeypatch.setattr(obs, "configured_secrets", lambda: ("configured-literal-secret-value",))
    masked = obs.mask_text(f"before {secret} after")
    assert obs.SECRET in masked
    assert "abcdefghijklmnop" not in masked and "configured-literal" not in masked and "canary" not in masked


@pytest.mark.parametrize(
    "phone", [PHONE_CANARY, "+201005550199", "201005550199", "0100 555 0199", "010-555-0199"]
)
def test_phone_numbers_are_masked(monkeypatch, phone):
    """International, WhatsApp-id and common local phone forms become [phone]."""
    monkeypatch.setattr(obs, "configured_secrets", lambda: ())
    assert obs.mask_text(f"call {phone} please") == f"call {obs.PHONE} please"


def test_business_content_is_kept(monkeypatch):
    """SKUs, quantities, prices, dates, times and ids stay readable so traces are useful."""
    monkeypatch.setattr(obs, "configured_secrets", lambda: ())
    text = (
        "Please quote 120 OD-001 and 3 DL-001 for USD 97.05 by 2026-11-03 14:30, "
        "job 5f0c1d2e-3a4b-4c5d-8e9f-0a1b2c3d4e5f"
    )
    assert obs.mask_text(text) == text


def test_media_bytes_and_inline_data_are_omitted(monkeypatch):
    """Raw bytes and base64 data URLs are replaced by size notes, recursively."""
    monkeypatch.setattr(obs, "configured_secrets", lambda: ())
    masked = obs.mask({"file": ("a.wav", b"\x00" * 50), "image": "data:image/jpeg;base64,QUJDRA==", "n": 3})
    assert masked["file"] == ["a.wav", "[50 bytes omitted]"]
    assert masked["image"].startswith("[media omitted")
    assert masked["n"] == 3


class State(TypedDict):
    """Minimal graph state for the capture test."""

    text: str
    notes: Annotated[list[str], operator.add]


def test_job_trace_exports_graph_and_model_runs_masked(captured):
    """A job trace exports the root, LangGraph steps and model call with content, never canaries."""

    def node(state: State) -> dict:
        """Echo the customer text through a model-call span, as the extraction node does."""
        with (
            obs.masked_or_off(),
            obs.model_call("openai.responses.extraction", "gpt-6-luna", {"input": state["text"]}) as call,
        ):
            obs.set_outputs(
                call, {"parsed": {"lines": [{"sku": "OD-001", "quantity": 120}]}, "echo": state["text"]}
            )
        return {"notes": ["Please confirm 120 OD-001."]}

    builder = StateGraph(State)
    builder.add_node("extract", node)
    builder.add_edge(START, "extract")
    builder.add_edge("extract", END)
    graph = builder.compile()
    job = {
        "id": "00000000-0000-0000-0000-000000000001",
        "kind": "agent",
        "company_id": "c",
        "conversation_id": "v",
        "payload": {},
    }
    customer = f"Quote 120 OD-001. My number is {PHONE_CANARY}, key {SECRET_CANARY}, see configured-literal-secret-value"
    with obs.job_trace(job) as run:
        with obs.masked_or_off():
            graph.invoke({"text": customer, "notes": []})
        obs.finish(run, "done")
    obs.masked_client().flush()
    sent = "\n".join(captured.bodies)
    assert sent, "nothing was exported"
    for name in ("luma.job.agent", "extract", "openai.responses.extraction"):
        assert f'"name":"{name}"' in sent.replace(" ", ""), name
    assert "Quote 120 OD-001" in sent and "Please confirm 120 OD-001." in sent
    assert "canary" not in sent and "0199" not in sent and "configured-literal" not in sent
    assert obs.PHONE in sent and obs.SECRET in sent
    assert '"outcome":"done"' in sent.replace(" ", "")


def test_tracing_is_forced_off_outside_a_job_trace(captured, monkeypatch):
    """Direct calls (tests, harness, scripts) never export, even if the environment enables tracing."""
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    with obs.masked_or_off():
        assert get_tracing_context()["enabled"] is False
        with obs.model_call("openai.embeddings", "text-embedding-3-small", {"input": ["x"]}) as call:
            obs.set_outputs(call, {"vectors": 1})
    assert captured.bodies == []


def test_model_call_exports_tokens_and_estimated_cost(captured):
    """A model-call run carries token counts, an estimated USD cost and the provider/model for LangSmith."""
    job = {"id": "00000000-0000-0000-0000-000000000003", "kind": "agent", "company_id": "c"}
    with obs.job_trace(job) as run:
        with obs.model_call("openai.responses.extraction", "gpt-6-luna", {"input": "x"}) as call:
            obs.set_usage(
                call,
                input_tokens=1000,
                output_tokens=200,
                input_usd_per_million=0.10,
                output_usd_per_million=0.50,
            )
            obs.set_outputs(call, {"ok": True})
        obs.finish(run, "done")
    obs.masked_client().flush()
    sent = "\n".join(captured.bodies).replace(" ", "")
    assert '"input_tokens":1000' in sent and '"output_tokens":200' in sent and '"total_tokens":1200' in sent
    assert '"total_cost":0.0002' in sent
    assert '"ls_provider":"openai"' in sent and '"ls_model_name":"gpt-6-luna"' in sent


def test_set_usage_is_a_noop_without_a_run():
    """Tracing off yields no run; recording usage must not raise."""
    obs.set_usage(None, input_tokens=5)


def test_disabled_tracing_exports_nothing(monkeypatch):
    """With tracing off, job_trace yields None and forces the context off."""
    monkeypatch.setattr(obs, "tracing_enabled", lambda: False)
    with obs.job_trace({"id": "1", "kind": "agent"}) as run:
        assert run is None
        assert get_tracing_context()["enabled"] is False


def _job() -> dict:
    """Return a minimal worker job for the nested-leak probes below."""
    return {
        "id": "00000000-0000-0000-0000-000000000002",
        "kind": "agent",
        "company_id": "c",
        "conversation_id": "v",
    }


def _assert_no_canaries(sent: str) -> None:
    """Fail when any planted secret or phone fragment appears anywhere in the exported request bodies."""
    assert sent, "nothing was exported"
    for leaked in ("canary", "0199", "configured-literal"):
        assert leaked not in sent, f"{leaked!r} reached the exporter"


def test_nested_tool_and_subgraph_runs_are_masked(captured):
    """Canaries in a traceable tool, a nested subgraph and deep payloads never reach the exporter."""
    from langsmith import traceable

    @traceable(run_type="tool", name="lookup_tool")
    def lookup_tool(query: str, extra: dict) -> dict:
        """Echo the query and a nested payload like a catalog tool would."""
        return {"hits": [{"query": query, "deep": {"level": [extra]}}]}

    def inner(state: State) -> dict:
        """Subgraph node that calls the tool with canaries nested several levels deep."""
        lookup_tool(state["text"], {"a": {"b": [{"c": f"{SECRET_CANARY} {PHONE_CANARY}"}]}})
        return {"notes": [f"inner saw {PHONE_CANARY}"]}

    sub = StateGraph(State)
    sub.add_node("inner", inner)
    sub.add_edge(START, "inner")
    sub.add_edge("inner", END)
    outer = StateGraph(State)
    outer.add_node("sub", sub.compile())
    outer.add_edge(START, "sub")
    outer.add_edge("sub", END)
    graph = outer.compile()
    with obs.job_trace(_job()) as run:
        with obs.masked_or_off():
            graph.invoke({"text": f"order for {PHONE_CANARY} key {SECRET_CANARY}", "notes": []})
        obs.finish(run, "done")
    obs.masked_client().flush()
    sent = "\n".join(captured.bodies)
    _assert_no_canaries(sent)
    assert "lookup_tool" in sent and "inner" in sent


def test_exception_text_and_error_field_are_masked(captured):
    """A node that raises with canaries in its message exports neither the message nor the traceback unmasked."""

    def boom(state: State) -> dict:
        """Fail the way a provider or database error can, echoing request data in the message."""
        raise RuntimeError(
            f"provider rejected {SECRET_CANARY} for {PHONE_CANARY} configured-literal-secret-value"
        )

    builder = StateGraph(State)
    builder.add_node("boom", boom)
    builder.add_edge(START, "boom")
    builder.add_edge("boom", END)
    graph = builder.compile()
    with obs.job_trace(_job()) as run:
        try:
            with obs.masked_or_off():
                graph.invoke({"text": "x", "notes": []})
        except RuntimeError as failure:
            obs.finish(run, "failed", str(failure))
    obs.masked_client().flush()
    _assert_no_canaries("\n".join(captured.bodies))


def test_metadata_tags_and_job_payload_are_masked(captured):
    """Canaries in the job payload and in run metadata set by callers are masked like inputs."""
    job = {
        **_job(),
        "payload": {"from": PHONE_CANARY, "note": SECRET_CANARY, "nested": {"x": [PHONE_CANARY]}},
    }
    with obs.job_trace(job) as run:
        with obs.model_call("probe", "m", {"input": "hello", PHONE_CANARY: SECRET_CANARY}) as call:
            obs.set_outputs(call, {"ok": True})
        obs.finish(run, "done")
    obs.masked_client().flush()
    _assert_no_canaries("\n".join(captured.bodies))


def test_production_client_masks_every_exported_field(monkeypatch):
    """The real client factory must mask inputs, outputs, metadata and the error string, or the probes above prove nothing."""
    seen = {}
    monkeypatch.setattr(obs, "Client", lambda **options: seen.update(options) or object())
    obs.reset()
    try:
        obs.masked_client()
    finally:
        obs.reset()
    for option in ("anonymizer", "hide_inputs", "hide_outputs", "hide_metadata"):
        assert seen[option] is obs.mask, option
