# Graph architecture — state, nodes, edges, routing

The MIS opinion on how to build a LangGraph `StateGraph`. Applies to vanilla graphs and to the inner graphs you may still build inside a Deep Agent.

## Mental model

A graph is a **typed state machine over an LLM**:

- **State** is the data the graph operates on, persisted at every step by the checkpointer.
- **Nodes** are pure functions `(state, ...) -> dict` that return updates to merge into state.
- **Edges** route execution between nodes — static (always go from A to B) or conditional (a function of state picks the next node).
- **Tools** are LLM-callable functions; the graph executes them via a tool node.
- **Subgraphs** are graphs invoked as nodes — used sparingly.

The compiled graph is the unit of deployment. `langgraph.json` lists one entry per graph.

## State design

### Typed state

Use a `TypedDict` for ergonomic state, Pydantic when you need runtime validation.

```python
"""State and routing types for the email_assistant graph."""
from typing import Annotated, Literal, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Working state for the email assistant graph."""
    messages: Annotated[list[AnyMessage], add_messages]
    triage_decision: Literal["respond", "ignore", "notify"] | None
    inbound_email_id: str
    draft: str | None
```

### Reducers

Replacement is the default. Accumulating fields **must** declare a reducer via `Annotated[T, reducer]`:

- `add_messages` for message lists — handles ids + deduping.
- `operator.add` for plain lists you want to extend.
- Custom: any callable `(old, new) -> merged`.

### Keep state minimal

- Only what nodes need to read or update.
- No raw API responses — parse them in the node and put the parsed shape in state.
- No big blobs (full email bodies, full document content). Use the virtual filesystem (deep agents) or a key-value store, and put the *reference* in state.
- No secrets. They live in `configuration` (LangGraph's `configurable`) or env vars.

### Configuration vs state

- **State** changes every step. Persisted by the checkpointer.
- **Configuration** is set when the graph is invoked and stays constant for the run (user id, tenant, model overrides, feature flags). Access via `RunnableConfig` / `configurable`.

```python
async def my_node(state: AgentState, config: RunnableConfig) -> dict:
    tenant_id = config["configurable"]["tenant_id"]
    # ...
```

## Nodes

### Pure functions of state

```python
async def triage_email(state: AgentState) -> dict:
    """Decide whether to respond, ignore, or notify on the inbound email."""
    decision = await call_structured_llm(TRIAGE_PROMPT, state["messages"][-1])
    return {"triage_decision": decision.kind}
```

Rules:

- **Return only the keys you change.** LangGraph merges the dict into state.
- **One concern per node.** If a node fetches data AND decides, split it.
- **I/O goes through `services/` or tool nodes**, not raw `requests`/`httpx` inside reasoning nodes.
- **Async first** for any node that touches the network or an LLM.

### Node naming

`snake_case` verb + (optional) object: `triage_email`, `draft_reply`, `route_after_tools`, `compress_history`.

### Where nodes live

`src/<agent>/nodes/<file>.py`. Re-export from `nodes/__init__.py` so `graph_builder.py` reads cleanly. Group related nodes per file:

```
nodes/
├── __init__.py     # re-exports
├── agent.py        # LLM call / reasoning nodes
├── tools.py        # tool execution node(s)
├── routing.py      # conditional routing functions
├── interrupts.py   # HITL handlers
└── <domain>.py     # domain-specific nodes (triage, draft, summarise, …)
```

## Edges

Three kinds:

| Edge kind            | When to use                                              | Lives in              |
|----------------------|----------------------------------------------------------|-----------------------|
| Static `add_edge`    | Unconditional transition (`triage` → `route`)            | `graph_builder.py`    |
| Conditional `add_conditional_edges` | Branching based on state | `graph_builder.py` + routing fn in `nodes/routing.py` |
| Implicit (END)       | Return `END` from a routing function to terminate        | inline in the routing fn |

Rules:

- **No more than one conditional edge per node.** If you need a second, the node is doing two jobs.
- **Routing functions are not compute nodes.** They live in `nodes/routing.py`, return a `Literal[...]` of next-node names, and have no side effects.
- **Edge wiring lives only in `graph_builder.py`.** Don't sprinkle `add_edge` calls across files.

## Routing patterns

### Match on a discriminator

```python
def route_after_triage(state: AgentState) -> Literal["draft", "notify", "__end__"]:
    """Pick the next branch from the triage decision."""
    match state["triage_decision"]:
        case "respond": return "draft"
        case "notify":  return "notify"
        case "ignore":  return "__end__"
        case None:
            raise ValueError("triage_decision must be set before routing")
```

The discriminator is a typed `Literal` field on the state — never a stringy `if "respond" in state["messages"][-1].content`.

### Tool loop

The standard ReAct loop:

```
agent  →  tools  →  agent  →  tools  →  …  →  END
        ↑___________|
```

Routing: after `agent`, if the last message has tool calls, go to `tools`; otherwise `END`.

```python
def route_after_agent(state: AgentState) -> Literal["tools", "__end__"]:
    """If the LLM asked for tools, run them; otherwise stop."""
    return "tools" if state["messages"][-1].tool_calls else "__end__"
```

### Fan-out (`Send` API)

Use `Send` to dispatch the same node to a list of inputs in parallel:

```python
from langgraph.types import Send

def fan_out_per_recipient(state: AgentState) -> list[Send]:
    """Spawn one draft branch per recipient."""
    return [Send("draft_for_recipient", {"recipient": r}) for r in state["recipients"]]
```

Useful for parallel research, per-item processing, etc. For Deep Agents, prefer the `task` subagent tool — it gives you context isolation that `Send` does not.

## Graph construction

All wiring in `graph_builder.py`:

```python
"""Compose the email_assistant graph: triage → branch → (draft|notify) → END."""
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from <agent>.schemas.states import AgentState
from <agent>.nodes import triage_email, draft_reply, notify_user, run_tools, agent_step
from <agent>.nodes.routing import route_after_triage, route_after_agent

def build_graph():
    """Build and compile the email_assistant graph."""
    g = StateGraph(AgentState)

    g.add_node("triage", triage_email)
    g.add_node("agent",  agent_step)
    g.add_node("tools",  run_tools)
    g.add_node("notify", notify_user)

    g.set_entry_point("triage")
    g.add_conditional_edges("triage", route_after_triage, {
        "draft":  "agent",
        "notify": "notify",
        "__end__": END,
    })
    g.add_conditional_edges("agent", route_after_agent, {
        "tools":   "tools",
        "__end__": END,
    })
    g.add_edge("tools", "agent")
    g.add_edge("notify", END)

    return g.compile(checkpointer=MemorySaver())
```

Rules:

- **One `build_graph()` per agent.** Returns a compiled graph.
- **Checkpointer is selected at build time.** `MemorySaver` for dev/tests, Postgres/SQLite for production. Selection lives in `graph_factory.py` (optional helper) — not scattered.
- **Read the wiring out loud.** If you can't explain the graph in one paragraph, simplify.

## Checkpointers

| Checkpointer              | Use for                                          |
|---------------------------|--------------------------------------------------|
| `MemorySaver`             | Tests, dev, ephemeral demos                      |
| `SqliteSaver`             | Local dev with persistence, single-process apps  |
| `PostgresSaver` (+ pgvector) | Production multi-tenant deployments           |
| LangGraph Platform        | Managed deploy; checkpointer is automatic        |

Rules:

- Pick at **build time** based on env (`MIS_CHECKPOINTER=postgres|sqlite|memory`).
- Schema migrations live alongside the deploy, not inside the agent package.
- Threads are addressed by a `thread_id` in `configurable`. Generate one per user-conversation; never reuse across users.

## Subgraphs — use sparingly

A subgraph is a compiled graph used as a node in another graph. They're powerful but easy to overuse.

Use a subgraph when:

- The work is itself a multi-step state machine with its own checkpoint cadence.
- The work is reusable across multiple parent graphs.

Don't use a subgraph when:

- You just want to group nodes. Use functions or a python module.
- You want context isolation. Use Deep Agents' `task` subagent — it's purpose-built for it.

## Streaming

LangGraph supports three stream modes — pick deliberately:

| Mode      | What you see                                          | Use for                          |
|-----------|-------------------------------------------------------|----------------------------------|
| `values`  | Full state after each step                            | UI that re-renders on each step  |
| `updates` | The dict each node returned                           | Compact UI / logs                |
| `messages`| Token-by-token LLM stream                             | Chat UIs                         |

The three can be combined. The frontend (langgraph-sdk) consumes them via `useStream`.

## Errors and retries

- **Node errors propagate.** Don't swallow exceptions inside nodes to "be nice" — the checkpoint captures the failure and the run can be resumed.
- **Retries on transient failures** are configured on the tool / service layer, not at the node level.
- **Tool errors are surfaced to the LLM as observations.** The agent re-plans; a code-level exception bubbles up.

## Inspectability

A good graph is easy to inspect:

- Every node logs its inputs / outputs via the LangSmith trace (enabled by default if `LANGCHAIN_TRACING_V2=true`).
- Routing decisions are derived from typed state fields, not opaque LLM output, so traces show the discriminator.
- The compiled graph's `get_graph().draw_mermaid()` produces a Mermaid diagram. Keep one in `docs/ARCHITECTURE.md`.
