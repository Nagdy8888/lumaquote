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

Google integration decision (user approved October 29): use Apps Script only for
Google Workspace access. GAS sends HMAC-signed complete snapshots after edits and
on a one-minute timer to the backend. No backend Google OAuth client/refresh token
or Google Cloud setup is required. The phase 4 Google OAuth requirement is fulfilled
through the user's Apps Script authorization rather than a separate backend grant.
Drive exports must also use GAS and preserve the canonical approved PDF; that
adapter remains unfinished. One-minute scheduling is approximate, not a 60-second
delivery guarantee. Milestone checkboxes remain pending live verification.

gpt-6-luna Responses, gpt-transcribe, text-embedding-3-small (1536 dimensions).
Unavailable models are explicit blockers; never silently choose a costly fallback.
Google consent/Apps Script authorization and Meta test settings require the user's
accounts. Live tests and offline substitutes must be reported separately.

## Evidence and commits

Google work from this chat is documented in [the GAS setup guide](../gas/README.md),
[work log](WORK_LOG.md), and [GAS progress evidence](evidence/google-gas-progress.json).
Local snapshot tests and live signed edit callbacks passed. Live full-snapshot
import, periodic timer execution and Drive export remain pending; phase 4 is not
complete. Root `AGENTS.md` requires documentation updates after every completed
step or coherent file-change group and reading the rules at each project prompt.

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
Photo intake and version-bound semantic retrieval/embeddings are implemented in
the working tree with targeted database checks and a full local regression pass.
Broader evaluation and remaining operational safeguards are unfinished. LangSmith
export encountered an account monthly trace allowance rejection (HTTP 429) on
October 29; current availability has not been reverified. This is not a phase 3
completion or whole-app release claim.

The current descriptive retrieval baseline uses exact codes first, then PostgreSQL
lexical ranking and explicit watt/CCT/IP constraints. Suggestions carry current
source versions and original pages and require a written selection. Retired
sources are excluded; outdated source/pages, changed prices and invalid pack quantities block old finalization.
Generated development queries are reported separately from the frozen 80-case
suite. Paid semantic fallback and broader synonym/ambiguity evaluation remain pending.

Photo intake progress: private image uploads now share bounded media processing
with voice notes; normalized previews and literal unconfirmed label readings are
implemented. Local provider-boundary tests and a synthetic vision canary passed.
Browser/full regression verification passed with paid inference disabled; no new
milestone is checked yet because broader evaluation/integration gates remain.
