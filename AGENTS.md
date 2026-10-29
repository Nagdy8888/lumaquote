# Project implementation rules

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
