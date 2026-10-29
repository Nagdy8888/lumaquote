# Testing — unit, integration, notebooks

Three test surfaces, each with a clear job. Notebooks are for humans; CI runs unit + integration only.

```
tests/
├── unit/                       # Fast, isolated, no network
│   ├── test_<agent>_nodes.py
│   ├── test_<agent>_tools.py
│   ├── test_<agent>_routing.py
│   └── test_<service>_client.py
├── integration/                # Compiled graph end-to-end, network ok
│   ├── test_<agent>_graph.py
│   └── test_<service>_live.py  # marked `live`, excluded by default
└── notebooks/                  # Interactive — for debugging, NOT in CI
    ├── test_<agent>_walkthrough.ipynb
    ├── test_memory_live.ipynb
    └── test_tools_live.ipynb
```

## Unit tests (`tests/unit/`)

Fast, isolated, **no network**. Every PR that changes a node, tool, routing function, or service must add or update at least one unit test here.

### Testing a node

```python
"""Unit tests for the triage_email node."""
import pytest
from unittest.mock import AsyncMock, patch

from <agent>.nodes.triage import triage_email

@pytest.mark.asyncio
async def test_triage_classifies_respond():
    """A clear question is classified as respond."""
    state = {"messages": [{"role": "user", "content": "Can you send me the report?"}]}

    with patch("<agent>.nodes.triage.call_structured_llm", new=AsyncMock(return_value=_decision("respond"))):
        out = await triage_email(state)

    assert out == {"triage_decision": "respond"}
```

Rules:

- **Patch the LLM call**, not the entire node. The node's *logic* is what you're testing.
- **One assert per scenario.** A test that asserts six things on one call is six tests pretending to be one.
- **Test names are sentences:** `test_triage_classifies_respond`, not `test_triage_1`.

### Testing a tool

```python
"""Unit tests for the send_email tool."""
from unittest.mock import MagicMock, patch
from <agent>.tools.send_email import send_email

def test_send_email_delegates_to_gmail_client():
    """The tool forwards args verbatim to GmailClient.send."""
    fake_client = MagicMock()
    fake_client.send.return_value = "msg-123"

    with patch("<agent>.tools.send_email.GmailClient", return_value=fake_client):
        result = send_email.invoke({"to": "a@b.com", "subject": "Hi", "body": "yo"})

    assert result == "msg-123"
    fake_client.send.assert_called_once_with(to="a@b.com", subject="Hi", body="yo")
```

### Testing routing

Routing functions are pure — easy to test exhaustively:

```python
"""Unit tests for route_after_triage."""
import pytest
from <agent>.nodes.routing import route_after_triage

@pytest.mark.parametrize("decision, expected", [
    ("respond", "draft"),
    ("notify",  "notify"),
    ("ignore",  "__end__"),
])
def test_route_after_triage(decision, expected):
    """Each triage decision maps to the documented branch."""
    assert route_after_triage({"triage_decision": decision}) == expected

def test_route_after_triage_rejects_unset():
    """A None decision raises — the routing function is total over the type."""
    with pytest.raises(ValueError):
        route_after_triage({"triage_decision": None})
```

### Testing a service

Mock the HTTP layer with `respx` or `httpx_mock`:

```python
"""Unit tests for GmailClient.send."""
import respx
from httpx import Response
from services.gmail.client import GmailClient
from services.gmail.settings import GmailSettings

@respx.mock
def test_send_posts_to_messages_endpoint():
    """send() POSTs to /users/me/messages/send with the expected payload."""
    route = respx.post("https://gmail.googleapis.com/.../messages/send").mock(
        return_value=Response(200, json={"id": "msg-123"}),
    )
    GmailClient(GmailSettings(...)).send(to="a@b.com", subject="hi", body="yo")
    assert route.called
```

## Integration tests (`tests/integration/`)

End-to-end runs of a **compiled graph**, exercising real routing, real state, real tool calls. The network is allowed; LLM calls and external APIs are mocked at the boundary (or replayed from recorded fixtures).

```python
"""Integration tests for the email_assistant graph."""
import pytest
from <agent>.graph_builder import build_graph

@pytest.mark.asyncio
async def test_respond_branch_drafts_reply(monkeypatch):
    """A 'respond' triage walks all the way to a drafted reply, no human input."""
    monkeypatch.setattr("<agent>.nodes.triage.call_structured_llm",
                        _stub_triage("respond"))
    monkeypatch.setattr("<agent>.nodes.agent.call_llm_with_tools",
                        _stub_agent_with_draft("Sure, here is the report…"))

    graph = build_graph()
    out = await graph.ainvoke({"messages": [_inbound("Can you send the report?")]},
                              config={"configurable": {"thread_id": "t-1"}})
    assert "Sure, here is the report" in out["draft"]
```

Rules:

- **Use the compiled graph, not the individual nodes.** This is what catches wiring bugs.
- **Mock at the *LLM* and *service-client* boundaries** — the rest of the graph runs for real.
- **One scenario per test** — `test_respond_branch_…`, `test_notify_branch_…`, `test_ignore_branch_…`.
- **Use unique `thread_id` per test** so checkpointers don't bleed.

### `live` tests

Tests that hit real APIs (Gmail, Slack, …) are tagged with `pytest.mark.live`:

```python
@pytest.mark.live
@pytest.mark.asyncio
async def test_send_email_to_staging_inbox():
    ...
```

Configure `pytest.ini`:

```ini
[pytest]
markers =
    live: hits real APIs; excluded from default CI
addopts = -m "not live"
```

Run live tests explicitly: `pytest -m live`. CI runs them only on a nightly job against staging.

## Notebooks (`tests/notebooks/`)

Notebooks are **debugging + onboarding aids**, not CI gates.

Use them for:

- Walking through an agent run step-by-step, inspecting state at each node.
- Probing the virtual filesystem after a deep agent run.
- Sanity-checking a new tool with realistic inputs.

Do **not** use them for:

- Regression tests. They go in `tests/unit/` or `tests/integration/`.
- Anything that needs to gate a merge.

A useful notebook starts with:

```python
# Cell 1 — load env, build agent
from dotenv import load_dotenv; load_dotenv()
from <agent>.graph_builder import build_graph
graph = build_graph()
```

…and then walks input → state at each step → output. Keep them runnable from a clean checkout.

## Test conventions

- **Async tests use `pytest-asyncio`** — `@pytest.mark.asyncio` on every async test.
- **Fixtures live in `tests/conftest.py`** at the relevant scope (root, per-directory).
- **No real LLM calls in unit / integration default CI.** Mock at the boundary.
- **Coverage gate: 80% line coverage** for `src/<agent>/` and `src/services/`. Enforced by CI.
- **No flaky tests.** A flaky integration test is treated as a bug — fix the determinism, don't `@pytest.mark.flaky` it.

## What CI runs

| Stage          | Command                              | Required? |
|----------------|--------------------------------------|-----------|
| Lint           | `ruff check .`                       | ✅        |
| Format check   | `ruff format --check .`              | ✅        |
| Type-check     | `mypy src`                           | ✅        |
| Unit tests     | `pytest tests/unit -q`               | ✅        |
| Integration    | `pytest tests/integration -q -m "not live"` | ✅ |
| Live (nightly) | `pytest tests/integration -m live`   | nightly only |
