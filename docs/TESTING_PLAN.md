# LumaQuote testing plan

Status: requirements retained; test runners and substantial local coverage are
implemented. Current results and remaining gates are recorded in WORK_LOG.md
and docs/evidence artifacts; this plan does not itself certify completion.
The [tooling and test map](reference/TOOLING_AND_TESTS.md) explains actual commands,
fixture isolation, each test family's assertions and what existing evidence can
and cannot prove. Requirements below remain unchanged.
This document adds testing requirements to the agreed application plan. It keeps
the English commercial-lighting workflow, premium LinkedIn presentation, approved
stack, local-first release, and selective Docker decisions intact.

## What must be proved

A customer can send a request, clarify requirements, receive a quotation reviewed
by a salesperson, and see the correct delivery outcome. Evidence must also show
that forbidden, ambiguous, interrupted, and repeated actions behave safely.

Critical invariants:

- Money, quantities, units, discounts, and expiry follow deterministic rules.
- Catalog evidence supports product claims; validated Sheets records supply
  prices and stock. Missing evidence never becomes an invented specification.
- Only an authorized staff member can approve the exact current revision for
  the intended customer. Consequential changes invalidate approval.
- Staff takeover stops automated replies, including previously queued work that
  has not crossed the external dispatch boundary.
- Duplicate requests and retries do not blindly repeat business effects.
  An uncertain provider send remains unknown until reconciled.
- Company records, private files, approvals, and graph threads remain isolated.
- Spending and capacity are reserved before expensive work.
- UI state reflects persisted outcomes; submitted is not delivered.

## Test layers

### 1. Static and build checks

Run Python lint/type checks, TypeScript checks, frontend lint, and a production
build. Check generated API types against the FastAPI OpenAPI contract, migration
ordering, dependency lockfiles, and accidental server secrets in browser assets.
Triage dependency findings against the actual affected feature and version.

### 2. Unit tests

Use pytest for Python domain behavior and Vitest for meaningful frontend logic.
Test interfaces and outcomes rather than private implementation details.

- Decimal arithmetic, line totals, allowed discounts, rounding, currency, pack
  sizes, invalid quantities, and separately listed shipping.
- Seven-day quotation validity, source effective dates, timezone boundaries,
  expiry, revision identity, and approval invalidation.
- Requirement validation, missing consequential fields, supported product
  alternatives, policy selection, and deterministic dispatch eligibility.
- Rate/quota/budget decisions, retry classification, redaction, and state
  transitions, including delivery events arriving out of order.

Use fake clocks, deterministic IDs, and independent expected calculations.
Do not call OpenAI, Meta, Google, or LangSmith in unit tests.

### 3. Property and state-machine tests

Use Hypothesis for rules with many input combinations, rather than writing large
lists of similar examples.

- Valid line items always reconcile with documented quotation arithmetic;
  negative, non-finite, excessive, or invalid-unit values cannot enter a quote.
- Repeated edit/reject/approve/expire/takeover sequences cannot make an obsolete
  revision dispatchable or grant authority to a customer message.
- Replaying the same event does not create another logical effect. A reused
  idempotency key with a different payload is rejected.
- Budget reservations and release/reconciliation transitions preserve the
  accounting invariant under repeated operations and partial failure.

Keep generated examples bounded, record seeds, and preserve useful failures as
explicit regression cases.

### 4. Frontend component tests

Use React Testing Library with Vitest for interactive components that have
meaningful state: quotation editing, approval, takeover, voice-note review,
evidence selection, and integration recovery.

Check loading, empty, validation, forbidden, stale-version, pending, failed, and
retry states. Ensure double-clicks cannot create duplicate actions, failed edits
reconcile with the server, and consequential actions require server confirmation.
Check accessible names, keyboard behavior, and focus after dialogs and errors.
Avoid tests that only confirm static text or copy component internals.

### 5. API and provider contract tests

Exercise FastAPI routes with valid and invalid requests, authentication, role
checks, conflict responses, scoped idempotency, pagination, and bounded uploads.
Verify the generated frontend client handles real API responses and errors.

Use sanitized, versioned provider fixtures for WhatsApp verification and signed
raw-body events, batched messages/receipts, media downloads, Google pagination and
errors, signed Apps Script callbacks, model structured output, and trace exports.
Cover unknown fields, malformed responses, expiry, authorization failures, 429s,
timeouts, and server errors. Fixture tests prove adapter behavior against those
contracts; live smoke tests separately check the actual provider connection.

### 6. Database and infrastructure integration tests

Use real local PostgreSQL/Supabase for transactions, constraints, RLS, private
Storage, retrieval queries, jobs, outbox, and LangGraph checkpoints.

- Test anonymous, authenticated staff, restricted worker, and privileged
  administrative paths explicitly. Do not use a superuser to prove RLS.
- Exercise direct REST/RPC/Storage access as well as FastAPI, including cross-
  company IDs, changed memberships, and forbidden property updates.
- Verify atomic approval plus dispatch intent, unique inbox/outbox keys,
  foreign keys, source versions, checkpoint ownership, and lease fencing.
- Test exact SKU matching, vector/text retrieval, document-version replacement,
  citations to the correct original PDF page, and stale evidence rejection.

Use disposable databases for schema/migration/restore tests where feasible, and
dedicated synthetic tenants and private object prefixes for Supabase API tests.
Require an explicit local test target; refuse hosted URLs and unscoped cleanup.
Never reset the developer database or touch another project's containers/volumes.
Use separate real database connections for concurrency tests.

### 7. Composite workflow tests

Here, composite means several real application modules working together through
their business interfaces: API, persisted graph, domain services, database,
worker, and outbox. Replace only external providers with controlled test adapters.

Required scenarios:

1. Text request -> missing requirement -> clarification -> cited product match
   -> validated prices/stock -> draft -> human approval -> PDF -> delivery event.
2. Voice note with an ambiguous quantity -> customer confirmation -> correct
   draft; a product-label photo follows the same confirmation rules.
3. Unavailable/discontinued product -> supported alternative or staff escalation;
   an unsupported compatibility claim cannot enter a final quotation.
4. Customer revision or consequential Sheet edit after approval -> old approval
   invalidated -> new revision -> another authorized review before dispatch.
5. Staff takeover while agent work or a reply is queued -> dispatch gate blocks
   unsent automation; the UI reports anything already submitted honestly.
6. Staff rejection, duplicate resume, and worker restart while awaiting approval
   -> durable state restored without repeated side effects.
7. Drive export failure after WhatsApp submission -> retry only the export,
   preserving the canonical PDF and avoiding another customer message.
8. Sheets unavailable, stale, or malformed -> visible blocked finalization;
   recovery requires a validated snapshot, not a silent fallback to old prices.

These tests are the main proof that individual components form a working product.

### 8. Browser end-to-end tests

Use Playwright against the running native frontend, API, worker, and local
Supabase. Default browser tests use controlled external adapters and synthetic
data, with that mode clearly labeled.

Cover login, inbox, audio playback/transcript review, clarification, original-page
evidence, quote edits, stale approval conflicts, approve/send, takeover, delivery
failure, refresh, logout, SSE disconnect/reconnect, and expired staff access.
Check that reconnecting reconciles persisted state without duplicate activity.

Test a full desktop workflow and a representative narrow/portrait workflow.
Check the quotation PDF's readable content, totals, customer, revision, validity,
page breaks, and clipping with structured assertions plus rendered-page review.
Compare the Drive copy with the canonical PDF byte-for-byte; do not require
unrelated regenerated PDFs to share bytes when metadata can legitimately differ.

### 9. Agent, RAG, voice, and photo evaluation

Keep the agreed 80 scenarios: 40 text, 24 voice, and 16 photo; 60 development and
20 untouched holdout cases. Split by scenario family so paraphrases or recordings
of the same request cannot leak across the boundary. Expected answers stay
outside runtime retrieval, prompts, accessible metadata, and inference traces.

Include unclear speech, spoken model codes, unit confusion, background noise,
unclear labels, missing specifications, outdated catalogs, unsupported products,
prompt injection, and legitimate requests where the correct action is to ask.
Do not rely entirely on artificially clean generated speech or label images.

Evaluate consequential field accuracy, correct clarification/escalation, product
matching, evidence provenance, deterministic totals, approval binding, and final
workflow outcome. Use independent assertions and staff review for consequential
ambiguity; an LLM judge alone cannot approve a safety-critical result.

Targets from the agreed plan:

- Retrieval recall@5 >= 95% on applicable, labeled product-retrieval cases.
- Successful workflow outcomes >= 90% across the defined scenario suite.
- Zero unauthorized sends and zero unsupported final quotation lines.
- Every ambiguous consequential field triggers clarification or staff review.

Report counts and denominators by modality and split, not just a pooled score.
Freeze code, prompts, model configuration, and fixtures before the holdout run.
If results drive changes, that holdout is no longer untouched; label subsequent
results accordingly and use new reserved cases for a new holdout claim.
Compare retrieval/agent outcomes with a simple exact-SKU/text-search baseline.

### 10. Security, privacy, and abuse tests

Assess all 42 concepts in the project's engineering coverage catalog, marking
applicability and recording implementation plus behavioral evidence. The ledger
validator supplements inspection; it does not certify security.

Prioritize cross-company access, stale privileges, direct Supabase bypasses,
approval spoofing, webhook signature/replay handling, SQL/command/XSS payloads,
SSRF, hostile documents/transcripts, unauthorized agent tools, and secret leakage.
Check API/SSE/file access after membership revocation and private cache behavior.

Test rate limits at the boundary and under concurrent processes; test the last
available budget reservation, full queues, per-conversation ordering, exhausted
quotas, and unavailable enforcement. All expensive paths must use the controls.

Upload tests include wrong MIME/content, corrupt and oversized files, image
decompression limits, long audio, parser hangs, and scanned PDFs that must be
rejected in the native-text-only first release. Confirm the processing sandbox
has no network, credentials, or unrestricted host access, and enforce resource
and wall-clock limits against an actual running sandbox.

Inject synthetic PII/secret canaries into nested tools, model calls, exceptions,
and attachments. Inspect logs, browser assets, errors, local trace payloads, and
an authorized live LangSmith trace for leaks before real customer data is used.

### 11. Concurrency, fault injection, and recovery tests

Use controlled barriers and explicit failure points rather than timing sleeps.

- Two staff approve/edit the same revision, takeover races with dispatch, a
  source changes at finalization, and duplicate callbacks race across workers.
- Crash before/after an inbox commit, checkpoint, approval/outbox transaction,
  external submission, and delivery receipt; restart and inspect durable results.
- Expire a worker lease, allow another worker to claim it, and prove the stale
  worker cannot commit or send using its old fencing token.
- Simulate provider acceptance followed by a lost response. Keep the result
  unknown for reconciliation rather than claiming exactly-once external delivery.
- Reorder and repeat webhook receipts; delivery status must not regress.
- Inject timeouts, 429s, outages, poison jobs, and invalid source snapshots.
  Verify bounded retries, deadlines, visible recovery, and no retry storm.

Test clean migrations and upgrades with pending synthetic jobs/approvals. Restore
database records and required private files in isolation, then resume a business
workflow. Exercise the agreed 7-day media and 90-day business-record retention,
including derived vectors, checkpoints, external copies, and backup exceptions.
Record measured local restore time and recoverable data; public-service RPO/RTO
commitments belong to a later hosting decision.

### 12. Performance, accessibility, and visual acceptance

Measure local API latency, queue wait, provider processing, end-to-end latency,
concurrency, and usage separately. Target the agreed p95 of 12 seconds for text
and 25 seconds for bounded voice/photo fixtures, with sample sizes and hardware
recorded. Do not mix stub-provider timings with live-provider results or include
human clarification/approval wait in machine-processing latency.

Load tests use provider stubs by default. Exercise the agreed two active model
workflows, one per conversation, and 100-item queue limit; verify overload remains
bounded and staff review remains usable. Paid load testing is not a default.

Use automated accessibility checks with Playwright/axe plus manual keyboard,
focus, screen-reader spot checks, contrast, and reduced-motion review. Test
WebGL unavailable, slow asset loading, animation paused, and static 3D fallback.
The entire business workflow must remain usable without the 3D scene.

Capture visual baselines for Overview, Inbox, evidence, quotation approval, and
Integrations at desktop and portrait sizes. Review intentional baseline changes.
Stabilize time, fonts, synthetic data, and animation for screenshot comparisons;
review the live 3D scene separately on a supported browser.

Review LinkedIn capture mode for personal identifiers in every visible surface:
conversation, transcript, evidence, PDF, activity, tooltips, and errors. Hide
diagnostics without disguising failures. Show real stored activity and retain
clear synthetic-data disclosure; do not fabricate savings or customer results.

## Live integration acceptance

Run a small, explicit provider smoke suite after local checks pass:

1. Receive real text, English audio, and a product-label photo from an authorized
   WhatsApp test recipient; complete clarification, staff approval, PDF sending,
   and observed delivery receipts where the test environment provides them.
2. Edit the authorized Google Sheet manually and via API; verify Apps Script
   notification and periodic reconciliation respectively. Confirm a consequential
   change blocks an old approval and a fresh revision can be reviewed.
3. Export the identical quotation PDF to authorized Drive storage. Revoke or
   expire integration access and verify visible, recoverable failure.
4. Verify an actual redacted trace in the intended LangSmith project. Run bounded
   live OpenAI text/transcription/photo checks within the remaining allowance.

A missing credential, consent, provider permission, or test-recipient setup is
Blocked or Not Run, never a substituted pass. Keep this suite opt-in, separate
from normal CI, with explicit test-recipient/file allowlists and spending checks.
No real client records or unsolicited messages are needed.

## Environments and execution

Use pytest, Hypothesis, Vitest/React Testing Library, and Playwright/axe as planned
test tools. Pin compatible versions when implementing; they are not installed by
this document. Add named commands for static, unit, integration, composite,
browser, security, evaluation, performance, and live suites as each becomes real.
Do not add placeholder commands that pass without running their intended checks.

Most tests run as native processes. Docker remains limited to the existing local
Supabase services and the untrusted file-processing sandbox. Browser runners,
API, worker, UI, and test orchestration do not need Docker. A test network policy
must deny external provider traffic unless the live suite is explicitly enabled.
Browser tests may contact only the application and declared local test services.

Isolate parallel tests with database namespaces, synthetic users, thread IDs,
object prefixes, and scoped cleanup. Multi-process/race tests need committed data
and independent connections rather than rollback-only single-connection fixtures.
Store artifacts without credentials, signed URLs, or private customer content.

For pull requests, run static/build/unit/property/component tests, local provider
contracts, relevant real database/integration/composite tests, and a focused
browser smoke workflow. Broader browser/security/recovery checks run before a
milestone is accepted; full quality/performance/restore suites run at their release
gates and after relevant changes. Live paid evaluations are opt-in and budgeted.
Once the frozen release suites pass, rerun only when changes or failures justify
it. Fix flaky tests rather than retrying until green; mandatory quarantined tests
remain unresolved gates.

## Tests within the existing milestones

1. **Design and foundations:** test-target safeguards, fixture/answer-key
   separation, initial contracts, auth/RLS, schema constraints, sandbox isolation,
   build, and keyboard/viewport checks for the first reviewable workspace.
2. **Manual quotation workflow:** unit/property tests for calculations and
   revisions; real database approval/outbox tests; composite and browser tests
   for a complete manually operated request-to-quotation slice; PDF review.
3. **Persistent agent and media:** graph interruption/restart/resume, ambiguity,
   retrieval/provenance, malicious content, controlled text/audio/photo scenarios,
   spending reservations, and local/nested trace-redaction checks.
4. **Live Google and WhatsApp:** provider contract negatives, signed callbacks,
   stale-source races, reconciliation, duplicate/unknown sends, and the bounded
   real WhatsApp/Sheets/Drive/OpenAI/LangSmith smoke checks.
5. **Visual finish and safeguards:** desktop/portrait visual checks, accessibility,
   3D fallback/performance, capture privacy, full authorization/abuse checks,
   concurrency/failure injection, migrations, retention, and isolated restore.
6. **Frozen evaluation and showcase:** full local regression, frozen 80-case
   evaluation with separate holdout reporting, measured latency/usage, reviewed
   engineering coverage, final live integration evidence, screenshot/recording
   review, and reproducible setup/evidence documentation.

Add regression checks as behavior is implemented; testing is part of each slice,
not work postponed until the visual finish milestone.

## Completion evidence

For every required suite, record Passed, Failed, Blocked, or Not Run; revision,
environment, dependency/model/prompt/fixture versions; command or manual steps;
scenario counts; sanitized artifacts; and unresolved failures. Distinguish local
adapters, provider test environments, and real external calls.

Critical invariant failures block the relevant milestone or release regardless of
average quality score or code coverage. Use branch coverage to find omissions in
money, approval, authorization, spending, and dispatch behavior; a coverage number
alone is not acceptance evidence. Do not impose arbitrary 100% coverage on UI
markup or write tests that simply mirror implementation.

All applicable release checks and the engineering coverage review must pass
before calling the workflow ready for the recorded showcase. Synthetic evaluation
and a working WhatsApp test do not establish real business impact or production
hosting readiness. Estimated model usage remains distinct from provider billing.

Related references: [local setup](../LOCAL_DEVELOPMENT.md),
[evaluation skill](../.agents/skills/evaluate-quotation-agent/SKILL.md),
[release verification](../.agents/skills/verify-and-review/references/verify-quotation-release/GUIDE.md), and
[engineering coverage catalog](../.agents/skills/verify-and-review/references/engineering-coverage/references/concepts.json).
