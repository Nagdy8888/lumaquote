---
name: langgraph
description: Write or change LangGraph code in app/agents - state, nodes, edges, interrupts and resume, checkpoint persistence and threads. Use for any agent-graph change; pair with implement-human-approval for approval pauses.
---

# LangGraph

One entry point for the three upstream LangChain skills, kept unchanged (pinned commit
`126c384d8552dcb476b226c244172186cc3f4328`) as references. Read only the part you need:

- [fundamentals](references/fundamentals/GUIDE.md): StateGraph, state schemas, nodes, edges, Command, streaming.
- [human-in-the-loop](references/human-in-the-loop/GUIDE.md): `interrupt`, validated resume input, replay and idempotency.
- [persistence](references/persistence/GUIDE.md): checkpointers, threads, durable state.

The references show many languages; this project uses Python only.

## Project rules that override the examples

- Verify every API against the installed `langgraph` version (`requirements.lock.txt`) before use (R3).
- The checkpointer is PostgreSQL; in-memory checkpointers are for isolated tests only.
- A thread id is not authorization: map it to an authorized company/conversation on the server.
- Nodes call backend business interfaces; prices, totals, approval and sending are deterministic code, never prompt-only.
- Approval binds to the exact quotation revision and customer (`implement-human-approval`).
- Trace detail follows decision D24 in `docs/DECISIONS.md` (full detail, secrets and phone numbers masked).
- Where to look in this repo: `app/agents/luma_agent/` (`graph.py`, `state.py`, `nodes/`, `runtime/`, `worker.py`)
  and `docs/reference/AGENT_RUNTIME.md`.
