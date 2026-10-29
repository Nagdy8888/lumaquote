# Deep Agents harness

The [Deep Agents harness](https://docs.langchain.com/oss/python/deepagents/harness) (the `deepagents` Python package) is a higher-level wrapper around LangGraph that bundles primitives we'd otherwise reinvent per project: explicit planning, subagent delegation, a virtual filesystem, declarative permissions, HITL interrupts, persistent memory, and progressive-disclosure skills.

This file is the MIS opinion on when to reach for it and how to wire it cleanly into the standard folder layout.

## When to use it

Adopt the harness when **two or more** of these are true:

- The agent runs for many turns / hours and the working context grows.
- The work decomposes into independent subtasks that benefit from isolated context.
- The agent produces durable artefacts (drafts, research reports, code) that later turns will read or edit.
- You need fine-grained, auditable control over what the agent can read / write.
- You want the plan to be inspectable by a human — and resumable.
- The collaboration spans sessions and the agent benefits from persistent memory.

If only one is true, a vanilla `StateGraph` with a ReAct loop is usually simpler.

## The primitives — one at a time

### `write_todos` (planning)

The harness exposes a `write_todos` tool that lets the agent maintain a structured task list with `pending` / `in_progress` / `completed` statuses, persisted in agent state.

**Why it pays for itself:**

- The plan becomes inspectable — a human (or a sibling agent) can read it and intervene.
- The agent doesn't have to re-derive its plan from scratch when the context gets compressed.
- Resumption is trivial — the todo list is the resume point.

**Do not disable it.** The token cost is small; the inspectability gain is large.

### `task` (subagent delegation)

The main agent gets a `task` tool that spawns an **ephemeral subagent** with its own fresh context. The subagent runs autonomously and returns a **single final report** to the main agent.

**Why use a subagent instead of just calling a function:**

- **Context isolation** — the subagent's intermediate reasoning never enters the main context.
- **Parallelism** — multiple subagents can run concurrently.
- **Specialisation** — the subagent can have a different tool set, system prompt, or model.
- **Compression** — a noisy 50-turn research process compresses into a 200-token summary.

**When to spawn a subagent:**

- The subtask is large enough (think: 5+ tool calls or 10k+ tokens of intermediate reasoning).
- The subtask has a clearly-statable goal and a clearly-statable success condition.
- Multiple subtasks can be parallelised.

**When *not* to spawn one:**

- The task is "help me think about X" with no clear deliverable — the parent benefits from seeing the reasoning.
- The task is < 3 tool calls — the spawn overhead dominates.
- The task needs many turns of interaction with the parent — subagents return *one* report.

Subagents inherit the parent's permissions by default; you can also pass a narrower permission set per subagent.

### Virtual filesystem

A pluggable filesystem backend that gives the agent these tools:

| Tool         | Purpose                                                              |
|--------------|----------------------------------------------------------------------|
| `ls`         | Directory listing with metadata                                      |
| `read_file`  | Read a file (multimodal: text, images, video, audio, PDF)             |
| `write_file` | Create a file                                                        |
| `edit_file`  | String-replacement edits                                             |
| `glob`       | Pattern file discovery                                               |
| `grep`       | Content search                                                       |
| `execute`    | Shell commands (sandbox backends only)                               |

**Use it for:**

- Drafts and artefacts that the agent produces and later edits (research notes, generated code, document drafts).
- Handoff between turns / sessions — the artefact is persistent, the chat history is not.
- Sharing scratch between a parent and its subagents (the subagent reads the file, writes its output to a new path, returns the path to the parent).

**Don't use it for:**

- Secrets / credentials. Even with permissions, the filesystem is a high-blast-radius surface.
- Working state that belongs in the graph's state dict (current step's variables, routing flags).
- Anything that needs structured querying — that's a database.

The filesystem backend is pluggable: in-memory for tests, sandboxed local FS for dev, an isolated container for production.

### Filesystem permissions

Declarative, **first-match-wins** rules. Pattern:

```python
from deepagents import FileSystemPermission

permissions = [
    FileSystemPermission(operation="read",  path_pattern="/workspace/**",        mode="allow"),
    FileSystemPermission(operation="write", path_pattern="/workspace/drafts/**", mode="allow"),
    FileSystemPermission(operation="read",  path_pattern="**/.env*",             mode="deny"),
    FileSystemPermission(operation="write", path_pattern="**",                   mode="deny"),
]
```

**Rules:**

- **Deny by default.** End the list with a catch-all `mode="deny"` for both `read` and `write`.
- **Allow narrowly.** Allow specific path prefixes (`/workspace/**`, `/sandbox/<thread_id>/**`).
- **Always deny sensitive globs explicitly** even when the catch-all would catch them: `**/.env*`, `**/.ssh/**`, `**/secrets/**`. Defence in depth.
- **Subagents inherit parent permissions** unless you pass them their own narrower set.

### `interrupt_on` (HITL gates)

Pause the agent before specific tool calls so a human can approve, edit, or reject.

```python
graph = create_deep_agent(
    ...,
    interrupt_on={
        "send_email":   True,
        "delete_event": True,
        "post_to_slack": True,
    },
)
```

**Rules:**

- **Interrupt on every tool whose effect cannot be undone cheaply.** Sends, deletes, transfers, posts, payments.
- **The default for new side-effecting tools is `True`.** Loosen explicitly per environment.
- **In dev mode, drop the interrupts** — iteration speed matters and dev data is throw-away. Dev mode is a runtime flag, not a code branch in `main`.

### Memory (`AGENTS.md`)

Persistent memory files loaded at every invocation. Use them for stable preferences and conventions that should carry across sessions — not for chat history.

```python
graph = create_deep_agent(
    ...,
    memory=["./AGENTS.md", "./project-memory.md"],
)
```

**What goes in:**

- The user's preferences (timezone, name pronunciation, communication style).
- The project's conventions (naming, code style, decision policies).
- Decisions made in previous sessions that the agent should respect.

**What does NOT go in:**

- Chat transcripts. That's the checkpointer's job.
- Secrets. Memory files are loaded into the prompt every turn.
- Working state. Use the filesystem or state.

Memory is loaded **always** (unlike skills). Keep it tight (a few hundred lines max) or the per-turn token cost grows.

### Skills (progressive disclosure)

Skills are reusable playbooks the agent loads **on demand**. Each skill is a directory with a `SKILL.md` describing what it is and when to use it — exactly the standard you are reading right now.

**Use skills for:**

- Reusable expertise that doesn't apply to every turn (e.g. "respond to a Stripe webhook failure", "audit a PR for the MIS contribution standard").
- Anything that would bloat the system prompt if loaded unconditionally.

**Don't use skills for:**

- Universal rules — those go in `AGENTS.md`.
- Project-specific configuration — that's `configuration` / env vars.

The harness loads a skill's `SKILL.md` body only when the agent decides the skill is relevant. References + assets are loaded lazily on top of that.

### Harness profiles

Declarative bundles that apply per-provider or per-model settings without per-agent code:

```python
from deepagents import HarnessProfile, register_harness_profile

register_harness_profile(
    "anthropic:claude-sonnet-4-6",
    HarnessProfile(
        excluded_tools=frozenset({"ls", "read_file", "write_file", "edit_file", "glob", "grep"}),
        # ...system prompt tweaks, middleware overrides, etc.
    ),
)
```

**Use profiles to:**

- Exclude tools that a particular model handles poorly.
- Apply system-prompt tweaks that only make sense for one model family.
- Centralise model-specific config so agents stay model-agnostic.

**Do not:**

- Sprinkle `if model == "gpt-4o": ...` through agent code. That's exactly what profiles exist to prevent.

## Where this fits in the folder layout

```
src/<agent_name>/
├── <agent_name>.py             # `graph = create_deep_agent(...)`
├── configuration.py            # RunnableConfig schema
├── settings.py                 # env vars
├── prompts/
│   └── system.py               # SYSTEM_PROMPT
├── tools/
│   ├── base.py                 # get_tools(dev_mode) — assembly + approval (when not using interrupt_on)
│   └── <tool>.py
├── skills/                     # ← optional: per-agent skills the deep agent can load
│   └── <skill-name>/SKILL.md
├── permissions.py              # declarative FileSystemPermission list
└── profiles.py                 # register_harness_profile(...) calls
```

**Two notes on this layout:**

- **`permissions.py`** is its own module so security reviewers can read it without spelunking through agent wiring.
- **`profiles.py`** is imported for side-effects at package import time. Document this in the file's top-level docstring (the `# noqa: F401` trick is acceptable here).

## Build pattern (full template: `assets/template-deep-agent.py`)

```python
"""Build the <agent> deep agent: harness + tools + permissions + interrupts + memory."""
from deepagents import create_deep_agent, FileSystemPermission

from <agent>.tools.base import get_tools
from <agent>.prompts.system import SYSTEM_PROMPT
from <agent>.permissions import PERMISSIONS
from <agent> import profiles  # noqa: F401 — registers HarnessProfile entries

def build_agent(dev_mode: bool = False):
    """Build and return the compiled deep agent."""
    tools, _ = get_tools(dev_mode=dev_mode)

    interrupt_on = {} if dev_mode else {
        "send_email":   True,
        "delete_event": True,
        "post_to_slack": True,
    }

    return create_deep_agent(
        model="anthropic:claude-sonnet-4-6",
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        permissions=PERMISSIONS,
        interrupt_on=interrupt_on,
        memory=["./AGENTS.md"],
    )

graph = build_agent(dev_mode=False)
```

## Best practices — distilled

1. **Don't disable `write_todos`.** Inspectability beats the token savings.
2. **Spawn subagents at clean task boundaries** — a clearly-statable goal with a deliverable. Avoid "help me think" subagents.
3. **Permissions deny-by-default.** Allow `/workspace/**` (or narrower) and deny everything else explicitly.
4. **Interrupt on every side-effecting tool by default.** Loosen per environment, not per code path.
5. **Skills over fat system prompts.** Anything > 100 lines of "if user asks for X, do Y" is a skill.
6. **`AGENTS.md` is for stable preferences.** Working state lives in the filesystem; chat history in the checkpointer.
7. **One harness profile per model.** Centralise per-model knobs.
8. **Subagents inherit permissions — narrow them when you can.** A research subagent doesn't need write access.
9. **Compose the harness once, not per-turn.** The agent is built at process start; per-invocation customisation lives in `configurable`, not `create_deep_agent`.
10. **Trace everything.** Keep `LANGCHAIN_TRACING_V2=true` in production. LangSmith traces show every tool call, every subagent spawn, every permission check.

## Anti-patterns

- Granting a wildcard write (`mode="allow"` on `**`). The whole point of permissions is to be specific.
- Spawning a subagent for every step. Subagents are for *isolation*, not flow control.
- Putting working state in the filesystem because state design is hard. Fix state design.
- Putting secrets in `AGENTS.md`. Memory is loaded into the prompt.
- Embedding skill content in the system prompt. That's not a skill, it's a system prompt — the whole point of skills is progressive disclosure.
- Disabling `interrupt_on` globally because "it slows things down". It slows down side effects, which is the point.
