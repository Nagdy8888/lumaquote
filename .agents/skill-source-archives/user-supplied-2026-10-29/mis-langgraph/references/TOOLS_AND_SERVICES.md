# Tools and services

The two layers that connect an agent to the outside world: **services** (reusable API code) and **tools** (LLM-callable functions). Get the boundary right and tools stay thin, services stay testable, and agents stay portable.

## Services

A **service** is reusable integration code. It does NOT know about LangGraph.

```
src/services/<service>/
├── __init__.py
├── client.py        # API wrapper (auth + fetch + send)
├── settings.py      # env vars, base URLs, scopes
├── prompts.py       # optional — only if every consumer uses the same prompt verbatim
├── tools.py         # OPTIONAL — @tool wrappers if every agent uses them identically
└── scripts/         # one-off CLI scripts (OAuth setup, manual ingest)
```

Rules:

- **No imports from `src/<agent>/`.** Services never depend on agents.
- **No `@tool` decoration in `client.py`.** That belongs in `tools.py` (only if every consumer uses it identically) or in each agent's `tools/`.
- **One service per integration.** Gmail, Slack, Stripe, Google Calendar, internal-API-X, …
- **Auth lives in `client.py`** behind a single class (`GmailClient`, `SlackClient`). Refresh logic, retries, rate-limit handling — all here.
- **Settings come from env vars via `settings.py`** (a Pydantic settings model or simple dataclass). No `os.getenv` scattered through `client.py`.

### Client pattern

```python
"""Gmail API client — handles OAuth, fetch, send, label, delete."""
from dataclasses import dataclass
from .settings import GmailSettings

@dataclass
class GmailClient:
    """Wraps the Gmail HTTP API with auth + retry."""
    settings: GmailSettings

    def send(self, to: str, subject: str, body: str) -> str:
        """Send an email. Returns the sent message id."""
        ...

    def list_inbox(self, limit: int = 20) -> list[Email]:
        """List the most recent inbox messages."""
        ...
```

### When a service has its own `tools.py`

Only when **every agent** that uses this service uses these tools identically. If two agents want different behaviour (different argument shapes, different return formats), keep the tool in the agent's `tools/` folder.

A typical service has **no** `tools.py` — the wrapping lives per-agent.

## Tools (agent-side)

A **tool** is an `@tool`-decorated function the LLM may call. Tools live in **each agent's** `tools/` folder.

```
src/<agent>/tools/
├── __init__.py
├── base.py          # get_tools() + approval wrapping
├── approval.py      # add_approval helper
└── <tool>.py        # one tool (or a small cluster of related tools) per file
```

### Tool file pattern

```python
"""Send an email via the Gmail service. Wrapped with approval in production."""
from langchain_core.tools import tool
from services.gmail.client import GmailClient
from <agent>.settings import settings

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to the recipient.

    Args:
        to: recipient email address (validated upstream)
        subject: subject line; ≤ 200 chars
        body: plain-text body

    Returns:
        the sent message id

    Raises:
        GmailError: if the API rejects the request
    """
    return GmailClient(settings.gmail).send(to=to, subject=subject, body=body)
```

Rules:

- **One tool per file** (or one small cluster of clearly-related tools).
- **The docstring is the LLM's source of truth.** Write it for the model, not just for humans — describe args, returns, error conditions, and any constraints the model needs to respect.
- **Type every argument and the return.** The tool schema is derived from these.
- **Validate at the boundary.** Anything questionable (long strings, structured payloads) is parsed against a Pydantic model before the side effect.
- **Don't catch exceptions to hide them.** A tool that swallows errors leaves the agent unable to course-correct.
- **No `print`, no `logger.info` for telemetry inside a tool body** — use the LangSmith trace; the call is already captured.

### Approval wrapping

Side-effecting tools (any tool that mutates the world) are wrapped with `add_approval`. The wrap pauses execution; a human approves, edits the args, or rejects.

```python
"""Approval helper: wraps a tool so its call is gated on human approval."""
from langchain_core.tools import BaseTool
from langgraph.types import interrupt

def add_approval(tool: BaseTool) -> BaseTool:
    """Wrap `tool` so it pauses for human approval before executing."""
    original = tool.func

    def wrapped(*args, **kwargs):
        decision = interrupt({"tool": tool.name, "args": kwargs})
        if decision.get("approved"):
            return original(*args, **{**kwargs, **decision.get("edits", {})})
        return f"REJECTED by human: {decision.get('reason', 'no reason given')}"

    tool.func = wrapped
    return tool
```

### Tool assembly (`tools/base.py`)

```python
"""Tool assembly for the email_assistant agent."""
from <agent>.tools.approval import add_approval
from <agent>.tools.send_email   import send_email
from <agent>.tools.read_inbox   import read_inbox
from <agent>.tools.delete_email import delete_email
from <agent>.tools.search_inbox import search_inbox

NEEDS_APPROVAL: frozenset[str] = frozenset({"send_email", "delete_email"})

def get_tools(dev_mode: bool = False) -> tuple[list, dict]:
    """Assemble the agent's tools; wrap side-effecting ones with approval outside dev mode.

    Args:
        dev_mode: if True, approval is skipped (fast iteration).

    Returns:
        tuple of (tools_list, tools_by_name_dict)
    """
    tools = [send_email, read_inbox, delete_email, search_inbox]
    if not dev_mode:
        tools = [add_approval(t) if t.name in NEEDS_APPROVAL else t for t in tools]
    return tools, {t.name: t for t in tools}
```

Rules:

- **One `get_tools(dev_mode)` per agent.** It's the single source of truth for the tool set.
- **`NEEDS_APPROVAL` is a `frozenset` at module level** — easy to grep, easy to audit, no surprises.
- **`dev_mode` is a runtime flag**, set from env / settings — not a code branch left in `main`.

## Services vs tools — the boundary

| Question                                                | Where it lives          |
|---------------------------------------------------------|-------------------------|
| Authenticating to an API                                | `services/<name>/client.py` |
| Parsing an API response into a typed shape              | `services/<name>/client.py` |
| Retrying on a 429                                       | `services/<name>/client.py` |
| Deciding when to call the API                           | An agent's `nodes/`     |
| Exposing the API to an LLM                              | An agent's `tools/`     |
| The tool's docstring (what the LLM reads)               | The `@tool` in the agent's `tools/` |
| Wrapping a call with approval                           | An agent's `tools/base.py` |
| One-off CLI to set up the integration (OAuth, ingest)   | `services/<name>/scripts/` |

## Deep Agents — when `interrupt_on` replaces `add_approval`

If you're using the Deep Agents harness, you have **two** ways to gate side-effecting tools:

1. `add_approval(tool)` wrap at assembly time (vanilla LangGraph pattern).
2. `interrupt_on={"send_email": True, ...}` passed to `create_deep_agent(...)`.

**Prefer `interrupt_on`** for deep agents — it consolidates the gating config in one place and the harness handles the resume-from-interrupt mechanics.

`add_approval` is still useful when:

- You want approval logic that does more than "approve / reject" (e.g. complex argument editing).
- You're embedding a sub-graph that isn't using the deep-agents harness.

Don't combine both on the same tool — pick one.

## Testing tools and services

| Layer       | What to mock                                              | Where                          |
|-------------|-----------------------------------------------------------|--------------------------------|
| Service     | The HTTP layer (`respx`, `httpx_mock`, recorded fixtures) | `tests/unit/test_<service>.py` |
| Tool        | The service client (`MagicMock`, `unittest.mock`)         | `tests/unit/test_<agent>_tools.py` |
| End-to-end  | Nothing — run against a staging account                   | `tests/integration/`           |

A tool's unit test should:

1. Call the tool with realistic args.
2. Assert the service client was called with the expected shape.
3. NOT hit the real API.

A service's unit test should:

1. Call the client method.
2. Mock the HTTP layer to return realistic responses (success, 4xx, 5xx, malformed).
3. Assert parsing, retry, and error mapping.

Integration tests for tools / services run against a **dedicated staging account** with disposable data. They live in `tests/integration/`, are tagged `live`, and are excluded from default CI.

## Anti-patterns

- An `@tool` defined in `services/` that calls into an agent's settings. Tools are agent-side.
- An agent reaching into `services/<name>/_internal/...`. Services have a public surface; respect it.
- A tool that wraps a side effect without `@tool`'s docstring describing the side effect. The model needs to know.
- Sharing a `tools/` folder across agents. Tools are per-agent; share the service underneath.
- Catching every exception in a tool to "be safe". The LLM has to see the failure to recover.
- Putting `NEEDS_APPROVAL` in a global config file. It's per-agent — keep it next to `get_tools()`.
