# LangGraph Multi-Agent Project Structure

A blueprint for organizing scalable LangGraph applications with multiple extensive agents and shared services.

```
apps/agents/
│
├── langgraph.json              # LangGraph config: registers all agents (graphs)
├── pyproject.toml              # Python project metadata & dependencies
├── requirements.txt            # Pinned dependencies
├── Dockerfile                  # Container build for LangGraph Platform
├── .dockerignore
│
├── src/
│   │
│   ├── services/               # ── SHARED SERVICES (used across all agents) ──
│   │   ├── __init__.py
│   │   ├── base.py             # Base service class / shared utilities
│   │   ├── approval.py         # Human-in-the-loop approval logic
│   │   ├── encryption.py       # Encryption/decryption helpers
│   │   │
│   │   ├── gmail/              # Gmail integration service
│   │   │   ├── __init__.py
│   │   │   ├── client.py       # Gmail API client (auth, fetch, send)
│   │   │   ├── settings.py     # Gmail-specific settings
│   │   │   ├── prompts.py      # Gmail-related prompt templates
│   │   │   ├── tools.py        # Gmail tools (exposed to agents)
│   │   │   └── scripts/        # Standalone utility scripts
│   │   │       ├── setup_gmail.py   # One-time OAuth setup
│   │   │       └── run_ingest.py    # Manual ingestion script
│   │   │
│   │   ├── slack/              # Slack integration service
│   │   │   ├── __init__.py
│   │   │   ├── client.py       # Slack API client
│   │   │   ├── settings.py     # Slack-specific settings
│   │   │   └── tools.py        # Slack tools (exposed to agents)
│   │   │
│   │   └── <new_service>/      # Add new integrations here (calendar, etc.)
│   │       ├── __init__.py
│   │       ├── client.py
│   │       ├── settings.py
│   │       └── tools.py
│   │
│   │
│   ├── <agent_name>/           # ── PER-AGENT PACKAGE (one per graph) ──
│   │   ├── __init__.py
│   │   ├── <agent_name>.py     # Graph entry point (compiled graph export)
│   │   ├── graph_builder.py    # Graph construction (nodes, edges, conditionals)
│   │   ├── graph_factory.py    # Factory for graph initialization (optional)
│   │   ├── configuration.py    # Runtime configuration (LangGraph configurable)
│   │   ├── settings.py         # Agent-level env vars and settings
│   │   ├── rules.py            # Business rules / heuristics (optional)
│   │   ├── utils.py            # Agent-specific utilities
│   │   │
│   │   ├── nodes/              # ── Graph Nodes ──
│   │   │   ├── __init__.py     # Re-export all node functions
│   │   │   ├── agent.py        # LLM call / reasoning node
│   │   │   ├── routing.py      # Conditional routing logic
│   │   │   ├── tools.py        # Tool execution node
│   │   │   ├── interrupts.py   # Interrupt / human-in-the-loop handling
│   │   │   └── <domain>.py     # Domain-specific nodes (fetch_history, triage, etc.)
│   │   │
│   │   ├── prompts/            # ── Prompt Templates ──
│   │   │   ├── __init__.py
│   │   │   ├── system.py       # System prompts
│   │   │   ├── defaults.py     # Default / fallback prompts
│   │   │   └── <task>.py       # Task-specific prompts (triage, summarization, etc.)
│   │   │
│   │   ├── schemas/            # ── State & Data Models ──
│   │   │   ├── __init__.py
│   │   │   ├── states.py       # Graph state definitions (TypedDict / Pydantic)
│   │   │   ├── routing.py      # Routing enums / models
│   │   │   └── memory.py       # Memory / store schemas
│   │   │
│   │   ├── tools/              # ── Agent-Specific Tools ──
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Tool assembly (get_tools, wrapping, registration)
│   │   │   ├── approval.py     # Approval wrappers (@requires_approval, add_approval)
│   │   │   └── <tool_name>.py  # Individual tools (memory, search, delegation, etc.)
│   │   │
│   │   └── eval/               # ── Evaluation Framework (optional) ──
│   │       ├── __init__.py
│   │       ├── <eval_name>.py  # Evaluation scripts
│   │       ├── prompts.py      # Eval-specific prompts
│   │       ├── <dataset>.py    # Test datasets
│   │       └── results/        # Stored evaluation outputs (charts, CSVs)
│   │
│   │
│   └── <another_agent>/        # Additional agents follow the same structure
│       ├── __init__.py
│       ├── <another_agent>.py
│       ├── graph_builder.py
│       ├── nodes/
│       ├── prompts/
│       ├── schemas/
│       └── tools/
│
│
├── tests/                      # ── TEST SUITE ──
│   ├── __init__.py
│   │
│   ├── unit/                   # Fast, isolated unit tests (pytest)
│   │   ├── test_<agent>_nodes.py
│   │   ├── test_<agent>_tools.py
│   │   └── test_services.py
│   │
│   ├── integration/            # End-to-end graph tests (pytest)
│   │   ├── test_<agent>_graph.py
│   │   └── test_<service>_live.py
│   │
│   └── notebooks/              # Interactive Jupyter notebook tests
│       ├── test_agent.ipynb              # Full agent walkthrough
│       ├── test_memory.ipynb             # Memory store testing
│       ├── test_tools_live.ipynb         # Live tool integration
│       └── test_<feature>_live.ipynb     # Feature-specific live tests
│
│
└── docs/                       # ── DOCUMENTATION ──
    ├── FOLDER_STRUCTURE.md     # This file
    ├── ARCHITECTURE.md         # System architecture overview
    ├── <SERVICE>_SETUP.md      # Per-service setup guides (GMAIL_SETUP.md, etc.)
    ├── <SERVICE>_TOOLS.md      # Per-service tool documentation
    └── plans/                  # Implementation plans (numbered sequentially)
        ├── 001-initial-setup.md
        ├── 002-feature-name.md
        └── ...
```

## Design Principles

### 1. Shared Services vs Agent-Specific Tools

| Layer | Location | Purpose |
|-------|----------|---------|
| **Services** | `src/services/<name>/` | Reusable integrations (API clients, auth, helpers). Shared across agents. |
| **Agent Tools** | `src/<agent>/tools/` | Tools exposed to the LLM. May wrap service methods. Agent-specific behavior. |

**Rule of thumb:** If two agents need the same API client, it belongs in `services/`. If only one agent uses a tool, it stays in that agent's `tools/` folder.

```
services/gmail/client.py    →  Gmail API wrapper (fetch, send, label)
email_assistant/tools/       →  @tool send_email(...) that calls the Gmail client
personal_assistant/tools/    →  @tool check_inbox(...) that also calls the Gmail client
```

### 2. Agent Package Internals

Each agent is a self-contained package with consistent subfolders:

| Subfolder | What goes here |
|-----------|----------------|
| `nodes/` | Pure functions `(state) → dict`. Each file = one node or a group of related nodes. |
| `prompts/` | String templates or functions that return prompts. Separated by task. |
| `schemas/` | `TypedDict` or Pydantic models for graph state, routing decisions, memory. |
| `tools/` | `@tool`-decorated functions + assembly logic (`get_tools()`). Approval wrapping happens here. |
| `eval/` | Evaluation datasets, scripts, and result artifacts. Optional but recommended. |

### 3. Graph Construction Pattern

```python
# <agent_name>.py — Entry point (what langgraph.json points to)
from <agent_name>.graph_builder import build_graph

graph = build_graph()   # Returns a compiled StateGraph

# graph_builder.py — All wiring in one place
def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("node_a", node_a_fn)
    builder.add_node("node_b", node_b_fn)
    builder.add_edge("node_a", "node_b")
    ...
    return builder.compile(checkpointer=...)
```

### 4. Tool Registration Pattern

```python
# tools/base.py
def get_tools(dev_mode: bool = False) -> tuple[list, dict]:
    """Assemble all tools for this agent.

    Returns:
        (tools_list, tools_by_name_dict)
    """
    tools = [tool_a, tool_b, tool_c]

    # Conditional approval wrapping
    if not dev_mode:
        tools = [add_approval(t) if t.name in NEEDS_APPROVAL else t for t in tools]

    tools_by_name = {t.name: t for t in tools}
    return tools, tools_by_name
```

### 5. Adding a New Agent

1. Create `src/<agent_name>/` with the subfolder structure above
2. Export the compiled graph from `<agent_name>.py`
3. Register in `langgraph.json`:
   ```json
   {
     "graphs": {
       "<agent_name>": "./src/<agent_name>/<agent_name>.py:graph"
     }
   }
   ```
4. Add tests in `tests/`
5. Add docs in `docs/`

### 6. Adding a New Shared Service

1. Create `src/services/<service_name>/` with `client.py`, `settings.py`, `tools.py`
2. Each agent that uses it imports from `services.<service_name>`
3. Add setup guide in `docs/<SERVICE>_SETUP.md`
