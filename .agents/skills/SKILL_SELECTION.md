# Skills for the supplier quotation app

Project-local selection updated on 2026-10-29. These are development instructions,
not installed application capabilities. No global skills or account settings were changed.

## Agreed product

An English web application for an electrical distributor. Customers communicate
through WhatsApp text and English voice notes. The assistant clarifies requirements,
retrieves supported product options, checks authoritative prices and availability,
and prepares quotations. Authorized salespeople review and approve exact revisions
before sending, handle exceptions, and can take over conversations.

Synthetic business files and test audio are permitted and labeled. Evaluation
results must distinguish local substitutes, provider sandboxes, live integrations,
and actual client pilots. No revenue or time-saving results are presumed.

## Project-specific skills

Visual requirement: deliver a distinctive, premium sales workspace with polished
motion and purposeful 3D when feasible. Use one memorable supplier-related scene,
with a static fallback and reduced-motion support. Preserve fast, accessible
conversation, quotation, and approval workflows. Choose the visual palette and
3D library during design; synthetic assets must not imply verified specifications.

- `plan-quotation-app`: specifications, architecture, scaffolding, and complete workflow slices.
- `integrate-whatsapp`: authenticated events, media, outbound delivery, deduplication, and recovery.
- `process-voice-notes`: English audio, transcripts, extracted fields, and ambiguity.
- `implement-human-approval`: clarification, durable pauses, exact-revision authorization, and takeover.
- `build-quotations`: prices, stock, deterministic arithmetic, revisions, and document parity.
- `automate-google-workspace`: Sheets, Drive, Gmail, Apps Script, and synchronization.
- `ingest-supplier-evidence`: versioned catalogs, exact identifiers, retrieval, and provenance.
- `secure-quotation-app`: customer/staff/company isolation, agent permissions, and data protection.
- `implement-abuse-controls`: shared rate limits, quotas, AI budget reservations, concurrency, backpressure, idempotency, and recovery, with adversarial acceptance scenarios.
- `evaluate-quotation-agent`: coherent synthetic datasets, hidden answer keys, and business scenarios.
- `verify-quotation-release`: reproducible local, sandbox, and deployment readiness evidence.
- `review-quotation-code`: specification and business-invariant review without assuming an issue tracker.
- `verify-engineering-coverage`: research-backed catalog of 42 commonly overlooked security, reliability, data, and AI concepts; requires explicit applicability and evidence-backed coverage during substantial planning, review, and release.

This coverage skill is the user's safeguard against relying on them to name
engineering controls. It includes definitions, project failure examples, a
coverage-ledger validator, and validator tests. It supplements implementation
skills rather than adding another generic security checklist. Planned or missing
controls are not Covered; a passing metadata validator is not proof of safety.

Read only the skills relevant to the current task. Verify changing provider APIs,
messaging policies, quotas, and execution identity against current official sources
when implementing an integration.

Security guidance includes definitions and implementation requirements for Auth,
RBAC/RLS, IDOR/BOLA, CORS/CSRF/XSS, SSRF, uploads/audio, prompt injection, tool
permissions, approval races, trace redaction, audit events, retention, and restore.
The new abuse-control skill and expanded secure-quotation-app references use OWASP
and Supabase primary guidance. Rates, budgets, and retention values remain explicit
configuration choices; no arbitrary production thresholds are presumed.
This addition changes development instructions only, not live enforcement.

## Retained general guidance

- `client-crud-state`: TanStack Query ownership, row-level pending feedback, canonical-response patches, rollback, and selective reconciliation.
- `react-feature-structure`: lean React/Vite feature boundaries and strict typed interfaces.
- `project-documentation`: proportionate setup, decision, architecture, runbook, and release documentation.
- `contribution-workflow`: requested Git/PR work using actual repository conventions and authorization.

The supplied eight-skill package is integrated through these four entrypoints and
references in frontend-design, plan-quotation-app, and secure-quotation-app.
Its generic coding principles are folded into the existing planning workflow.
UI direction, framework mechanics, review, coverage, release checks, and hook setup
each retain one primary owner. One TanStack Query cache owns remote UI data.
No Next.js backend, hosted limiter, additional agent harness, global Git settings,
or hook installation is introduced by the import.

Organization branding is removed from active skill names, descriptions, and
guidance. Original files and exact license notices are retained in a verified,
non-active [source archive](../skill-source-archives/user-supplied-2026-10-29/).
Its SKILL.md entrypoints are disabled. Rebranding does not change the original
license or grant public redistribution rights.

- `fastapi`: official framework guidance for validated APIs, dependencies, and streaming.
- `shadcn`: official component APIs, composition, theming, and project configuration.
- `langsmith-trace`: official instrumentation and trace diagnosis, under project redaction rules.

These three imports are pinned and licensed in the upstream manifest. shadcn
has a Codex metadata/context compatibility adaptation recorded with original hashes.
No application packages, CLI binaries, accounts, or traces were created.

## Approved stack

React, TypeScript, React Router, Vite, Tailwind CSS, shadcn/ui, and TanStack Query;
Python FastAPI/Pydantic; Python LangGraph; PostgreSQL with exact/text search and
pgvector; a durable PostgreSQL-backed Python worker; SSE; pytest and Playwright.
Use OpenAI for inference and English audio transcription, and LangSmith for
redacted tracing. The database, Auth, and private Storage use this project's
isolated local Supabase stack, quotation-local-dev, while the hosted account is
unavailable. Do not reuse the separate Smart RAG stack. Model names, budgets, and
production hosting remain separate decisions. Direct Meta developer testing and
Google Workspace/Apps Script remain the agreed integration approach.

Credentials stay backend-only. Imported CLI examples do not authorize feedback,
remote install scripts, raw trace exports, or publication of datasets.

## Additional upstream guidance

- `langgraph-fundamentals`: LangChain's state, graph routing, streaming, and language-specific implementation guidance.
- `langgraph-human-in-the-loop`: interrupts, validated resume input, and replay/idempotency mechanics; supplements `implement-human-approval`.
- `langgraph-persistence`: checkpointers, conversation threads, and persistent state; thread IDs do not replace authorization.

These three upstream skills are pinned to LangChain repository commit
`126c384d8552dcb476b226c244172186cc3f4328`. Their license and file hashes are
recorded in the upstream manifest. Installation adds guidance, not application
dependencies or paid hosting. Preserve exact-revision approval and dispatch
deduplication when adapting their examples. Verify API details against the chosen
package versions before implementation.

- `whatsapp-webhooks`: Hookdeck's imported Meta webhook handshake, signature checks,
  payload guidance, and example handlers. Supplements `integrate-whatsapp`; it does
  not replace our durable processing, human approval, or conversation ownership rules.

- `frontend-design`: initial visual direction grounded in the sales workflow.
- `impeccable`: focused UX refinement and visual verification within that direction.
- `web-design-guidelines`: accessibility and interaction review.
- `react-best-practices` (discovery name `vercel-react-best-practices`): applicable only if React/Next.js is chosen.
- `codebase-design`: maintainable interfaces and tests at meaningful seams.
- `security-audit`: guidance or a dedicated source-based audit according to the actual request.
- `setup-pre-commit`: configure appropriate checks once a toolchain exists; preserve existing hooks.
- `resolving-merge-conflicts`: only for an actual merge/rebase conflict, respecting user scope.

Choose one lead design workflow. Do not stack competing redesign procedures.
Imported skills do not grant authority to publish, send messages, commit, deploy,
or start independent agents beyond the user's request and applicable instructions.

## WhatsApp development choice

Use Meta Cloud API directly with its free developer testing setup and authorized
test recipients. No paid messaging provider or hosted gateway is required by this
selection. Confirm test restrictions, messaging policy, and any tunnel's limits at
implementation time. AI, transcription, and hosting costs are separate.

Hookdeck's skill was installed from commit
`c764bd14611072eb81fe55ff850c79963a456158`. Its MIT license and file hashes are
recorded with the import. No account, webhook, tunnel, or live message was created
by installing the skill.

## Removed and replaced guidance

Removed the old Hybrid/Graph RAG implementation, phase, frontend, structured-table,
security, scaffolding, and release skills. Their reusable requirements now appear
in the focused skills above, without missing phase-contract prerequisites or
assumptions about Arabic, LightRAG, ParadeDB, Supabase, or a particular deployment.

Removed iOS/course/Claude hook skills, overlapping UI packages, architecture
exploration, and generic implement/spec/review workflows that assumed unavailable
tools or an issue tracker. Local find-skills and skill-creator copies were removed;
platform skill authoring and discovery remain available when needed.

Recursive deletion was blocked by automatic approval review. The 23 retired skill
folders were instead moved to `retired-skills-2026-10-28/` outside the active
`skills/` directory, with their `SKILL.md` files renamed to `SKILL.md.disabled`.
They are recoverable reference copies and must not be loaded as project guidance.

## Provenance

Retained imports and their original recorded hashes are listed in
[`upstream-manifest.json`](upstream-manifest.json).
Project-authored skill hashes and retired folder names are recorded separately in
[`project-manifest.json`](project-manifest.json).
That manifest also records a local hash baseline for the unchanged existing
`impeccable` skill, whose upstream provenance was not present in the old manifest.
Upstream license files are preserved. This selection makes no claim that the
application is implemented, tested with clients, or production ready.
