# User decisions register

This file is the single home for decisions the user (the project owner) has made.
Rules, skills, plans and code must agree with it. When a skill or doc conflicts with
an entry here, the entry wins and the conflicting file is fixed in the same change
(rule R1/R2 in [AGENTS.md](../AGENTS.md)).

How to add an entry: append a row to the right section with the date (YYYY-MM-DD), the
decision in one or two sentences, and where it came from (chat question, work-log entry).
Never edit an old decision in place; add a newer row that supersedes it and say which.

## Product and scope

| ID | Date | Decision | Source |
|---|---|---|---|
| D01 | 2026-10-29 | English web app for an electrical (commercial-lighting) distributor. Customers use WhatsApp text and English voice notes; authorized salespeople approve exact quotation revisions before sending. | `.agents/skills/SKILL_SELECTION.md` |
| D02 | 2026-10-29 | Synthetic business data and test media are allowed if labeled. No revenue or time-saving claims. | `SKILL_SELECTION.md` |
| D03 | 2026-10-29 | Stack: React/TypeScript/Vite/Tailwind/shadcn/TanStack Query; FastAPI/Pydantic; Python LangGraph; PostgreSQL + pgvector; durable PostgreSQL worker; SSE; pytest/Playwright; isolated local Supabase `quotation-local-dev`. | `SKILL_SELECTION.md` |
| D04 | 2026-10-29 | OpenAI for inference and English transcription; LangSmith for tracing. Models pinned in `app/backend/luma/core/config.py`. | `SKILL_SELECTION.md`, plan |
| D05 | 2026-10-29 | Business defaults (USD, tax excluded, limits, retention, budgets) as listed in the plan's "Fixed business defaults". | `docs/IMPLEMENTATION_PLAN.md` |
| D06 | 2026-11-02 | Showcase runs locally only (this machine, local Supabase). No deployment in scope. | Chat, plan decisions |

## Integrations

| ID | Date | Decision | Source |
|---|---|---|---|
| D10 | 2026-10-29 | Google: Apps Script only (GAS-only). No backend Google OAuth client or Google Cloud setup. GAS sends signed snapshots after edits and on an approximately one-minute timer. | Work log 2026-10-29 |
| D11 | 2026-10-29 | WhatsApp: Meta Cloud API directly with the free developer test number and authorized test recipients. | `SKILL_SELECTION.md` |
| D12 | 2026-11-02 | Phase 4 stays gated on real Google and real WhatsApp verification; the user will do the account steps. | Chat |
| D13 | 2026-11-03 | Claude may operate the user's Google Apps Script and Meta developer pages in the browser to connect the app. Secrets copied by Claude go straight into ignored `.env.local` and must never be printed, logged, committed or traced. | Chat |

## AI, evaluation and tracing

| ID | Date | Decision | Source |
|---|---|---|---|
| D20 | 2026-11-02 | Model extraction stays as an advisory check; the deterministic written-order parser is the only path that confirms SKU and quantity. | Chat, plan decisions |
| D21 | 2026-11-02 | Paid evaluation: development re-runs allowed when the user approves; the frozen holdout is run once, only after the user confirms the agent is final. | Chat |
| D22 | 2026-11-02 | Recall@5 needs more labeled retrieval cases: relabel existing scenarios before the freeze, keeping 80 total and the 40/24/16 and 60/20 splits. | Chat |
| D23 | 2026-11-02 | Synthetic TTS voice and drawn label images satisfy the 24 voice/16 photo item when labeled synthetic. | Chat |
| D24 | 2026-11-03 | LangSmith traces show full detail: every graph step, model call and tool call with inputs and outputs. API keys, tokens and phone numbers are masked; message text, transcripts and quotations are shown. Supersedes the earlier opaque-only export rule in `plan-quotation-app`. | Chat |

## Working method

| ID | Date | Decision | Source |
|---|---|---|---|
| D30 | 2026-10-29 | Documentation ships with every change; every function and class has an inline contract. | `AGENTS.md` |
| D31 | 2026-10-29 | One commit and push per completed phase (or when the user asks); no force-push, history rewrite or deploy. | `AGENTS.md` |
| D32 | 2026-11-03 | Working rules R1-R15, skill consolidation (37 -> about 20, auto-discovered by Claude Code), documentation homes and Claude Code hooks approved as in [the proposal](proposals/2026-11-03-working-rules.md). | Chat |
| D33 | 2026-11-03 | Documentation must be deep for anything added or changed, with maintained diagrams, and the repository is mapped with a graphify knowledge graph. | Chat |
| D34 | 2026-11-03 | Old work-log entries stay in place (archiving old months was not approved); new entries use the short template. | Chat (archiving not chosen) |
| D35 | 2026-11-03 | Order of work: rules first, then detailed tracing, then live Google/Meta connections. | Chat |
| D36 | 2026-11-03 | Mirror all 19 project skills to `.claude/skills/` for Claude Code, including `impeccable` and its bundled Windows executable, after seeing the SkillSpector report (DO_NOT_INSTALL; the only finding judged real was the unverifiable `impeccable.exe`; the rest were scanner coverage limits and docs mentioning `.env` or attacks). | Chat |
