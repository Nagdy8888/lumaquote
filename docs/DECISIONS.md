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
| D37 | 2026-11-03 | The live Google (Apps Script, Drive) and Meta (WhatsApp test number, webhook) setup is done by Claude through the browser (Claude in Chrome), not by the user by hand. The user only signs in, approves consent screens and enters verification codes when asked. Secrets go straight into ignored `.env.local` (D13). | Chat |
| D38 | 2026-11-03 | Method for D22: rewrite the first message of seven plain exact-code text scenarios (five development, two holdout) into descriptive spec requests and label them for retrieval; no voice or photo asset is rewritten. Labeled cases rise from 7 to 14 (9 development, 5 holdout). Rewritten development scenarios need a new paid development re-run (separate approval). | Chat (question: how far to relabel) |
| D39 | 2026-11-03 | The frontend phase 5 plan runs on its own branch `feat/frontend-phase5` (git worktree), one commit per task, pushed to GitHub with one pull request. After CI and the local merge gate in the plan pass, Claude merges it with a merge commit and deletes the remote branch, local branch and worktree. Applies to this plan only; R15 otherwise unchanged. | Chat |
| D40 | 2026-11-03 | The frontend phase 5 plan runs to completion unattended: no progress check-ins or approval waits between tasks; blockers are tried, recorded and skipped; it ends only when merged and cleaned up or when every open task needs the user. R2 questions still go to `docs/MORNING_ACTIONS.md`. | Chat |
| D41 | 2026-11-03 | Paid development re-run after the D38 relabel is capped at 40 of the 60 development scenarios to lower cost: 20 text, 12 voice, 8 photo (proportional to the split), always including the five rewritten development scenarios e016, e035, e054, e069, e078; selected with `LUMA_EVAL_IDS`, run name `dev-run-3`, `LUMA_EVAL_MAX_USD` kept low. The report states 40/60 and does not claim the other 20. The holdout is unchanged (80-scenario frozen set, one run, D21). | Chat ("for development rerun for lowering the budget verify the runs for max 40 not 80 scenario") |
| D42 | 2026-11-03 | Every paid evaluation run (development re-runs and the holdout) must be traced in LangSmith through the masked worker trace (`observability.job_trace`, D24). `tests/integration/test_live_evaluation.py` now enables tracing, fails before any paid call if no LangSmith key is configured, and tags each job trace with the run name and scenario. An untraced partial `dev-run-3` (18 of 40 scenarios, about USD 0.005) was stopped and set aside as `.local/evaluation-runs/aborted-untraced-dev-run-3`; it is not reported. | Chat ("every run must be traced in langsmith") |
| D43 | 2026-11-07 | WhatsApp gets a second provider, the Twilio WhatsApp Sandbox, because Meta refuses app creation for the restricted `LumaQuote Test` portfolio. Selected with `WHATSAPP_PROVIDER=twilio`; Meta stays implemented and default, so D11 is kept as an alternative, not removed. The user opens a Twilio trial account (Claude never creates accounts) and joins the sandbox from their phone; trial credit covers test sends, and no paid plan is bought. Quotation PDFs reach Twilio through a 15-minute HMAC-signed gateway link. | Chat (question: easier WhatsApp route; answer: Twilio Sandbox) |
| D44 | 2026-11-07 | Customers reach the agent through a Telegram bot, because Twilio's WhatsApp Sandbox is not free for the user in Egypt and Meta is blocked (D43 context). Telegram is a separate conversation channel (`telegram`) using the free Bot API with long polling from the worker (no tunnel or webhook). It reuses the inbox, agent, approval and outbox pipeline, and has its own allowlist (`TELEGRAM_ALLOWED_USERS`) and live switch (`ENABLE_LIVE_TELEGRAM`). WhatsApp code (Meta and Twilio) stays and is not removed. The user creates the bot in @BotFather. | Chat ("is there is nothing to do make the agent in telegram") |
| D45 | 2026-11-07 | The GitHub repo `Nagdy8888/lumaquote` is public, because GitHub Actions on the private repo were blocked by a billing lock. Claude scanned the full git history first (no secret files; only placeholder and canary tokens). Public status does not clear the account-level billing lock; the user must resolve it in GitHub billing. | Chat ("make the repo public") |
| D46 | 2026-11-07 | Paid AI becomes the agent's brain: with `ENABLE_PAID_AI=true` the OpenAI model (`gpt-6-luna`, D04) reads the recent conversation and a price-free catalog listing and writes the customer replies. An order the model reads from free wording is restated by code and confirmed only by the customer's plain YES directly after that restatement; a written order the model reads identically still confirms directly. Replies mentioning money, percentages, links, discounts, guarantees or approval are replaced by fixed text. Supersedes D20 only while paid AI is on. Budget caps unchanged (USD 25 total, 5 per day, D05). | Chat (questions: provider, confirmation, replies, budget) |
| D47 | 2026-11-07 | Customers can also send requests by Gmail. Google access stays inside the user's Apps Script (D10 kept): `gas/Mail.gs` reads only mails under one Gmail label (`LumaQuote`, set by a Gmail filter) in the user's own mailbox, pushes them signed to the gateway, and sends the replies and quotation PDFs the backend queues, from the user's Gmail. Only senders on `EMAIL_ALLOWED_SENDERS` whose mail Gmail authenticated (DMARC, DKIM or SPF for the From domain) reach the agent. Live sends need `ENABLE_LIVE_EMAIL=true`. Attachments are not processed in this version. | Chat (questions: transport, mailbox, senders) |
