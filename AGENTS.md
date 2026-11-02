# LumaQuote working rules

Binding for every agent and model (Codex, Claude Code, Sonnet, Opus) on every prompt,
including small edits, continuations and resumed sessions. Re-read this file at the
start of each turn; do not rely on an earlier copy. Approved 2026-11-03 (decision D32);
the reasoning is in [the proposal](docs/proposals/2026-11-03-working-rules.md) and the
previous long-form rules are archived in [docs/archive/](docs/archive/AGENTS-until-2026-11-03.md).

User decisions live in [docs/DECISIONS.md](docs/DECISIONS.md). If a rule, skill, doc or
code conflicts with a decision there, the decision wins; fix the conflicting file in the
same change.

## Rules

Each rule names its enforcement: **script** (fails `npm run verify`), **hook** (Claude Code
blocks or warns), **review** (checked by reading).

**Before work**
- **R1** Read this file, `docs/DECISIONS.md` and the lead skill for the task (routing table below). *review*
- **R2** Ask the user first when a task changes security, money, data deletion, paid calls, external messages, accounts or scope. Record the answer in `docs/DECISIONS.md`. *review*
- **R3** Never guess an API. Read the pinned version (`requirements.lock.txt`, `package-lock.json`) and official docs before using it. *review*

**While editing**
- **R4** Every Python and TypeScript function, class, hook and component has an adjacent contract: purpose, meaningful inputs/outputs, side effects, authority, invariants, errors. Do not restate identifiers. *script: `check:architecture`, `check:frontend`*
- **R5** Layering: `core` never imports features; routes validate transport and delegate; `main.py` only composes; agent nodes call backend business interfaces; business rules and authorization are deterministic code, never prompt-only. No god files. *script: `check:architecture`, `check:frontend`*
- **R6** After editing an existing file, look at `git diff --stat`. A file that lost more than 30 lines needs a stated reason in the work log. *hook (warn)*
- **R7** Experiments that change source (mutation tests, probes) run in a `git worktree` or are reverted with `git checkout -- <file>` and confirmed with `git status`. Never leave them in the main tree. *review*
- **R8** Text files are UTF-8 with LF line endings and no mojibake (`â€`, `Ã`). *script: `check:docs`*

**Evidence and claims**
- **R9** Every result names exactly one label: `local`, `local-substitute`, `sandbox`, `live`, `synthetic`. New `docs/evidence/*.json` files carry the common header (`date`, `commit`, `label`, `command`, `result`). *script: `check:docs`*
- **R10** A plan checkbox is ticked only with an evidence link on the same line. Phase 4 items need `live` evidence. *script: `check:docs`*
- **R11** Evaluation scoring rules and oracle changes are committed before the run they score. Changes made after seeing results are labeled `post-hoc` and reported separately. *script: `summarize_agent_run.py`*
- **R12** "All checks pass" means one complete `npm run verify:full` on the final tree. Partial runs are reported as partial; skipped checks as skipped. *review*
- **R13** Never print, log, commit or trace secrets, tokens or phone numbers. Credentials stay backend-only. *script: `check:secrets`; trace masking tests*

**Finishing**
- **R14** A task that changed files ends with deep documentation (next section), one work-log entry in the template, and the narrowest checks that cover the change. *hook (Stop blocks when code changed without a work-log entry)*
- **R15** Commit and push only at a completed phase or when the user asks. Stage only your own files. Never force-push, rewrite history, bypass hooks or deploy. *hook (blocks force-push, `reset --hard`, deploy)*

## Documentation (decisions D30, D33)

Documentation is part of the change, not a later step. For anything added or changed:

1. **Inline contracts** next to the code (R4).
2. **Deep reference**: update the owning guide in `docs/reference/` (index: [docs/README.md](docs/README.md)).
   Cover what applies: actors and authority, call flow, inputs/outputs and units, state transitions,
   database writes and transactions, idempotency, limits and cost, external effects, failures and
   recovery, configuration, tests and evidence, open gaps. Full standard:
   [deep documentation](.agents/skills/project-documentation/references/deep-documentation.md).
3. **Diagrams**: when a change touches architecture, a workflow or a state machine, edit the
   canonical `docs/diagrams/*.mmd`, run `npm run diagrams:render` then `npm run diagrams:check`, and
   look at the rendered SVG for clipping and misleading arrows. Local renderer only.
4. **Knowledge graph**: after a change that adds, moves or deletes modules, run `npm run graph:update`
   so `graphify-out/` matches the code (decision D33).
5. **Work log**: append one entry to `docs/WORK_LOG.md`:

```
### YYYY-MM-DD - <what changed> (phase N, <label>)
- Why: <user request or plan item>
- Changed: <paths>
- Checked: <command> -> <result>; not run: <list>
- Evidence: <file or none>
- Open: <gaps / user actions>
```

One home per fact: plan status in `docs/IMPLEMENTATION_PLAN.md` (checkbox + one status line +
evidence link); test requirements in `docs/TESTING_PLAN.md` (never weaken); user decisions in
`docs/DECISIONS.md`; current behavior in `docs/reference/`; history in `docs/WORK_LOG.md`;
open user actions in `docs/MORNING_ACTIONS.md`; proof in `docs/evidence/`.

## Skill routing

Skills live in `.agents/skills/` (canonical) and are mirrored to `.claude/skills/` for Claude Code
with `npm run skills:sync`. Pick one lead skill; add at most two supporting skills.

| Task | Lead skill | Supporting |
|---|---|---|
| Scope, architecture, new workflow slice | `plan-quotation-app` | `verify-and-review` |
| Backend route, schema, dependency | `fastapi` | `secure-quotation-app` |
| Prices, stock, totals, revisions, PDFs | `build-quotations` | `fastapi` |
| Agent graph, nodes, checkpoints | `langgraph` | `implement-human-approval` |
| Approval pauses, takeover, clarification | `implement-human-approval` | `langgraph` |
| Voice notes, transcription, photos | `process-voice-notes` | `secure-quotation-app` |
| Catalog ingestion, retrieval, citations | `ingest-supplier-evidence` | `langsmith-trace` |
| LangSmith tracing and trace queries | `langsmith-trace` | `secure-quotation-app` |
| WhatsApp webhook, media, sending | `integrate-whatsapp` | `secure-quotation-app` |
| Google Sheets, Drive, Apps Script, clasp | `automate-google-workspace` | `secure-quotation-app` |
| Auth, tenancy, uploads, rate limits, budgets | `secure-quotation-app` | `verify-and-review` |
| Frontend code, queries, mutations | `frontend-structure` | `shadcn` |
| Visual design, layout, motion, 3D | `frontend-design` | `impeccable`, `shadcn` |
| shadcn components | `shadcn` | `frontend-structure` |
| Evaluation datasets, scoring, holdout | `evaluate-quotation-agent` | `verify-and-review` |
| Docs, diagrams, evidence | `project-documentation` | - |
| Code review, "is it done", plan checkboxes, coverage ledger | `verify-and-review` | `project-documentation` |
| Commits, pushes, PRs | `contribution-workflow` | `verify-and-review` |

## Code layout

- `app/backend/luma/core`: shared infrastructure (config, identity, database, storage, admission, errors).
- `app/backend/luma/features/<feature>`: schemas, routes, domain rules, persistence for one feature.
- `app/backend/luma/main.py`: composition only.
- `app/agents/luma_agent`: graph state, construction, nodes, adapters, runtime, worker.
- `app/frontend/src/app` (composition), `src/features/<feature>` (feature UI and data), `src/shared` (business-independent only).
- Root `scripts`, `tests`, `docs`, `supabase`, `gas`: automation, verification, documentation, migrations, Apps Script.

## Commands

Run everything through npm scripts; they wrap the project's Python (`node scripts/python.cjs`).

| Purpose | Command |
|---|---|
| Local Supabase | `npm run db:start` |
| API / worker / UI | `npm run dev:api`, `npm run dev:worker`, `npm run dev:ui` |
| Fast rule checks | `npm run check:rules` (docs, skills) |
| Lint, architecture, frontend | `npm run lint:python`, `npm run check:architecture`, `npm run check:frontend` |
| Tests | `npm run test:unit`, `npm run test:python`, `npm run test:ui`, `npm run test:browser` |
| Diagrams | `npm run test:diagrams`, `npm run diagrams:render`, `npm run diagrams:check` |
| Skills mirror | `npm run skills:sync`, `npm run skills:check`, `npm run skills:manifest` |
| Knowledge graph | `npm run graph:update` |
| Full gate | `npm run verify`, `npm run verify:full` |

## Unattended work and accounts

Continue authorized plan work while the user is away. Put anything that needs the user's
accounts, consent or credentials in `docs/MORNING_ACTIONS.md` and keep going with independent
work. Browser work in the user's Google and Meta accounts is allowed (decision D13); secrets go
straight into ignored `.env.local` and are never shown, logged or committed. Paid provider calls
need the opt-in flags the tests define and the user's approval for that run.
