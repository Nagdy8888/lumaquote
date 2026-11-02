# CLAUDE.md

@AGENTS.md

The imported `AGENTS.md` is the binding rule set for this repository. It was written
for Codex, but every rule applies to Claude Code unchanged: "Codex prompt" means any
prompt. This file only adds what Claude Code needs to follow it. If the two files
disagree, `AGENTS.md` wins; fix this file instead of working around the conflict.

## Start of every turn

1. Re-read the root `AGENTS.md` and any nested `AGENTS.md` that covers the files you
   will touch. Do not rely on an earlier turn's copy, including after context compaction.
2. Read the skills that apply to the task (see below) before the first edit.
3. For any task that changes files, read
   `.agents/skills/project-documentation/SKILL.md` and
   `.agents/skills/project-documentation/references/deep-documentation.md`.

Pure read-only answers do not need a work-log entry, but still follow `AGENTS.md`.

## Project skills are not auto-loaded

The project skills live in `.agents/skills/<name>/SKILL.md`. Claude Code does not
discover that directory, and there is no `.claude/` folder. Open the `SKILL.md`
yourself with the Read tool. Start with `.agents/skills/SKILL_SELECTION.md`, which maps
each task to its owning skill and says which skills must not be stacked.

Common picks:

- Architecture, specs, workflow slices: `plan-quotation-app`
- Backend routes and schemas: `fastapi`, `codebase-design`
- Frontend: `react-feature-structure`, `client-crud-state`, `frontend-design`, `shadcn`
- Agent graph and approval pauses: `langgraph-fundamentals`, `implement-human-approval`
- WhatsApp, voice, catalog, Google: `integrate-whatsapp`, `process-voice-notes`,
  `ingest-supplier-evidence`, `automate-google-workspace`
- Security and abuse: `secure-quotation-app`, `implement-abuse-controls`
- Quotations and prices: `build-quotations`
- Docs and diagrams: `project-documentation`, `mermaid-diagrams`
- Review and release: `review-quotation-code`, `verify-engineering-coverage`,
  `verify-quotation-release`
- Commits, pushes, PRs: `contribution-workflow`

User-level Claude Code skills and plugins do not replace these. Where a user-level
skill overlaps a project skill, the project skill owns the work. The
`.agents/skills/_licenses` folder and the retired-skills archives are reference only;
never load them as guidance.

## Commands

Run everything through npm scripts. They wrap the project's Python environment
(`node scripts/python.cjs`), so do not call `python`, `pytest` or `ruff` directly.

| Purpose | Command |
| --- | --- |
| Start local Supabase | `npm run db:start` |
| API / worker / UI | `npm run dev:api`, `npm run dev:worker`, `npm run dev:ui` |
| Lint Python | `npm run lint:python` |
| Architecture and inline-doc check | `npm run check:architecture` |
| Frontend checks and types | `npm run check:frontend`, `npm run typecheck` |
| Python unit tests | `npm run test:unit` |
| Python tests without browser | `npm run test:python` |
| UI tests | `npm run test:ui` |
| Browser workflow test | `npm run test:browser` |
| Diagram tests, render, freshness | `npm run test:diagrams`, `npm run diagrams:render`, `npm run diagrams:check` |
| Full gate | `npm run verify`, `npm run verify:full` |

Pick the narrowest checks that cover the change, then run the architecture/docstring
check and, for any diagram or code-bound doc change, the diagram checks. Integration
tests need local Supabase; the full gate takes several minutes. Report skipped or
unrun checks as skipped.

## Rules most often missed

- **Docs ship with the change.** After each completed step, update the inline
  contracts and the matching guide under `docs/reference/` (found through
  `docs/README.md`), then append an entry to `docs/WORK_LOG.md` with the changed paths,
  actual verification results and gaps. Do this before starting the next step. Do not
  log the log update itself.
- **Every function and class gets a docstring or JSDoc,** including private helpers,
  nested functions and nontrivial callbacks. `npm run check:architecture` enforces the
  Python side. Describe purpose, side effects, authority, invariants and errors. Do not
  restate identifiers.
- **Layering.** `core` never imports features. `main.py` only composes. Routes validate
  transport and delegate. Agent nodes call backend business interfaces. Business rules
  and action authorization are deterministic code, never only prompts. No god files.
- **Diagrams.** Edit the canonical `docs/diagrams/*.mmd`, run `npm run diagrams:render`,
  then `npm run diagrams:check`, and look at the rendered SVG for clipping and
  misleading arrows. Use the local renderer only; do not upload project data or
  install global tooling.
- **Plans and tests stay intact.** Do not rewrite `docs/IMPLEMENTATION_PLAN.md` or
  `docs/TESTING_PLAN.md`. Check off an item only when it is implemented and verified.
  Ledger entries such as B25/B27 stay Planned until the evidence exists.
- **Evidence labels.** Keep local substitutes, provider sandboxes, live integrations
  and real pilots distinct. No revenue or time-saving claims. Fixtures are fictional.
- **Account-dependent work** goes in `docs/MORNING_ACTIONS.md`. Do not stall independent
  work on it.
- **Secrets.** Never print, log, commit or echo `.env`, `.env.local` or any populated
  config. Record only variable names and purposes. Credentials stay backend-only. Paid
  provider calls need the opt-in the tests already define; never enable them just to
  validate prose.
- **API facts.** Read the actual types, pinned package versions and official docs before
  using an API. Do not invent functions, config, schemas or test results.

## Git

`AGENTS.md` authorizes one commit and push after each completed implementation phase,
and nothing more. Before it: run that phase's checks, update its tracker and evidence,
and inspect the staged diff for secrets and unrelated changes. Use a descriptive scoped
message. Never force-push, rewrite history, bypass hooks, or deploy. The working tree
may hold uncommitted work from earlier sessions; stage only the files you changed.
Commit and push only at a completed phase, or when the user asks.
