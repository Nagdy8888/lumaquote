# LumaQuote implementation tracker

The agreed scope is the English commercial-lighting supplier quotation app.
Preserve all six milestones and the [testing plan](TESTING_PLAN.md).
Unchecked means unfinished, not a verified capability.

## Required code organization

Application code lives in `app/backend`, `app/frontend`, and `app/agents`.
Organize concrete features and infrastructure separately; keep application entry
points limited to composition. Avoid god files and speculative empty abstractions.
Every authored function and class requires meaningful inline documentation, not
only separate project docs. Root AGENTS.md defines the enforceable conventions.

## 1. Design and foundations
- [x] Premium graphite/copper workspace, responsive UI, self-hosted fonts, accessible primitives.
- [x] Native frontend/API/worker commands; isolated local Supabase; restricted DB identities.
- [x] Staff Auth, current membership, migrations/RLS/private file access, typed contracts.
- [x] 72 labeled synthetic products, six catalog PDFs, realistic requests and stock exceptions.
- [x] Real resource-bounded, network-disabled media sandbox.

## 2. Manual quotation workflow
- [x] Intake, clarification, evidence, product selection, deterministic Decimal totals.
- [x] Immutable revisions, PDF parity, exact customer/revision approval, rejection, takeover.
- [x] Durable inbox/jobs/outbox, honest delivery state, scoped idempotency and audit.
- [x] Unit/property/integration/composite/browser validation.

## 3. Persistent agent and media
- [x] PostgreSQL-backed LangGraph, restart/resume, customer and staff participation.
- [ ] OpenAI structured extraction, confirmed consequential media fields, evidence-backed matching.
- [ ] English transcription/photo intake, reservations and limits, redacted LangSmith tracing.
- [ ] Retrieval versions/citations, embeddings, ambiguity/injection/regression checks.

## 4. Live Google and WhatsApp
- [ ] Real Google OAuth, validated Sheet snapshots, signed Apps Script callbacks and 60s reconciliation.
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
- [ ] Screenshots, truthful 90â€“120s shot list, reproducible setup and verified release evidence.

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

gpt-6-luna Responses, gpt-transcribe, text-embedding-3-small (1536 dimensions).
Unavailable models are explicit blockers; never silently choose a costly fallback.
Google consent/Apps Script authorization and Meta test settings require the user's
accounts. Live tests and offline substitutes must be reported separately.

## Evidence and commits

Phase 1 checks are recorded in [phase-1 evidence](evidence/phase-1.json).
Phases 1 and 2 are locally verified; agent and external integration milestones remain unchecked.
Phase 2 checks are recorded in [manual workflow evidence](evidence/phase-2.json).
Early manual-flow tests do not establish live WhatsApp, model, or Google execution.

## Phase 3 progress (not complete)

Voice upload, restricted decoding, private playback, and budget-reserved English
transcription are implemented. Opt-in synthetic live canaries passed for Responses
and transcription. Consequential fields require explicit written confirmation;
model prose cannot authorize outbound commercial claims. A new worker resumes
persisted customer/staff interrupts without trusting browser approval payloads.
Photo intake, semantic retrieval/embeddings, broader evaluation and operational
recovery remain unfinished. LangSmith export is blocked by the account's monthly
trace allowance (HTTP 429), recorded in MORNING_ACTIONS.md. This is not a phase 3
completion or whole-app release claim.
