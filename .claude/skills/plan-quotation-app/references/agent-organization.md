# Agent implementation organization

Start with one coordinated Python LangGraph workflow for the approved quotation process. Preserve a clear distinction between domain rules, integration adapters, LLM-callable tools, graph orchestration, and transport.

## Shape code around actual behavior
Keep graph construction and routing visible and typed. State contains compact serializable progress and references, not service clients, full files, secrets, or redundant authoritative business records.
Separate prompts, schemas, nodes, and tools when their volume warrants it; do not create empty per-agent hierarchies or a new shared package for each function.
Adapters own provider authentication, typed requests/responses, and appropriate transport recovery. They do not import graph state or UI code. Tool wrappers validate caller scope and invoke these adapters or domain operations.
Nodes may call asynchronous services and return partial state updates; do not falsely describe I/O-bearing nodes as mathematically pure. Make dependencies explicit and independently testable.
Keep quotation arithmetic, approval validity, access checks, and action identities in deterministic domain code. The graph coordinates them and cannot replace their enforcement.

## Durable behavior
Use persistent Supabase-backed checkpointing for restart/resume acceptance scenarios. Keep checkpoints separate from business approval and delivery records.
Interrupted node replay must not repeat external sends. Apply exact-revision approval, durable dispatch identity/outbox, worker leases, and recovery policies.
Use one authorized thread mapping per company/conversation. A thread identifier is not a permission token.
Store only necessary conversation state, define retention, and redact nested trace content before LangSmith export.

## Framework and verification boundaries
Read the installed LangGraph fundamentals, persistence, and human-in-the-loop skills for framework mechanics and their language-specific references.
The supplied multi-agent harness examples are not adopted as a requirement. Do not add autonomous subagents, virtual filesystems, persisted instruction memories, another model provider, or a new deployment service to satisfy a template.
Use pytest for domain and node behavior, real persistent-state integration tests for interruption/recovery, and held-out conversation scenarios for quality. Notebooks can explore behavior but are not release gates.

