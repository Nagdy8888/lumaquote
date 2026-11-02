# Project implementation rules

## Read at the start of every prompt

These rules apply to every Codex prompt and all work in this repository, including
continuations, resumed sessions, and small edits. At the start of each turn, read
this root `AGENTS.md` and any applicable nested `AGENTS.md` before acting. Do not
rely only on a previous turn's copy. Carry these requirements through handoffs and
context compaction. This file governs this project, not unrelated workspaces.

## Documentation after every step or file change

Use the project-documentation skill at
`.agents/skills/project-documentation/SKILL.md` for every task that changes files
or completes an implementation/setup/verification step. Read its instructions
and relevant references before the first such step in each turn.

After each completed step or coherent file-change group, update documentation
before starting the next step. Do not postpone documentation until the end of a
phase, commit, or conversation. This covers code, tests, scripts, GAS, migrations,
configuration, assets, dependencies, and documentation files themselves.

- Update the affected inline contracts and existing setup/reference/runbook docs
  whenever behavior, structure, configuration, or operating instructions change.
- Append a concise entry to `docs/WORK_LOG.md` recording the step, changed paths,
  purpose, actual verification results, and remaining gaps or required account
  actions. Record failures and unrun checks honestly. For private configuration,
  record only the purpose and safe variable names, never values or credentials.
- Keep `docs/IMPLEMENTATION_PLAN.md` and its approved scope intact; update existing
  progress items only when supported by implementation and verification. Preserve
  `docs/TESTING_PLAN.md` requirements. Put account-dependent follow-up actions in
  `docs/MORNING_ACTIONS.md` and evidence in the existing evidence location.
- Include documentation-only changes in the same work-log entry as the step they
  describe. Updating the log does not require another recursive log entry.
- Before reporting a step complete, review the changed-file list for documentation
  coverage and run applicable architecture/documentation checks plus relevant
  feature checks. A passing check does not replace reviewing the docs themselves.

For a read-only answer with no completed operational step or file changes, no
work-log entry is required; still read and follow this file for that prompt.

## Required documentation depth

Documentation is part of implementation acceptance. A work-log entry, file list,
generated schema, passing docstring check or one-line purpose comment alone does
not satisfy the user's requirement for deep documentation.

Before changing an existing subsystem, read its relevant implementation reference
through `docs/README.md` and verify it against source. For each changed behavior,
document the affected contracts as applicable: actors and authority; module/call
flow; meaningful inputs, outputs and units; state transitions; database writes and
transaction/lock boundaries; identity/version/idempotency rules; resource and cost
limits; external effects; failures, uncertainty and recovery; configuration and
operation; tests, actual evidence and remaining gaps. Explain why an important
invariant exists and what callers must preserve when extending the implementation.

Keep function/class contracts adjacent to definitions and cross-module explanations
in the focused `docs/reference/` guides linked from the documentation index. Update
existing guides rather than creating competing explanations. Extend or split a
guide when responsibilities require it; there is no mandatory page or line count.
A small change updates its relevant contract, not every unrelated guide.

Review documentation against all affected new, changed, renamed and deleted paths
before reporting completion or making a phase commit. Validate links/examples and
run applicable inline/architecture checks. A documentation-only change should use
appropriate static/contract checks; do not report historical runtime tests as rerun
or spend on live providers merely to validate prose. Follow the detailed standard
in `.agents/skills/project-documentation/references/deep-documentation.md`.

## Maintained diagrams and professional visual documentation

Use the installed `mermaid-diagrams` skill with project-documentation when
documenting architecture, relationships, nontrivial workflows or state changes.
Maintain the affected diagrams alongside code; do not substitute diagrams for
meaningful inline contracts or detailed prose.

Canonical sources live in `docs/diagrams/*.mmd`, with catalogued code bindings,
owned guide embeds and generated SVG previews. Keep views focused, labels readable,
contrast clear and titles/descriptions accessible. Draw actual relationships;
label optional, planned, unverified and local-only paths explicitly. Exclude
credentials, private URLs and customer data.

Before completion or commit, run the diagram tests, render changed sources and
verify `npm run diagrams:check`. Inspect actual rendered output for readability,
clipping, stray nodes and misleading arrows; syntax success and file hashes alone
are insufficient. Source, embeds and assets must agree. Use the local renderer;
do not upload project data or install global tooling as a side effect. Small
unrelated prose changes do not require a decorative diagram. The documentation
skill's visual standard defines the detailed workflow.

## Layout and responsibilities

- `app/backend/luma/core`: configuration, identity, database, storage, admission,
  errors, and other genuinely shared infrastructure. Never import features here.
- `app/backend/luma/features/<feature>`: transport schemas, routes, domain rules,
  persistence, and application behavior owned by that feature. Separate files by
  responsibility; routes validate transport and delegate business decisions.
- `app/backend/luma/main.py`: application composition only. No business queries,
  pricing, provider calls, or workflow decisions.
- `app/agents/luma_agent`: typed graph state, construction, individual nodes,
  prompts/adapters, and orchestration. Agents call backend business interfaces;
  deterministic rules and action authorization never live only in prompts.
- `app/frontend/src/app`: router, providers, and application composition.
- `app/frontend/src/features/<feature>`: feature UI, queries, mutations, and
  behavior. Keep internal implementation private behind a small public entry.
- `app/frontend/src/shared`: business-independent UI, session/API infrastructure,
  and genuinely shared contracts. Do not accumulate unrelated helpers.
- Root `scripts`, `tests`, `docs`, and `supabase` own development automation,
  verification, documentation, and migrations respectively.

No god files or speculative empty hierarchies. Split when responsibilities change,
not according to an arbitrary line count. Use explicit imports; avoid global
service locators, circular dependencies, and large barrels exporting everything.

## Inline documentation

The user explicitly requires inline documentation for every authored function and
class. Python definitions, including private helpers and nested functions, need a
docstring. TypeScript/JavaScript named functions, classes, hooks, components, and
nontrivial callbacks need adjacent JSDoc explaining their contract. Document small
inline callbacks at their containing expression when this is clearer.

Explain purpose, meaningful input/output semantics, side effects, authorization,
invariants, and error behavior as relevant. Do not restate every identifier or
invent guarantees. Update documentation when behavior changes. Generated API
types and unmodified vendored components remain clearly labeled; document owned
wrappers rather than hand-editing generated declarations.

Keep local docs close to code, with project docs recording larger decisions.
Run the architecture/documentation checks as well as feature tests before claiming
the requested structure and documentation are covered.

## Verification and truth

Preserve the approved plan in `docs/IMPLEMENTATION_PLAN.md` and testing requirements
in `docs/TESTING_PLAN.md`. Check off only implemented and verified behavior.
Read actual contracts/types and pinned documentation before using an API; never
invent functions, configuration, schemas, completed integrations, or test results.
Never expose populated environment files or credentials in logs, UI, traces, or
test output. Keep simulated/local and live integration evidence distinct.

## Phase commits

The user authorizes a commit and push after every completed implementation phase.
Run that phase's applicable checks, update its tracker and evidence, inspect the
staged diff for secrets/unrelated changes, then make a descriptive scoped commit.
Do not call an incomplete phase complete to create a commit. Never bypass failing
checks or hooks. Push to the verified intended remote without force-pushing; check
remote CI when available. Report the commit, push result, and validation. If no
remote is configured, finish the local work and report the missing destination.
This standing authorization does not include deployment or rewriting history.

## Unattended work and integration tooling

Continue authorized plan work while the user is asleep. Record anything requiring
their interactive account access, consent, credentials, or decisions in
`docs/MORNING_ACTIONS.md`; do not pause independent work for those prerequisites.
Use the applicable installed skills and record actual validation and gaps.
Manage the Google Apps Script source/project with clasp as explicitly requested.
