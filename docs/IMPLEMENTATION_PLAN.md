# LumaQuote implementation tracker

The agreed scope is the English commercial-lighting supplier quotation app.
Preserve all six milestones and the [testing plan](TESTING_PLAN.md).
Unchecked means unfinished, not a verified capability. An item is checked only
when it is implemented and verified at the level the item names (local, provider
sandbox or live); local substitutes never check a live item.

## Required code organization

Application code lives in `app/backend`, `app/frontend`, and `app/agents`.
Organize concrete features and infrastructure separately; keep application entry
points limited to composition. Avoid god files and speculative empty abstractions.
Every authored function and class requires meaningful inline documentation, not
only separate project docs. Root AGENTS.md defines the enforceable conventions.

## 1. Design and foundations
- [x] Premium graphite/copper workspace, responsive UI, self-hosted fonts, accessible primitives. ([evidence](evidence/phase-1.json), [accessibility](evidence/phase-1-accessibility.json))
- [x] Native frontend/API/worker commands; isolated local Supabase; restricted DB identities. ([evidence](evidence/phase-1.json))
- [x] Staff Auth, current membership, migrations/RLS/private file access, typed contracts. ([evidence](evidence/phase-1.json))
- [x] 72 labeled synthetic products, six catalog PDFs, realistic requests and stock exceptions. ([evidence](evidence/phase-1.json))
- [x] Real resource-bounded, network-disabled media sandbox. ([evidence](evidence/phase-1.json))

## 2. Manual quotation workflow
- [x] Intake, clarification, evidence, product selection, deterministic Decimal totals. ([evidence](evidence/phase-2.json))
- [x] Immutable revisions, PDF parity, exact customer/revision approval, rejection, takeover. ([evidence](evidence/phase-2.json))
- [x] Durable inbox/jobs/outbox, honest delivery state, scoped idempotency and audit. ([evidence](evidence/phase-2.json))
- [x] Unit/property/integration/composite/browser validation. ([evidence](evidence/phase-2.json))

## 3. Persistent agent and media
- [x] PostgreSQL-backed LangGraph, restart/resume, customer and staff participation. ([evidence](evidence/phase-3-progress.json))
- [ ] OpenAI structured extraction (advisory: the deterministic written-order parser stays authoritative), confirmed consequential media fields, evidence-backed matching.
- [ ] English transcription/photo intake, reservations and limits, redacted LangSmith tracing.
- [ ] Retrieval versions/citations, embeddings, ambiguity/injection/regression checks.

## 4. Live Google and WhatsApp
- [ ] Real Google access through the user's Apps Script authorization (GAS-only), validated Sheet snapshots, signed Apps Script callbacks and approximately one-minute reconciliation.
- [ ] Version Apps Script source in the repository and manage its Google project with clasp.
- [ ] Meta test webhook/media/replies/PDF and receipt reconciliation.
- [ ] Identical Drive PDF export with independent retry.
- [ ] Verified real integrations; account/consent/test-number prerequisites recorded explicitly.

## 5. Visual finish and safeguards
- [ ] Optional lazy 3D product scene; reduced motion/static fallback; LinkedIn capture privacy.
- [ ] Endpoint/rate/quota/capacity/security controls and reviewed 42-concept evidence ledger.
- [ ] Race/restart/outage, retention, migration and isolated backup/restore checks.
- [ ] Desktop/portrait/accessibility/performance and visual review.

## 6. Frozen evaluation and showcase
- [ ] 80 scenarios: 40 text/24 voice/16 photo, split 60 development/20 untouched holdout.
- [ ] Recall@5 >=95%, workflow >=90%, zero unauthorized sends/unsupported final lines.
- [ ] All consequential ambiguity asks/escalates; measured latency and estimated usage reported honestly.
- [ ] Screenshots, truthful 90-120 s shot list, reproducible local setup and verified release evidence.

## Fixed business defaults

USD, tax excluded, separately listed shipping; seven-day validity; no default
discount; admin-only discounts up to 10%; stock is observed, never reserved;
delivery dates require staff confirmation. No paid WhatsApp templates or
out-of-window automatic outreach. Audio <=10 MB/120 s, photo <=5 MB,
native-text PDF <=20 MB/50 pages. Estimated spend allowance $25 total/$5 daily,
$0.25 reservation/run, two active workflows globally, one/conversation,
100 queued work items. Staff reads 120/min, mutations 30/min, approve/send
10/min; customer agent turns 6/min/conversation. Runtime media retention seven
days; business data/checkpoints/audit 90 days; backups seven days.

## Provider defaults

Google integration decision (user approved October 29): use Apps Script only for
Google Workspace access. GAS sends HMAC-signed complete snapshots after edits and
on a one-minute timer to the backend. No backend Google OAuth client/refresh token
or Google Cloud setup is required. The phase 4 Google access requirement is fulfilled
through the user's Apps Script authorization rather than a separate backend grant.
Drive exports also use GAS and must preserve the canonical approved PDF; the
adapter (`gas/Exports.gs` plus the signed claim/receipt protocol) is implemented
and locally tested but has not run in Google. One-minute scheduling is approximate,
not a 60-second delivery guarantee.

Models: gpt-6-luna Responses, gpt-transcribe, text-embedding-3-small (1536 dimensions),
pinned in `app/backend/luma/core/config.py`. Unavailable models are explicit blockers;
never silently choose a costly fallback. Paid calls stay off (`ENABLE_PAID_AI=false`)
unless a test's own opt-in is set for an approved run. Google Apps Script authorization
and Meta test settings require the user's accounts. Live tests and offline substitutes
are reported separately.

## Decisions recorded 2026-11-02

The user answered these planning questions on November 2, 2026:

- **Model extraction stays, as an advisory check.** The deterministic written-order
  parser remains the only path that confirms SKU and quantity; the model can only
  withhold confirmation. The first development run showed no measured benefit over
  the parser, so evaluation reports must state the model's contribution separately.
- **Paid evaluation:** re-measure the development split now; freeze and spend the
  holdout only after the user confirms the agent is final. Each holdout run is one-shot.
- **Recall@5 denominator:** before the freeze, relabel existing scenarios as
  descriptive/retrieval requests so Recall@5 rests on more than three holdout cases.
  Keep 80 scenarios and the 40/24/16 and 60/20 splits; split by family as now.
- **Evaluation media:** synthetic TTS voice notes and drawn label images satisfy the
  24 voice/16 photo item when every report labels them synthetic. They support no
  claim about human speech or camera photos.
- **Live integrations:** the user will complete both the Google and Meta account
  steps; phase 4 stays gated on real Google and WhatsApp verification.
- **Showcase hosting:** local only (this machine and local Supabase). No deployment
  is in scope; "reproducible setup" means the documented local setup.

## Status by phase

Evidence files live in [`docs/evidence/`](evidence/); the [work log](WORK_LOG.md)
records each step. Status below was reconciled with source and evidence on 2026-11-02.

### Phases 1 and 2 - complete, locally verified

Phase 1 checks are recorded in [phase-1 evidence](evidence/phase-1.json) and
[accessibility evidence](evidence/phase-1-accessibility.json). Phase 2 checks are in
[manual workflow evidence](evidence/phase-2.json). Early manual-flow tests do not
establish live WhatsApp, model or Google execution.

### Phase 3 - in progress (1 of 4 items)

Implemented and locally tested:

- Current-turn written-order boundary: only a complete positive written order matching
  all model fields confirms text, voice or photo requests
  ([evidence](evidence/written-confirmation-2026-11-01.json)). A 40-case development
  policy corpus (20 text/12 voice-policy/8 photo-policy) covers controlled adversarial output.
- Voice upload, restricted decoding, private playback and budget-reserved English
  transcription; photo uploads share the bounded media path with normalized previews
  and literal unconfirmed label readings ([photo evidence](evidence/photo-progress.json)).
- Version-bound retrieval: exact codes, then PostgreSQL lexical ranking with explicit
  watt/CCT/IP constraints, then the embedding fallback. Suggestions carry current source
  versions and pages and need a written selection. Retired sources are excluded; outdated
  sources/pages, changed prices and invalid pack quantities block finalization
  ([semantic evidence](evidence/semantic-progress.json),
  [recovery evidence](evidence/media-retrieval-recovery.json)).
- Hostile transcript/label text and failure-path secret canaries pass through the real graph.
- Opt-in synthetic live canaries passed for Responses, transcription, vision and embeddings.
  LangSmith export was rejected with HTTP 429 on October 29; since November 3 each worker job
  is exported as one masked full-detail trace (decision D24).

Open before the remaining items can be checked:

- Item 2: done 2026-11-03 for the agent job path: masked full-detail tracing (D24) with a
  live trace read back from LangSmith ([evidence](evidence/langsmith-trace-canary-2026-11-03.json)).
  Transcription/label-reading spans are verified only with a fake HTTP session.
- Items 3-4: broader synonym/ambiguity retrieval evaluation (the development re-run
  after the null-SKU fix is done, see phase 6; e064 still misses its target).
- Item 2: reservations and limits are implemented; the per-endpoint rate evidence is
  tracked under phase 5 and ledger B-entries.

### Phase 4 - in progress (0 of 5 items; blocked on user accounts)

Implemented and locally tested only:

- GAS source lives in [`gas/`](../gas/README.md) and is pushed with clasp; signed edit
  callbacks reached the backend live on October 29. Full-snapshot import and the
  one-minute trigger are locally tested; `installSupplierSynchronization` has not been
  run, so no live snapshot exists ([GAS evidence](evidence/google-gas-progress.json)).
- Drive export (`gas/Exports.gs`, signed claim/receipt, digest-pinned retry, concurrent
  claim test) against a Python stand-in. It has not run in Google.
- WhatsApp adapter (signed webhook, allowlisted ingress, restricted media fetch,
  three-phase gated sending, monotonic receipts, concurrent duplicate test) against a
  mock Graph transport. No Meta account, number or tunnel has been used.

The live steps are in [morning actions](MORNING_ACTIONS.md). See
[Google synchronization](reference/GOOGLE_SYNC.md) and [WhatsApp channel](reference/WHATSAPP.md).

### Phase 5 - in progress (0 of 4 items)

Frontend task breakdown for items 1 and 4 (proposed 2026-11-03, not started):
[frontend work plan](proposals/2026-11-03-frontend-plan.md).

Implemented, not yet sufficient to check any item:

- Item 1: lazy `LightingScene` (React Three Fiber) with a reduced-motion static fallback
  and an error boundary (`app/frontend/src/features/overview/`). Reviewed 2026-11-03: keyboard
  and capture-privacy review done, an axe defect fixed, scene lazy-loaded
  ([evidence](evidence/scene-review-2026-11-03.json), `local-substitute`). Open: performance on
  a production build on real hardware, and a human keyboard/screen-reader pass.
- Item 2: API boundary tests (credential refusal, Auth outage 503, exact-origin CORS,
  security headers, 413, gateway route exposure, the 30/min mutation limit) and a
  secret-value scanner (`npm run check:secrets`)
  ([API evidence](evidence/api-boundaries-2026-11-02.json),
  [secret scan](evidence/secret-scan-2026-11-02.json)). Since 2026-11-03 every per-user,
  per-conversation and queue limit has an integration test
  (`tests/integration/test_admission_limits.py`) and a database outage is a safe 503. Known
  gap: failed requests are never rate limited (strict xfail test; decision in
  [morning actions](MORNING_ACTIONS.md)). Engineering ledger: 3 Covered,
  2 NotApplicable, 37 Planned ([ledger](engineering/coverage.json)). Open: a reviewed ledger.
- Item 3: concurrency tests (export claims, duplicate webhooks), a retention command
  (dry run by default, not scheduled) and a logical backup/restore drill
  ([drill evidence](evidence/backup-restore-drill-2026-11-02.json)). Since 2026-11-03: clean
  install and upgrade tests (`test_migrations.py`) and database/Storage outage tests
  (`test_outages.py`). Open: scheduled retention, Drive/provider-side retention, orphan
  Storage objects.
- Item 4: four screenshots from the verified browser run
  (`docs/evidence/screenshots/2026-11-02/`). On 2026-11-03 a whole-app review of 19 views at
  1440 x 1050 and 390 x 844 passed: zero axe violations, no overflow, no capture-mode privacy
  match, keyboard order and live updates checked, dev-server timings measured
  ([evidence](evidence/ui-review-2026-11-03.json), `local-substitute`). Not ticked. Open:
  production-build performance, a screen-reader and real-device review, and 24 px target sizes
  (recorded, not asserted).
  A later re-review of the same views, 14 views by axe, layout and target-size, also passed
  ([evidence](evidence/page-accessibility-review-2026-11-03.json), `local-substitute`).

The last fully green `npm run verify:full` is recorded in
[checkpoint evidence](evidence/checkpoint-2026-11-02.json) (283 passed). A later run
was stopped by memory pressure after `test:python` and `test:ui` passed; see the work log.

### Phase 6 - in progress (0 of 4 items)

- The 80 scenarios (40 text/24 voice/16 photo; 60 development/20 holdout, split by
  family), an evaluator-only answer key, 40 synthetic voice/photo assets, a validator,
  an offline baseline and an opt-in paid harness are in
  [`tests/fixtures/evaluation/`](../tests/fixtures/evaluation/README.md).
- Development run 1 (2026-11-02): 59/60 workflow, zero unsupported lines or unauthorized
  sends, Recall@5 2/4 ([evidence](evidence/evaluation-development-agent-2026-11-02.json)).
  It exposed a null-SKU candidate bug, fixed offline afterwards.
- Development run 2 (2026-11-02, after the fix): 60/60 workflow (55/60 exact primary
  action), 44/44 ambiguous first turns acted on, zero unsupported lines or unauthorized
  sends, Recall@5 3/4 (e031 now found; e064 still missed), median decision 5.4 s, p95
  9.9 s, estimated USD 0.013 (app estimate, not billing)
  ([evidence](evidence/evaluation-development-agent-run2-2026-11-02.json)). Development
  results on synthetic assets only; four retrieval cases are too few to judge the 95% target.
  Since 2026-11-03 the set has 14 labeled retrieval cases (9 development, 5 holdout) and seven
  rewritten scenarios, so runs 1 and 2 no longer describe the current fixtures.
- A holdout freeze guard refuses holdout runs without a matching freeze record and
  explicit confirmation. No freeze record and no holdout run exist.
- [Showcase shot list](SHOWCASE_SHOT_LIST.md) (nine shots, 90-120 s, each labeled Real,
  Local substitute or Not shown) and the screenshots above exist; no recording yet.

## Remaining work in order

Local work (no account needed):

1. ~~Relabel scenarios for Recall@5 before the freeze~~ Done 2026-11-03 (D22, D38): 14 labeled
   cases, 9 development and 5 holdout; seven text scenarios rewritten, validator checks each label
   against the catalog ([evidence](evidence/evaluation-relabel-baseline-2026-11-03.json), `local`).
   Paid development re-run done on 40 of 60 scenarios (D41), all traced in LangSmith (D42):
   [evidence](evidence/evaluation-development-agent-run3-2026-11-03.json), `synthetic`.
2. Phase 3: nested trace-redaction check; check items 2-4 only when their evidence exists.
3. Phase 5: the remaining rate/quota/capacity tests, outage and migration checks, the
   3D keyboard/performance/capture review, the visual/accessibility review and a reviewed ledger.
4. ~~A single fully green `npm run verify:full` on the final tree.~~ Done 2026-11-03: 13 of 13
   steps in one run ([evidence](evidence/checkpoint-2026-11-03.json), `local`). Later edits were
   docs, evidence and one live-test change; rerun it once more before the freeze.

Done by Claude in the browser (decision D37); the user only signs in, approves consent and enters codes:

5. Google: run `installSupplierSynchronization`, then the Drive export steps
   (see [morning actions](MORNING_ACTIONS.md)).
6. Meta: test number, credentials in `.env.local`, tunnel and a live send/receipt.
7. Confirm the agent is final; then freeze and run the holdout once.
8. ~~Record the local showcase from the shot list; review it for private data.~~ Recorded and
   reviewed 2026-11-03 ([evidence](evidence/showcase-recording-2026-11-03.json), `local-substitute`):
   silent 66 s clip, kept local; trim and narrate before publishing.

## Evidence and commits

Google work is documented in [the GAS setup guide](../gas/README.md),
[work log](WORK_LOG.md), and [GAS progress evidence](evidence/google-gas-progress.json).
Root `AGENTS.md` requires documentation updates after every completed step or
coherent file-change group and reading the rules at each project prompt. Commits
follow the phase-commit rule there; a progress checkpoint never checks a milestone.
