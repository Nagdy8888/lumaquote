# Graph Report - Demo_Project_4  (2026-11-03)

## Corpus Check
- 316 files · ~227,608 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 40 file(s) not represented in the graph (top: .mmd 19, .css 8, (none) 5)

## Summary
- 2793 nodes · 6407 edges · 152 communities (105 shown, 47 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 385 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `31967999`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- psycopg
- semantic.py
- CatalogSearch
- October 29, 2026 - Offline embedding contract tests and engine recovery result
- conversation
- errors.py
- frontend/package.json
- test_whatsapp.py
- evaluation_dataset.py
- database
- test_drive_exports.py
- hashlib
- cn
- write
- vitest
- DomainError
- Button
- media_reading.py
- ask
- extraction.py
- settings
- nodes/retrieval.py
- re
- io
- scripts
- upload_audio
- workspace/schemas.py
- test_channel_contracts.py
- skills.py
- Apps Script transport and validated commercial snapshots
- test_trace_masking.py
- LumaQuote working rules
- begin
- index.cjs
- observability.py
- outbound.py
- test_summarize_post_hoc.py
- steps
- retention.py
- Design System: LumaQuote
- useQuotationDraft
- google.cjs
- compilerOptions
- ui-review.cjs
- job-recovery
- quotation-approval
- Test layers
- Persistent data, privileges and migration lifecycle
- test_browser_workflow.py
- LumaQuote implementation tracker
- components.json
- Work log
- main
- AppShell.tsx
- json
- documents.py
- check_frontend.cjs
- freeze_evaluation.py
- InputRecord
- Frontend ownership, server state and interaction contracts
- manual-workflow.cjs
- test_embedding_contracts.py
- ConversationThread.tsx
- staff
- bindings
- whatsapp-channel
- LumaQuote
- start-local-supabase.cjs
- frontend-live-updates
- diagrams
- system-boundaries
- staff-operation
- google-snapshot
- drive-export
- evidence-data
- package.json
- test_agent_on_development_scenario
- estimated-allowance
- frontend-draft
- verification-scope
- catalog.test.cjs
- StrictModel
- conversation-data
- Local Supabase
- health
- check_architecture.py
- Voice and product-label media lifecycle
- LumaQuote
- Configuration and native process operation
- ref_node_fs
- captureText
- LumaQuote architecture
- Backend contracts and business transactions
- appsscript.json
- WhatsApp channel (Meta Cloud API)
- queue_drive_export
- Sales and agent workflows
- test_agent_semantic_fallback_preserves_action_and_source_boundaries
- test_every_response_is_private_nosniff_and_unframed
- post
- Frontend work plan (for Sonnet execution)
- Visual guide to LumaQuote
- Project documentation
- test_operator_index_settles_or_blocks_uncertain_retries
- rule-enforcement
- Tasks
- CLAUDE.md
- Verified OpenAI contracts
- Showcase shot list (90-120 seconds)
- UI_DIRECTION.md
- test_workspace_integrations.py
- Proposal: working rules, skill routing and documentation (draft for approval)
- Working rules, skill routing and their enforcement
- Retry
- lumaquote
- scripts
- Development tooling, verification and evidence interpretation
- TestEnvironment
- test_live_evaluation.py
- test_signed_callback_receipts
- docs_root
- test_r15_bash_guard
- requirement-policy/README.md

## God Nodes (most connected - your core abstractions)
1. `DomainError` - 118 edges
2. `October 29, 2026 - Offline embedding contract tests and engine recovery result` - 92 edges
3. `database()` - 72 edges
4. `get_detail()` - 71 edges
5. `create_request()` - 63 edges
6. `settings()` - 58 edges
7. `post()` - 58 edges
8. `cn()` - 42 edges
9. `make_draft()` - 38 edges
10. `conversation()` - 36 edges

## Surprising Connections (you probably didn't know these)
- `Agent fallback and publication recheck` --references--> `ask()`  [INFERRED]
  docs/reference/CATALOG.md → app/agents/luma_agent/nodes/workflow.py
- `Command ownership` --references--> `prepare()`  [INFERRED]
  docs/reference/TOOLING_AND_TESTS.md → app/agents/luma_agent/nodes/workflow.py
- `2. Principles` --references--> `review()`  [INFERRED]
  docs/proposals/2026-11-03-working-rules.md → app/agents/luma_agent/nodes/workflow.py
- `Two-step approval confirmation` --references--> `review()`  [INFERRED]
  docs/reference/FRONTEND.md → app/agents/luma_agent/nodes/workflow.py
- `Unit and component coverage` --references--> `has_explicit_lines()`  [INFERRED]
  docs/reference/TOOLING_AND_TESTS.md → app/agents/luma_agent/requirements.py

## Import Cycles
- None detected.

## Communities (152 total, 47 thin omitted)

### Community 0 - "psycopg"
Cohesion: 0.04
Nodes (46): test_private_pdf_is_never_cacheable(), test_retrieval_requires_settled_room_and_cannot_repeat(), search(), test_authoritative_family_is_searchable_when_name_uses_different_words(), test_changed_product_evidence_requires_another_review(), test_description_lookup_retains_original_page_version_and_explicit_specs(), test_exact_sku_precedes_descriptive_similarity(), test_retired_catalog_cannot_be_recommended_or_finalized() (+38 more)

### Community 1 - "semantic.py"
Cohesion: 0.11
Nodes (13): index_company(), embedding_inputs(), has_current_embeddings(), publish_embeddings(), semantic_search(), vector_literal(), Cache identity and vector validation, Operator indexing (+5 more)

### Community 2 - "CatalogSearch"
Cohesion: 0.08
Nodes (18): query_constraints(), SearchCriteria, candidate_question(), search_catalog(), search(), CatalogHit, CatalogSearch, Agent fallback and publication recheck (+10 more)

### Community 3 - "October 29, 2026 - Offline embedding contract tests and engine recovery result"
Cohesion: 0.03
Nodes (79): 2026-10-29 - Agent fallback boundary tests added, 2026-10-29 - Agent fallback checks passed and evidence consolidated, 2026-10-29 - All Mermaid views rendered locally, 2026-10-29 - Configuration and verification reference coverage, 2026-10-29 — Current workflow documentation and screenshot reviewed, 2026-10-29 — Database gates passed; browser startup assertion failed, 2026-10-29 - Deep agent, media and retrieval references, 2026-10-29 - Deep backend and persistence documentation (+71 more)

### Community 4 - "conversation"
Cohesion: 0.05
Nodes (36): _deliver_local(), deliver_one(), claim_job(), recover_expired(), enqueue(), audit(), accept_customer_text(), change_ownership() (+28 more)

### Community 5 - "errors.py"
Cohesion: 0.04
Nodes (20): source_pdf(), accept_hint(), EditHint, verify_hint(), verify_mapping(), verify_signature(), claim_export(), drive_filename() (+12 more)

### Community 6 - "frontend/package.json"
Cohesion: 0.04
Nodes (57): dependencies, class-variance-authority@^0.7.1, clsx@^2.1.1, cn@^0.4.0, @fontsource/ibm-plex-sans@^5.3.0, @fontsource-variable/space-grotesk@^5.3.0, lucide-react@^1.63.0, radix-ui@^1.8.1 (+49 more)

### Community 7 - "test_whatsapp.py"
Cohesion: 0.08
Nodes (28): conversation_for(), deliver_webhook(), drain(), envelope(), graph(), Graph, outbox(), queue_reply() (+20 more)

### Community 8 - "evaluation_dataset.py"
Cohesion: 0.04
Nodes (28): 2026-11-02 - Holdout freeze guard (phase 6 preparation, offline), catalog_model(), _check_outcome(), _check_retrieval(), _check_structure(), _check_turns(), subtotal(), supported() (+20 more)

### Community 9 - "database"
Cohesion: 0.07
Nodes (24): rate_limit(), database(), domain_error(), response_boundaries(), operation(), membership(), customer_reply(), detail() (+16 more)

### Community 10 - "test_drive_exports.py"
Cohesion: 0.07
Nodes (22): 2026-11-02 - Concurrency tests, showcase shot list and screenshots; CI result, load_secrets(), main(), run(), scan_files(), tracked_files(), approve(), approved_quote() (+14 more)

### Community 11 - "hashlib"
Cohesion: 0.05
Nodes (24): 2026-11-02 - Synthetic voice/photo assets, paid development agent run and retrieval bug fix (phase 3), docker(), main(), object_paths(), prepare_scratch(), run(), snapshot(), source_params() (+16 more)

### Community 12 - "cn"
Cohesion: 0.11
Nodes (31): SignIn(), NewRequest(), cn(), Badge(), badgeVariants, Empty(), EmptyContent(), EmptyDescription() (+23 more)

### Community 13 - "write"
Cohesion: 0.15
Nodes (6): test_r10_ticked_items_need_evidence_and_phase_4_needs_live(), test_r6_edit_guard_warns_on_large_deletions(), test_r8_flags_mojibake_crlf_and_broken_links_but_not_quoted_code(), test_r9_requires_header_and_allowed_label_for_new_evidence(), test_skills_frontmatter_and_routing(), write()

### Community 14 - "vitest"
Cohesion: 0.16
Nodes (17): AudioWaveform(), decodeAudioData(), MediaPreview(), load(), computePeaks(), formatClock(), normalizePeaks(), view() (+9 more)

### Community 15 - "DomainError"
Cohesion: 0.06
Nodes (21): digest(), DomainError, authorize_outbound(), configured(), persist(), receive(), decide(), check_quotation() (+13 more)

### Community 16 - "Button"
Cohesion: 0.12
Nodes (31): App(), CatalogPage(), InboxPage(), connections, ConnectionsPage(), NotFoundPage(), LightingScene, Overview() (+23 more)

### Community 17 - "media_reading.py"
Cohesion: 0.18
Nodes (9): MediaReading, _read_label(), read_media(), extract(), masked_or_off(), model_call(), set_outputs(), tracing_enabled() (+1 more)

### Community 18 - "ask"
Cohesion: 0.10
Nodes (22): build_graph(), route(), ask(), clarify(), prepare(), review(), AgentState, F6 - Portrait inbox with a section switcher (G6) (+14 more)

### Community 19 - "extraction.py"
Cohesion: 0.06
Nodes (25): baseline_extract(), clarification_for(), has_explicit_lines(), Extraction, RequestedLine, parse_written_request(), Extraction and consequential-field confirmation, Integration coverage by responsibility (+17 more)

### Community 20 - "settings"
Cohesion: 0.12
Nodes (12): settings(), Settings, delete_files(), get_file(), put_file(), storage_headers(), main(), stable() (+4 more)

### Community 21 - "nodes/retrieval.py"
Cohesion: 0.22
Nodes (4): embed_texts(), validate_embedding_provider(), assert_request_version(), retrieve()

### Community 22 - "re"
Cohesion: 0.10
Nodes (13): degrade(), draw_label(), font(), main(), make_photo(), make_voice(), mix(), noise() (+5 more)

### Community 23 - "io"
Cohesion: 0.13
Nodes (7): bounded_output(), process_file(), Fixed sandbox boundary, test_corrupt_files_are_rejected(), test_image_is_normalized_without_metadata(), test_native_pdf_retains_original_page_text(), test_overlong_audio_is_rejected_before_transcription()

### Community 24 - "scripts"
Cohesion: 0.06
Nodes (35): scripts, build, check:architecture, check:docs, check:frontend, check:rules, check:secrets, db:configure (+27 more)

### Community 25 - "upload_audio"
Cohesion: 0.19
Nodes (4): audio_playback(), image_preview(), upload_audio(), upload_image()

### Community 26 - "workspace/schemas.py"
Cohesion: 0.09
Nodes (14): ActivityView, CompanyView, ConversationDetail, ConversationView, DeliveryView, JobView, MessageView, ProductView (+6 more)

### Community 27 - "test_channel_contracts.py"
Cohesion: 0.06
Nodes (16): ClaimRequest, ExportEnvelope, ReceiptRequest, extract_events(), handshake(), message_event(), status_event(), valid_signature() (+8 more)

### Community 28 - "skills.py"
Cohesion: 0.12
Nodes (13): active_skills(), check_frontmatter(), check_links(), check_manifests(), check_mirror(), check_routing(), digest(), located() (+5 more)

### Community 29 - "Apps Script transport and validated commercial snapshots"
Cohesion: 0.08
Nodes (23): drive_export_claim(), drive_export_receipt(), signed_body(), supplier_snapshot(), Apps Script transport and validated commercial snapshots, Atomic publication and offer freshness, Authority and process boundary, Diagnosis without leaking integration data (+15 more)

### Community 30 - "test_trace_masking.py"
Cohesion: 0.05
Nodes (22): Evidence limits, Frontend phase 5 follow-ups (2026-11-03), Google callback preparation, Google Workspace / clasp, LangSmith account limit, Latest verification, Local Docker / WSL availability, Morning actions (+14 more)

### Community 31 - "LumaQuote working rules"
Cohesion: 0.15
Nodes (12): Code layout, Commands, Documentation (decisions D30, D33), LumaQuote working rules, Rules, Skill routing, Unattended work and accounts, AI, evaluation and tracing (+4 more)

### Community 32 - "begin"
Cohesion: 0.16
Nodes (8): allowed_senders(), begin(), block(), record(), Egress, Inbound media, Ingress, Module and call flow

### Community 33 - "index.cjs"
Cohesion: 0.15
Nodes (20): crypto, embeddedBlock(), existingFile(), fingerprint(), fs, hash(), path, readCatalog() (+12 more)

### Community 34 - "observability.py"
Cohesion: 0.09
Nodes (14): configured_secrets(), finish(), flush(), job_trace(), mask(), mask_text(), masked_client(), reset() (+6 more)

### Community 35 - "outbound.py"
Cohesion: 0.11
Nodes (13): submit(), call(), download(), endpoint(), fetch_media(), GraphError, headers(), make_client() (+5 more)

### Community 36 - "test_summarize_post_hoc.py"
Cohesion: 0.22
Nodes (5): pin(), run_summarizer(), test_changed_or_missing_pin_is_refused_without_post_hoc(), test_matching_pin_is_scored_normally(), test_post_hoc_flag_labels_the_report()

### Community 37 - "steps"
Cohesion: 0.09
Nodes (21): VITE_SUPABASE_ANON_KEY, VITE_SUPABASE_URL, jobs, local-contracts, runs-on, steps, timeout-minutes, name (+13 more)

### Community 38 - "retention.py"
Cohesion: 0.17
Nodes (9): connect(), expired_media(), idle_conversations(), main(), purge_conversations(), purge_media(), purge_records(), run() (+1 more)

### Community 39 - "Design System: LumaQuote"
Cohesion: 0.10
Nodes (21): Buttons, Cards / Containers, Chips, Colors, Components, Design System: LumaQuote, Do:, Do's and Don'ts (+13 more)

### Community 40 - "useQuotationDraft"
Cohesion: 0.21
Nodes (11): EditableLine, draftSuite(), capturesLatestCleanVersion(), preservesConflict(), fixture(), useQuotationDraft(), beginEdit(), updateDiscount() (+3 more)

### Community 41 - "google.cjs"
Cohesion: 0.15
Nodes (8): fs, path, root, { spawnSync }, executable, path, root, { spawn }

### Community 42 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, baseUrl, esModuleInterop, jsx, lib, module, moduleResolution (+10 more)

### Community 43 - "ui-review.cjs"
Cohesion: 0.26
Nodes (12): { chromium }, fs, keyboardPass(), livePass(), main(), measure(), PRIVATE, reviewView() (+4 more)

### Community 44 - "job-recovery"
Cohesion: 0.11
Nodes (19): app/agents/luma_agent/lease.py, app/agents/luma_agent/runtime/jobs.py, app/agents/luma_agent/runtime/recovery.py, app/backend/luma/features/media/intake.py, app/backend/luma/features/media/persistence.py, job-recovery, media-lifecycle, bindings (+11 more)

### Community 45 - "quotation-approval"
Cohesion: 0.11
Nodes (19): app/agents/luma_agent/runtime/delivery.py, app/backend/luma/features/conversations/participation.py, app/backend/luma/features/quotations/approval.py, app/backend/luma/features/quotations/drafting.py, app/backend/luma/features/quotations/freshness.py, quotation-approval, sales-workflow, bindings (+11 more)

### Community 46 - "Test layers"
Cohesion: 0.11
Nodes (19): 10. Security, privacy, and abuse tests, 11. Concurrency, fault injection, and recovery tests, 12. Performance, accessibility, and visual acceptance, 1. Static and build checks, 2. Unit tests, 3. Property and state-machine tests, 4. Frontend component tests, 5. API and provider contract tests (+11 more)

### Community 47 - "Persistent data, privileges and migration lifecycle"
Cohesion: 0.11
Nodes (17): components, $defs, operations, paths, webhooks, Catalog, commercial snapshot and current embedding relationships, Checkpoints, retention and preservation, Conversation and quotation records (+9 more)

### Community 48 - "test_browser_workflow.py"
Cohesion: 0.21
Nodes (3): available_port(), test_complete_native_browser_workflow(), wait_for_server()

### Community 49 - "LumaQuote implementation tracker"
Cohesion: 0.11
Nodes (18): 1. Design and foundations, 2. Manual quotation workflow, 3. Persistent agent and media, 4. Live Google and WhatsApp, 5. Visual finish and safeguards, 6. Frozen evaluation and showcase, Decisions recorded 2026-11-02, Evidence and commits (+10 more)

### Community 50 - "components.json"
Cohesion: 0.12
Nodes (16): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+8 more)

### Community 52 - "Work log"
Cohesion: 0.12
Nodes (17): October 29, 2026 - Agent semantic fallback wiring, October 29, 2026 - Application documentation reconciliation, October 29, 2026 - Chat documentation reconciliation, October 29, 2026 - Documentation reconciliation validation, October 29, 2026 - Documentation workflow rule, October 29, 2026 - Fixed embedding adapter and explicit index command, October 29, 2026 - Local engine availability diagnosis, October 29, 2026 - Photo browser fixture and attempted verification (+9 more)

### Community 53 - "main"
Cohesion: 0.19
Nodes (8): check_encoding(), check_evidence(), check_links(), check_plan(), documentation_files(), evidence_header(), main(), relative()

### Community 54 - "AppShell.tsx"
Cohesion: 0.11
Nodes (24): AppShell(), navigation, useConversation(), useWorkspace(), followStream(), reconnectDelay(), encoder, MockStream (+16 more)

### Community 55 - "json"
Cohesion: 0.05
Nodes (26): inspect_audio(), inspect_image(), inspect_pdf(), main(), `bash` (PreToolUse on Bash, R15), Claude Code hooks, `edit` (PostToolUse on Edit and Write, R6), `stop` (Stop, R14 and R8-R10) (+18 more)

### Community 57 - "check_frontend.cjs"
Cohesion: 0.19
Nodes (12): Identity and evidence records, definitionName(), fs, inspect(), walk(), main(), visit(), path (+4 more)

### Community 58 - "freeze_evaluation.py"
Cohesion: 0.19
Nodes (6): freeze_fingerprints(), freeze_problems(), load_freeze(), check(), main(), write()

### Community 59 - "InputRecord"
Cohesion: 0.15
Nodes (6): InputRecord, InventoryInput, PolicyInput, PriceInput, ProductInput, SupplierTables

### Community 60 - "Frontend ownership, server state and interaction contracts"
Cohesion: 0.18
Nodes (11): SessionProvider(), Authored, generated and vendor-owned source, Frontend ownership, server state and interaction contracts, Live updates over an authenticated event stream, Mutations and canonical reconciliation, Private documents and temporary capabilities, Quotation editing and conflict preservation, Session and cache boundary (+3 more)

### Community 61 - "manual-workflow.cjs"
Cohesion: 0.19
Nodes (12): @axe-core/playwright@^4.13.0, @playwright/test@^1.64.1, @axe-core/playwright, @playwright/test, { chromium, expect }, dispatchFixture(), fs, main() (+4 more)

### Community 62 - "test_embedding_contracts.py"
Cohesion: 0.15
Nodes (6): test_embedding_response_indices_bind_each_vector_to_its_requested_record(), create(), test_invalid_provider_vectors_fail_closed(), test_shared_filters_refuse_ambiguous_or_negated_requirements(), test_valid_vector_has_only_finite_numeric_json(), unit_vector()

### Community 63 - "ConversationThread.tsx"
Cohesion: 0.10
Nodes (29): ConversationCommand, useConversationAction(), ConversationComposer(), ConversationThread(), JobState(), MediaUpload(), InboxSection, SectionSwitch() (+21 more)

### Community 64 - "staff"
Cohesion: 0.17
Nodes (8): staff(), Binary attachment protocol, Command payloads and a review sequence, Errors and limits, Identity and mutation protocol, Regenerating contracts, Staff API reference, Staff identity, idempotency and optimistic mutation protocol

### Community 65 - "bindings"
Cohesion: 0.17
Nodes (12): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/agents/luma_agent/graph.py, app/agents/luma_agent/nodes/extraction.py (+4 more)

### Community 66 - "whatsapp-channel"
Cohesion: 0.17
Nodes (12): app/backend/luma/features/messaging/inbound.py, app/backend/luma/features/messaging/outbound.py, app/backend/luma/features/messaging/webhook.py, app/backend/luma/features/messaging/whatsapp_client.py, supabase/migrations/20261102010000_whatsapp_inbox.sql, whatsapp-channel, bindings, height (+4 more)

### Community 67 - "LumaQuote"
Cohesion: 0.17
Nodes (11): Accessibility & Inclusion, Brand Commitments, Capabilities and Constraints, Evidence on Hand, LumaQuote, Operating Context, Platform, Product Principles (+3 more)

### Community 68 - "start-local-supabase.cjs"
Cohesion: 0.18
Nodes (10): api(), databaseClients, { execFileSync, spawnSync }, fs, http, names, path, privateDir (+2 more)

### Community 69 - "frontend-live-updates"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/workspace/routes.py, app/frontend/src/features/workspace/api.ts, app/frontend/src/features/workspace/useLiveUpdates.ts, app/frontend/src/shared/api/events.ts, frontend-live-updates, bindings, height, renderer_sha256 (+3 more)

### Community 70 - "diagrams"
Cohesion: 0.20
Nodes (9): height, renderer_sha256, source_sha256, svg_sha256, width, diagrams, catalog-retrieval, mermaid_version (+1 more)

### Community 71 - "system-boundaries"
Cohesion: 0.17
Nodes (12): app/agents/luma_agent/observability.py, app/agents/luma_agent/worker.py, app/backend/luma/features/media/sandbox.py, app/backend/luma/google_gateway.py, app/backend/luma/main.py, system-boundaries, bindings, height (+4 more)

### Community 72 - "staff-operation"
Cohesion: 0.18
Nodes (11): app/backend/luma/core/database.py, app/backend/luma/core/http.py, app/backend/luma/core/idempotency.py, app/backend/luma/features/quotations/routes.py, staff-operation, bindings, height, renderer_sha256 (+3 more)

### Community 73 - "google-snapshot"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/google_sync/callbacks.py, app/backend/luma/features/google_sync/snapshots.py, app/backend/luma/features/google_sync/validation.py, gas/Synchronization.gs, google-snapshot, bindings, height, renderer_sha256 (+3 more)

### Community 74 - "drive-export"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/google_sync/exports.py, app/backend/luma/features/quotations/documents.py, gas/Exports.gs, supabase/migrations/20261102000000_drive_exports.sql, drive-export, bindings, height, renderer_sha256 (+3 more)

### Community 75 - "evidence-data"
Cohesion: 0.12
Nodes (17): supabase/migrations/20261029010000_quotation_domain.sql, supabase/migrations/20261029100000_immutable_quotation_content.sql, supabase/migrations/20261029131000_versioned_embeddings.sql, evidence-data, workflow-data, bindings, height, renderer_sha256 (+9 more)

### Community 76 - "package.json"
Cohesion: 0.16
Nodes (15): devDependencies, @google/clasp@3.4.1, mermaid@11.17.2, supabase@2.122.0, typescript@5.9.3, typescript, name, overrides (+7 more)

### Community 78 - "estimated-allowance"
Cohesion: 0.13
Nodes (15): app/agents/luma_agent/budget.py, app/agents/luma_agent/nodes/retrieval.py, app/agents/luma_agent/nodes/workflow.py, app/agents/luma_agent/runtime/media.py, app/backend/luma/features/catalog/criteria.py, app/backend/luma/features/catalog/retrieval.py, app/backend/luma/features/catalog/semantic.py, bindings (+7 more)

### Community 79 - "frontend-draft"
Cohesion: 0.20
Nodes (10): app/frontend/src/features/conversations/api.ts, app/frontend/src/features/quotations/QuotationPanel.tsx, app/frontend/src/features/quotations/useQuotationDraft.ts, frontend-draft, bindings, height, renderer_sha256, source_sha256 (+2 more)

### Community 80 - "verification-scope"
Cohesion: 0.20
Nodes (10): .github/workflows/ci.yml, scripts/verify.cjs, tests/integration/test_browser_workflow.py, verification-scope, bindings, height, renderer_sha256, source_sha256 (+2 more)

### Community 81 - "catalog.test.cjs"
Cohesion: 0.20
Nodes (5): assert, fs, os, path, test

### Community 82 - "StrictModel"
Cohesion: 0.27
Nodes (5): StrictModel, DraftInput, Selection, test_concurrent_edits_allow_only_one_observed_version(), save()

### Community 83 - "conversation-data"
Cohesion: 0.22
Nodes (9): supabase/migrations/20261029110000_voice_intake.sql, supabase/migrations/20261029111000_media_message_binding.sql, bindings, height, renderer_sha256, source_sha256, svg_sha256, width (+1 more)

### Community 84 - "Local Supabase"
Cohesion: 0.22
Nodes (9): Conflicts, unavailable infrastructure and evidence, Credentials and application configuration, Local Supabase, Media and worker diagnosis, Native processes and optional provider work, Schema, Semantic index command under development, Services (+1 more)

### Community 87 - "Voice and product-label media lifecycle"
Cohesion: 0.25
Nodes (7): PhotoReading, Failure response and evidence, Intake and durable acceptance, Photo reading contract, Publication and customer confirmation, Voice and product-label media lifecycle, Voice reading contract

### Community 88 - "LumaQuote"
Cohesion: 0.25
Nodes (8): Documentation, LumaQuote, LumaQuote request-to-reviewed-offer workflow, Run locally, Status and next actions, Structure, Verification, Workflow at a glance

### Community 89 - "Configuration and native process operation"
Cohesion: 0.29
Nodes (7): Configuration and native process operation, Messaging and Google configuration, Paid AI policy, Private generated files and reproducibility, Safe routine operation, Supabase and database identities, Tracing policy

### Community 90 - "ref_node_fs"
Cohesion: 0.15
Nodes (8): fs, path, root, { spawnSync }, fs, path, root, { spawnSync }

### Community 91 - "captureText"
Cohesion: 0.15
Nodes (13): @react-three/drei@^10.7.9, LightingScene(), Luminaire(), LightingFallback(), SceneBoundary, captureText(), looksLikePhone(), maskForCapture() (+5 more)

### Community 92 - "LumaQuote architecture"
Cohesion: 0.33
Nodes (6): Agent participation and recovery limits, Code ownership, Durable business state, LumaQuote architecture, Processes and trust boundaries, Semantic retrieval work in progress

### Community 93 - "Backend contracts and business transactions"
Cohesion: 0.29
Nodes (7): Admission and repeat submissions, Backend contracts and business transactions, Canonical quotation, exact approval and final dispatch checks, Composition and dependency direction, Drafting an immutable offer, Failure boundaries and evidence, Identity, company selection and transactions

### Community 94 - "appsscript.json"
Cohesion: 0.33
Nodes (5): dependencies, exceptionLogging, oauthScopes, runtimeVersion, timeZone

### Community 95 - "WhatsApp channel (Meta Cloud API)"
Cohesion: 0.33
Nodes (6): Configuration (names only), Data, Failure and recovery, Proof and limits, WhatsApp channel (Meta Cloud API), WhatsApp webhook ingress and gated egress

### Community 97 - "Sales and agent workflows"
Cohesion: 0.40
Nodes (5): Agent requests and evidence, Manual quotation, Notes, human replies and takeover, Sales and agent workflows, Voice and product-label photos

### Community 100 - "post"
Cohesion: 0.06
Nodes (24): complete_media(), media_record(), test_mutation_rate_limit_rejects_the_thirty_first_request_with_retry_guidance(), test_populated_tenant_restores_identically_with_checkpoints_and_objects(), pending(), run_next(), test_customer_clarification_resumes_after_restart(), test_descriptive_request_gets_cited_choices_before_selection() (+16 more)

### Community 101 - "Frontend work plan (for Sonnet execution)"
Cohesion: 0.25
Nodes (8): Acceptance for the whole plan, Branch, pull request and merge (decision D39), Execution protocol for Sonnet (read before every task), Frontend work plan (for Sonnet execution), How to start, Open questions for the user (not blocking any task; use the stated default), Run to completion (user instruction, 2026-11-03), Why this plan exists

### Community 102 - "Visual guide to LumaQuote"
Cohesion: 0.50
Nodes (4): Data and runtime, Maintaining a view, Visual guide to LumaQuote, Workflow and architecture

### Community 103 - "Project documentation"
Cohesion: 0.50
Nodes (4): Current verification boundaries, Detailed implementation references, Documentation coverage and update ownership, Project documentation

### Community 105 - "rule-enforcement"
Cohesion: 0.17
Nodes (12): .claude/settings.json, scripts/check_docs.py, scripts/hooks/guard.py, scripts/skills.py, scripts/summarize_agent_run.py, rule-enforcement, bindings, height (+4 more)

### Community 106 - "Tasks"
Cohesion: 0.33
Nodes (6): F0 - Baseline, branch and worktree, F5 - Explicit approval confirmation (G5), F7 - Capture-mode body masking (G7), F8 - Whole-app visual and accessibility review with evidence (G9), F9 - Close-out, Tasks

### Community 108 - "Verified OpenAI contracts"
Cohesion: 0.67
Nodes (3): Embedding adapter under development, Photo label-reading contract, Verified OpenAI contracts

### Community 109 - "Showcase shot list (90-120 seconds)"
Cohesion: 0.67
Nodes (3): Not shown (do not demonstrate or claim), Reproducible evidence behind each claim, Showcase shot list (90-120 seconds)

### Community 115 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.18
Nodes (11): 1. What went wrong so far (evidence from the work log and this session), 2. Principles, 3. The rulebook (replaces most of AGENTS.md + CLAUDE.md prose), 4.1 Make skills discoverable, 4.2 Consolidate 37 -> about 20 skills, 4.3 One routing table, 4. Skill routing, 5. Documentation: one home per fact (+3 more)

### Community 116 - "Working rules, skill routing and their enforcement"
Cohesion: 0.18
Nodes (11): Evaluation scoring pin (R11), Failure and recovery, Knowledge graph (decision D33), npm checks, Overview, Rule-to-enforcement map, `scripts/check_docs.py` details, `scripts/skills.py` details (+3 more)

### Community 144 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, test, typecheck

### Community 145 - "Development tooling, verification and evidence interpretation"
Cohesion: 0.20
Nodes (10): Browser scenario and screenshots, Command ownership, Development tooling, verification and evidence interpretation, Explicit provider canaries, Historical checkpoint and remaining gates, Isolated integration environment, Offline and full gates, Offline, local integration and explicit live evidence boundaries (+2 more)

### Community 147 - "test_live_evaluation.py"
Cohesion: 0.06
Nodes (15): validate_media_provider(), reserve(), usage_totals(), assert_job(), process_conversation(), process_media(), run_media(), Durable state and provider admission (+7 more)

## Knowledge Gaps
- **1 isolated node(s):** `lumaquote`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1430 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **47 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Authenticated live updates with polling fallback` connect `AppShell.tsx` to `conversation`, `Frontend ownership, server state and interaction contracts`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Are the 44 inferred relationships involving `DomainError` (e.g. with `embed_texts()` and `validate_embedding_provider()`) actually correct?**
  _`DomainError` has 44 INFERRED edges - model-reasoned connections that need verification._
- **What connects `lumaquote` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `psycopg` be split into smaller, more focused modules?**
  _Cohesion score 0.039470233412011536 - nodes in this community are weakly interconnected._
- **Why does `DomainError` connect `DomainError` to `psycopg`, `semantic.py`, `conversation`, `errors.py`, `database`, `media_reading.py`, `ask`, `test_live_evaluation.py`, `nodes/retrieval.py`, `io`, `upload_audio`, `test_channel_contracts.py`, `Apps Script transport and validated commercial snapshots`, `observability.py`, `test_embedding_contracts.py`, `staff`, `StrictModel`, `post`, `test_operator_index_settles_or_blocks_uncertain_retries`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Should `semantic.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11396011396011396 - nodes in this community are weakly interconnected._
- **Why does `October 29, 2026 - Offline embedding contract tests and engine recovery result` connect `October 29, 2026 - Offline embedding contract tests and engine recovery result` to `queue_drive_export`, `CatalogSearch`, `conversation`, `evaluation_dataset.py`, `test_drive_exports.py`, `hashlib`, `vitest`, `media_reading.py`, `ask`, `extraction.py`, `Work log`, `AppShell.tsx`, `captureText`, `ConversationThread.tsx`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._