# Project documentation

Start with the guide for the job you are doing. The approved plan and test targets
remain intact; progress reports describe observed snapshots rather than release readiness.

- **Run or recover the app:** [local development](../LOCAL_DEVELOPMENT.md), including
  native commands, configuration, media processing and safe failure recovery.
- **Use the sales workspace:** [workflows](WORKFLOWS.md), covering revisions,
  approval, takeover, internal notes, human replies, evidence and media confirmation.
- **Change the code:** [architecture](ARCHITECTURE.md) explains processes, trust
  boundaries, module ownership, durable state and known recovery limits.
- **Call or extend an endpoint:** [API guide](api/README.md) and
  [generated OpenAPI](api/openapi.json) describe transport and business preconditions.
- **Verify a claim:** [testing plan](TESTING_PLAN.md), [engineering ledger](engineering/coverage.json),
  and the [evidence directory](evidence) distinguish local tests, live canaries,
  generated development queries and unfinished release gates.
- **Continue the implementation:** [implementation tracker](IMPLEMENTATION_PLAN.md),
  [work log](WORK_LOG.md) and [account actions](MORNING_ACTIONS.md).
- **Work on UI:** [design system](../DESIGN.md) and [UI direction](UI_DIRECTION.md).
- **Work on providers:** [OpenAI contracts](PROVIDER_CONTRACTS.md). The working-tree
  Google Apps Script source/setup guide is `gas/README.md`; Google status is
  recorded separately in [its evidence](evidence/google-gas-progress.json).

## Detailed implementation references

The [visual diagram guide](diagrams/README.md) links source-backed workflows,
architecture, ER relationships, agent/media/recovery states and integration
sequences. Guides embed readable SVGs with full-size links and expandable Mermaid;
their canonical sources and repeatable checks are documented there.

These references explain actual source contracts, side effects and failure
boundaries. Use the overview guides above to enter the project, then follow the
reference for the module you are changing:

- [Backend contracts](reference/BACKEND.md): Auth/company selection, restricted
  transactions, rate/idempotency semantics, participation, canonical arithmetic,
  revision/approval/dispatch sequence and private documents.
- [Data model and migrations](reference/DATA_MODEL.md): each table's ownership,
  keys/foreign keys, grants/RLS, media/vector bindings, precision, checkpoint
  separation and every migration's purpose.
- [Agent runtime](reference/AGENT_RUNTIME.md): state fields, graph edges and each
  node, durable resume, duplicate work, capacity/fences, budget reservation,
  interrupted work and trace privacy.
- [Media processing](reference/MEDIA.md): upload admission/identity, resource-bounded
  decode, fixed provider contracts, state transitions, written confirmation,
  private previews and recovery.
- [Catalog and retrieval](reference/CATALOG.md): conservative parsing, exact/lexical
  ranking, semantic cache identity/distance limits, paid index/query lifecycle,
  candidate revalidation and what evaluation results actually prove.
- [Frontend implementation](reference/FRONTEND.md): composition/routes, session and
  query keys, dirty draft conflicts, mutation reconciliation, temporary document
  capabilities, 3D fallback and capture/accessibility limits.
- [Google synchronization](reference/GOOGLE_SYNC.md): GAS ownership, HMAC/envelopes,
  receipt replay, complete schema validation, atomic publication and timer limits.
- [WhatsApp channel](reference/WHATSAPP.md): signed webhook ingress, sender allowlist,
  restricted media fetch, three-phase gated sending, uncertain outcomes, monotonic receipts
  and the (mock-only) proof boundary.
- [Configuration and operation](reference/CONFIGURATION.md): actual safe variable
  inventory/defaults, precedence/cache behavior, process/port ownership and private
  generated files.
- [Tooling and tests](reference/TOOLING_AND_TESTS.md): development scripts/test
  families, fixture preservation, gate commands, browser assertions, live opt-ins,
  CI scope and evidence interpretation, including the [80-scenario evaluation set](../tests/fixtures/evaluation/README.md) and what its offline baseline does not prove.

For example, to change photo processing, read MEDIA for its state/resource
contract, AGENT_RUNTIME for lease/allowance ownership, DATA_MODEL for durable
bindings and TOOLING_AND_TESTS for the tests that exercise those boundaries.
Do not infer a complete integration from an intended screen or a configured key.

## Documentation coverage and update ownership

The durable requirement is in [root AGENTS.md](../AGENTS.md), implemented through
the [project-documentation skill](../.agents/skills/project-documentation/SKILL.md)
and its [deep documentation standard](../.agents/skills/project-documentation/references/deep-documentation.md).
The always-applied editor rule at `.cursor/rules/project-documentation.mdc` points
to those same sources. Planning, review and release skills use this requirement;
it must travel with future implementation rather than depend on chat history.

Every authored function/class has its local contract near the definition. These
guides cover the larger responsibilities without duplicating every implementation line.

- `app/backend/luma/core/*` → architecture identity/trust boundaries, API admission
  protocol and local configuration/recovery instructions.
- `features/conversations/*`, `features/messaging/authorization.py` → workflow
  participation rules, API mutation preconditions, actor/dispatch boundaries.
- `features/quotations/*` → canonical content/PDF ownership, revision/approval
  workflow and freshness/dispatch checks.
- `features/catalog/*`, `scripts/evaluate_catalog.py` → descriptive evidence rules,
  exact-first lookup, source retirement and generated-baseline limitations.
- `features/media/*`, `luma_agent/runtime/{audio,media}.py`,
  `luma_agent/adapters/media_reading.py` → media lifecycle, provider contracts,
  raw upload/preview protocol and uncertain-outcome recovery.
- `luma_agent/{graph,state,lease,budget,observability}.py`, `nodes/*`, `runtime/*`
  → orchestration, fenced jobs, persisted participation, estimates and trace privacy.
- `src/features/conversations/*`, `src/features/quotations/*` → operator actions,
  local dirty-state behavior, pending/error handling and private viewer lifecycle.
  Shared and app composition boundaries are documented in the architecture guide.
- `supabase/migrations/*`, setup/dev scripts → local schema lifecycle and data
  preservation. The testing plan retains migration/restore requirements that are
  not established merely by successful local setup.
- `tests/unit`, `tests/integration`, `tests/browser` → testing plan plus dated
  result artifacts. Test source alone is not a passing result.

After each coherent change, update the affected inline contract and relevant
guide, append its actual result/gaps to `WORK_LOG.md`, then run the applicable
checks. Do not mark plan items complete from scaffolding, configured credentials,
mocked provider responses or a library installation. Account actions belong in
`MORNING_ACTIONS.md`; credentials never do.

## Current verification boundaries

The [November 1 written-confirmation evidence](evidence/written-confirmation-2026-11-01.json)
records the current-turn safety slice: complete written-order provenance, 40
controlled development policy cases, real graph denial/resume and a full local
regression. Its modality labels are not audio/vision accuracy or a frozen holdout.

Phases 1 and 2 have committed evidence. Voice/resume and lexical catalog work have
separate progress commits/evidence; phase 3 remains unfinished. Photo API/provider
tests, updated browser workflow and full regression have passed locally.
Version-bound semantic SQL and index recovery checks passed with fake
vectors; a real synthetic embedding plumbing canary also passed. Live semantic
quality and the frozen media evaluation remain unverified.

Read each evidence artifact's scope/date. Earlier aggregate test counts, screenshots,
and green CI do not automatically validate later working-tree changes. GitHub CI
runs static, unit/UI and build checks; the local Supabase/browser/sandbox checks
are separate. LangSmith export encountered a quota rejection on October 29;
current account availability has not been reverified during this commit task.
