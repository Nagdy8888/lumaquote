# Graph Report - Demo_Project_4  (2026-11-07)

## Corpus Check
- 336 files · ~266,489 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 47 file(s) not represented in the graph (top: .mmd 27, .css 8, .gs 5)

## Summary
- 3233 nodes · 7328 edges · 188 communities (130 shown, 58 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 464 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `853147d2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- create_request
- settings
- semantic.py
- October 29, 2026 - Offline embedding contract tests and engine recovery result
- conversation
- decimal
- frontend/package.json
- test_whatsapp.py
- evaluation_dataset.py
- make_draft
- test_drive_exports.py
- json
- cn
- json
- Voice and product-label media lifecycle
- Button
- App.tsx
- worker.py
- test_telegram.py
- extraction.py
- uuid
- conversations/routes.py
- re
- io
- scripts
- media/routes.py
- workspace/schemas.py
- webhook.py
- skills.py
- google_sync/routes.py
- test_trace_masking.py
- Proposal: working rules, skill routing and documentation (draft for approval)
- workflow.py
- index.cjs
- re
- outbound.py
- call
- steps
- retention.py
- Design System: LumaQuote
- QuotationPanel
- ref_node_path
- compilerOptions
- settings
- job-recovery
- quotation-approval
- Test layers
- Persistent data, privileges and migration lifecycle
- validate
- LumaQuote implementation tracker
- components.json
- Work log
- main
- NewRequest.tsx
- whatsapp_client.py
- conftest.py
- check_frontend.cjs
- freeze_evaluation.py
- package.json
- twilio_webhook.py
- manual-workflow.cjs
- Telegram channel (Bot API, long polling)
- AppShell.tsx
- test_surface_inventory.py
- bindings
- whatsapp-channel
- LumaQuote
- start-local-supabase.cjs
- ReceiptRequest
- catalog-retrieval
- system-boundaries
- diagrams
- google-snapshot
- drive-export
- workflow-data
- bindings
- test_twilio.py
- backend-modules
- frontend-draft
- verification-scope
- catalog.test.cjs
- psycopg
- conversation-data
- Local Supabase
- database
- check_architecture.py
- Morning actions
- LumaQuote
- Configuration and native process operation
- page-review.cjs
- test_twilio_signature.py
- LumaQuote architecture
- observability.py
- appsscript.json
- Apps Script transport and validated commercial snapshots
- WhatsApp channel (Meta Cloud API or Twilio Sandbox)
- Sales and agent workflows
- Google Apps Script integration
- test_api_boundaries.py
- test_controlled_provider_cannot_invent_customer_confirmation
- embedding_inputs
- Visual guide to LumaQuote
- Project documentation
- decide
- rule-enforcement
- test_staff_replies.py
- CLAUDE.md
- Verified OpenAI contracts
- IMPLEMENTATION_PLAN.md
- accept_media
- test_agent_on_development_scenario
- test_browser_workflow.py
- Proposal: working rules, skill routing and documentation (draft for approval)
- Working rules, skill routing and their enforcement
- media_links.py
- test_trace_canary.py
- early_in_minute
- lumaquote
- media.py
- Development tooling, verification and evidence interpretation
- Graph
- Retry
- pin
- User decisions register
- dependency_unavailable
- _assert_no_canaries
- PhotoReading
- FakeSession
- Tasks
- environment
- test_provider_failure_and_worker_logs_do_not_leak_canaries
- Layer 6: Data (PostgreSQL and private Storage)
- test_phone_numbers_are_masked
- test_nested_tool_and_subgraph_runs_are_masked
- generated.ts
- run
- State
- test_job_trace_exports_graph_and_model_runs_masked
- bootstrap.py
- test_production_client_masks_every_exported_field
- test_business_content_is_kept
- Layer 7: External integrations
- LumaQuote by layer
- staff
- Cross-cutting layer: verification and tooling
- test_holdout_is_refused_unless_frozen_unspent_and_confirmed
- test_handshake_requires_the_exact_verify_token_and_full_configuration

## God Nodes (most connected - your core abstractions)
1. `DomainError` - 130 edges
2. `October 29, 2026 - Offline embedding contract tests and engine recovery result` - 105 edges
3. `settings()` - 84 edges
4. `database()` - 76 edges
5. `create_request()` - 73 edges
6. `get_detail()` - 73 edges
7. `post()` - 64 edges
8. `make_draft()` - 45 edges
9. `cn()` - 42 edges
10. `scripts` - 36 edges

## Surprising Connections (you probably didn't know these)
- `Agent fallback and publication recheck` --references--> `ask()`  [INFERRED]
  docs/reference/CATALOG.md → app/agents/luma_agent/nodes/workflow.py
- `Command ownership` --references--> `prepare()`  [INFERRED]
  docs/reference/TOOLING_AND_TESTS.md → app/agents/luma_agent/nodes/workflow.py
- `2. Principles` --references--> `review()`  [INFERRED]
  docs/proposals/2026-11-03-working-rules.md → app/agents/luma_agent/nodes/workflow.py
- `2026-11-03 - Nested trace-redaction check found and fixed an error-field leak (phase 3, local-substitute)` --references--> `masked_client()`  [INFERRED]
  docs/WORK_LOG.md → app/agents/luma_agent/observability.py
- `Working method` --references--> `job_trace()`  [INFERRED]
  docs/DECISIONS.md → app/agents/luma_agent/observability.py

## Import Cycles
- None detected.

## Communities (188 total, 58 thin omitted)

### Community 0 - "create_request"
Cohesion: 0.07
Nodes (17): test_queue_capacity_refuses_work_at_100_with_a_recoverable_503(), test_expired_operation_is_fenced_visible_and_not_retried(), test_expiry_recovery_skips_another_transactions_locked_job(), test_live_label_reading_remains_unconfirmed(), create_request(), test_database_outage_is_a_safe_retryable_503(), test_storage_outage_leaves_nothing_half_written_and_recovers(), photo_bytes() (+9 more)

### Community 1 - "settings"
Cohesion: 0.08
Nodes (17): ProviderError, fetch_media(), account_base(), auth(), call(), create_message(), fetch_media(), make_client() (+9 more)

### Community 2 - "semantic.py"
Cohesion: 0.05
Nodes (29): query_constraints(), SearchCriteria, candidate_question(), search_catalog(), CatalogHit, CatalogSearch, semantic_search(), vector_literal() (+21 more)

### Community 3 - "October 29, 2026 - Offline embedding contract tests and engine recovery result"
Cohesion: 0.02
Nodes (90): 2026-10-29 - Agent fallback boundary tests added, 2026-10-29 - Agent fallback checks passed and evidence consolidated, 2026-10-29 - All Mermaid views rendered locally, 2026-10-29 - Configuration and verification reference coverage, 2026-10-29 — Current workflow documentation and screenshot reviewed, 2026-10-29 — Database gates passed; browser startup assertion failed, 2026-10-29 - Deep agent, media and retrieval references, 2026-10-29 - Deep backend and persistence documentation (+82 more)

### Community 4 - "conversation"
Cohesion: 0.08
Nodes (21): _deliver_local(), recover_expired(), enqueue(), audit(), accept_customer_text(), conversation(), add_message(), intake() (+13 more)

### Community 6 - "frontend/package.json"
Cohesion: 0.04
Nodes (66): dependencies, class-variance-authority@^0.7.1, clsx@^2.1.1, cn@^0.4.0, @fontsource/ibm-plex-sans@^5.3.0, @fontsource-variable/space-grotesk@^5.3.0, lucide-react@^1.63.0, @radix-ui/react-slot@^1.5.0 (+58 more)

### Community 7 - "test_whatsapp.py"
Cohesion: 0.09
Nodes (26): deliver_one(), Inputs and outputs, conversation_for(), deliver_webhook(), envelope(), outbox(), queue_reply(), rows() (+18 more)

### Community 8 - "evaluation_dataset.py"
Cohesion: 0.06
Nodes (22): 2026-11-02 - Holdout freeze guard (phase 6 preparation, offline), loaded(), test_counts_and_family_split_match_the_plan(), test_every_media_turn_has_a_hashed_asset_and_stays_unconfirmed(), test_family_table_matches_the_bootstrap_catalog(), test_fingerprints_are_stable_hex_digests(), test_freeze_blocks_the_holdout_until_pinned_unchanged_and_unspent(), test_media_manifest_never_records_outcomes() (+14 more)

### Community 9 - "make_draft"
Cohesion: 0.07
Nodes (13): search(), test_authoritative_family_is_searchable_when_name_uses_different_words(), test_changed_product_evidence_requires_another_review(), test_description_lookup_retains_original_page_version_and_explicit_specs(), test_exact_sku_precedes_descriptive_similarity(), test_retired_catalog_cannot_be_recommended_or_finalized(), make_draft(), test_complete_manual_quotation_and_local_delivery() (+5 more)

### Community 10 - "test_drive_exports.py"
Cohesion: 0.09
Nodes (21): Changes on 2026-11-03, Extending safely, Features, Layer 3: Business features, Open gaps, Rules every feature follows, Tests and evidence, Who calls what (+13 more)

### Community 11 - "json"
Cohesion: 0.08
Nodes (13): evaluate(), main(), evaluate(), load_catalog(), main(), summarize(), denominators(), fingerprints() (+5 more)

### Community 12 - "cn"
Cohesion: 0.13
Nodes (27): radix-ui@^1.8.1, cn(), Badge(), badgeVariants, Empty(), EmptyContent(), EmptyDescription(), EmptyHeader() (+19 more)

### Community 13 - "json"
Cohesion: 0.03
Nodes (40): inspect_audio(), inspect_image(), inspect_pdf(), main(), `bash` (PreToolUse on Bash, R15), Claude Code hooks, `edit` (PostToolUse on Edit and Write, R6), `stop` (Stop, R14 and R8-R10) (+32 more)

### Community 14 - "Voice and product-label media lifecycle"
Cohesion: 0.10
Nodes (21): MediaPreview(), load(), ApiError, documentUrl(), openDocument(), Changes on 2026-11-03, Extending safely, How data moves (+13 more)

### Community 15 - "Button"
Cohesion: 0.14
Nodes (23): ConversationCommand, useConversationAction(), ConversationComposer(), ProductSelections(), QuoteSummary(), ReviewActions(), EditableLine, Conversation (+15 more)

### Community 16 - "App.tsx"
Cohesion: 0.14
Nodes (23): App(), CatalogPage(), InboxPage(), connections, ConnectionsPage(), LightingScene(), Luminaire(), LightingScene (+15 more)

### Community 17 - "worker.py"
Cohesion: 0.11
Nodes (14): finish(), process_audio(), process_conversation(), claim_job(), finish_job(), process_media(), main(), tick() (+6 more)

### Community 18 - "test_telegram.py"
Cohesion: 0.07
Nodes (21): poll_telegram(), poll_once(), reduce_update(), External effects and secrets, Modules and call flow, Bot, bot(), start() (+13 more)

### Community 19 - "extraction.py"
Cohesion: 0.07
Nodes (23): baseline_extract(), clarification_for(), Extraction, RequestedLine, parse_written_request(), Extraction and consequential-field confirmation, Integration coverage by responsibility, 2026-11-02 - Negative (mutation-style) checks for hostile-content tests (+15 more)

### Community 20 - "uuid"
Cohesion: 0.07
Nodes (16): accept_hint(), EditHint, verify_hint(), verify_mapping(), verify_signature(), verify_envelope(), InputRecord, InventoryInput (+8 more)

### Community 21 - "conversations/routes.py"
Cohesion: 0.10
Nodes (19): StrictModel, change_ownership(), queue_staff_reply(), record_customer_reply(), record_note(), customer_reply(), execute(), detail() (+11 more)

### Community 22 - "re"
Cohesion: 0.10
Nodes (13): degrade(), draw_label(), font(), main(), make_photo(), make_voice(), mix(), noise() (+5 more)

### Community 23 - "io"
Cohesion: 0.13
Nodes (6): bounded_output(), process_file(), test_corrupt_files_are_rejected(), test_image_is_normalized_without_metadata(), test_native_pdf_retains_original_page_text(), test_overlong_audio_is_rejected_before_transcription()

### Community 24 - "scripts"
Cohesion: 0.06
Nodes (36): scripts, build, check:architecture, check:docs, check:frontend, check:rules, check:secrets, db:configure (+28 more)

### Community 25 - "media/routes.py"
Cohesion: 0.11
Nodes (12): rate_limit(), audio_playback(), image_preview(), upload_audio(), upload_image(), Admission, Authenticated mutation protocol, Changes on 2026-11-03 (+4 more)

### Community 26 - "workspace/schemas.py"
Cohesion: 0.09
Nodes (14): ActivityView, CompanyView, ConversationDetail, ConversationView, DeliveryView, JobView, MessageView, ProductView (+6 more)

### Community 27 - "webhook.py"
Cohesion: 0.13
Nodes (8): configured(), extract_events(), handshake(), message_event(), read_limited(), receive(), status_event(), test_inbound_events_are_reduced_to_minimum_validated_fields()

### Community 28 - "skills.py"
Cohesion: 0.12
Nodes (13): active_skills(), check_frontmatter(), check_links(), check_manifests(), check_mirror(), check_routing(), digest(), located() (+5 more)

### Community 29 - "google_sync/routes.py"
Cohesion: 0.14
Nodes (11): claim_export(), record_nonce(), record_receipt(), drive_export_claim(), drive_export_receipt(), google_callback(), signed_body(), supplier_snapshot() (+3 more)

### Community 30 - "test_trace_masking.py"
Cohesion: 0.12
Nodes (5): test_disabled_tracing_exports_nothing(), test_media_bytes_and_inline_data_are_omitted(), test_model_call_exports_tokens_and_estimated_cost(), test_set_usage_is_a_noop_without_a_run(), test_tracing_is_forced_off_outside_a_job_trace()

### Community 31 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.24
Nodes (7): Code layout, Commands, Documentation (decisions D30, D33), LumaQuote working rules, Rules, Skill routing, Unattended work and accounts

### Community 32 - "workflow.py"
Cohesion: 0.08
Nodes (27): validate_embedding_provider(), build_graph(), route(), assert_job(), assert_request_version(), retrieve(), ask(), clarify() (+19 more)

### Community 33 - "index.cjs"
Cohesion: 0.15
Nodes (20): crypto, embeddedBlock(), existingFile(), fingerprint(), fs, hash(), path, readCatalog() (+12 more)

### Community 34 - "re"
Cohesion: 0.10
Nodes (6): adapter(), live_enabled(), ready(), ready(), largest_photo(), ready()

### Community 35 - "outbound.py"
Cohesion: 0.08
Nodes (15): allowed(), allowed_senders(), allowed_telegram_users(), begin(), block(), record(), submit(), queue_drive_export() (+7 more)

### Community 36 - "call"
Cohesion: 0.14
Nodes (8): call(), fetch_media(), get_updates(), make_client(), message_ref(), send_pdf(), send_text(), token()

### Community 37 - "steps"
Cohesion: 0.09
Nodes (21): VITE_SUPABASE_ANON_KEY, VITE_SUPABASE_URL, jobs, local-contracts, runs-on, steps, timeout-minutes, name (+13 more)

### Community 38 - "retention.py"
Cohesion: 0.17
Nodes (9): connect(), expired_media(), idle_conversations(), main(), purge_conversations(), purge_media(), purge_records(), run() (+1 more)

### Community 39 - "Design System: LumaQuote"
Cohesion: 0.10
Nodes (21): Buttons, Cards / Containers, Chips, Colors, Components, Design System: LumaQuote, Do:, Do's and Don'ts (+13 more)

### Community 40 - "QuotationPanel"
Cohesion: 0.17
Nodes (11): QuotationPanel(), draftSuite(), capturesLatestCleanVersion(), preservesConflict(), fixture(), useQuotationDraft(), beginEdit(), updateDiscount() (+3 more)

### Community 41 - "ref_node_path"
Cohesion: 0.09
Nodes (16): fs, path, root, { spawnSync }, fs, path, root, { spawnSync } (+8 more)

### Community 42 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, baseUrl, esModuleInterop, jsx, lib, module, moduleResolution (+10 more)

### Community 43 - "settings"
Cohesion: 0.15
Nodes (13): run_media(), settings(), Settings, delete_files(), get_file(), put_file(), storage_headers(), ready() (+5 more)

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
Cohesion: 0.17
Nodes (12): Catalog, commercial snapshot and current embedding relationships, Checkpoints, retention and preservation, Conversation and quotation records, Conversation, offer, approval, media and work relationships, Exact conversation and attachment binding, Google synchronization records, Media and normalized bytes, Migration sequence and local application (+4 more)

### Community 48 - "validate"
Cohesion: 0.11
Nodes (10): Unit and component coverage, 2026-11-03 - Pre-freeze Recall@5 relabel: 7 to 14 retrieval cases (phase 6, local), catalog_model(), _check_outcome(), _check_retrieval(), _check_structure(), _check_turns(), subtotal() (+2 more)

### Community 49 - "LumaQuote implementation tracker"
Cohesion: 0.11
Nodes (19): 1. Design and foundations, 2. Manual quotation workflow, 3. Persistent agent and media, 4. Live Google and WhatsApp, 5. Visual finish and safeguards, 6. Frozen evaluation and showcase, Decisions recorded 2026-11-02, Evidence and commits (+11 more)

### Community 50 - "components.json"
Cohesion: 0.12
Nodes (16): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+8 more)

### Community 52 - "Work log"
Cohesion: 0.12
Nodes (17): October 29, 2026 - Agent semantic fallback wiring, October 29, 2026 - Application documentation reconciliation, October 29, 2026 - Chat documentation reconciliation, October 29, 2026 - Documentation reconciliation validation, October 29, 2026 - Documentation workflow rule, October 29, 2026 - Fixed embedding adapter and explicit index command, October 29, 2026 - Local engine availability diagnosis, October 29, 2026 - Photo browser fixture and attempted verification (+9 more)

### Community 53 - "main"
Cohesion: 0.21
Nodes (7): check_encoding(), check_evidence(), check_links(), check_plan(), documentation_files(), main(), relative()

### Community 54 - "NewRequest.tsx"
Cohesion: 0.13
Nodes (17): SignIn(), useConversation(), MediaUpload(), NewRequest(), useWorkspace(), request(), Workspace, auth (+9 more)

### Community 55 - "whatsapp_client.py"
Cohesion: 0.12
Nodes (13): call(), download(), endpoint(), fetch_media(), headers(), make_client(), media_host_allowed(), message_id() (+5 more)

### Community 56 - "conftest.py"
Cohesion: 0.14
Nodes (5): apply(), scratch(), shape(), test_all_migrations_apply_cleanly_and_match_the_live_schema(), test_upgrade_keeps_pending_work()

### Community 57 - "check_frontend.cjs"
Cohesion: 0.17
Nodes (13): What is stored, Identity and evidence records, definitionName(), fs, inspect(), walk(), main(), visit() (+5 more)

### Community 58 - "freeze_evaluation.py"
Cohesion: 0.19
Nodes (6): freeze_fingerprints(), freeze_problems(), load_freeze(), check(), main(), write()

### Community 59 - "package.json"
Cohesion: 0.16
Nodes (15): devDependencies, @google/clasp@3.4.1, mermaid@11.17.2, supabase@2.122.0, typescript@5.9.3, typescript, name, overrides (+7 more)

### Community 60 - "twilio_webhook.py"
Cohesion: 0.13
Nodes (11): addressed_to_us(), configured(), expected_signature(), first(), message_event(), receive_message(), receive_status(), status_event() (+3 more)

### Community 61 - "manual-workflow.cjs"
Cohesion: 0.25
Nodes (10): beat(), { chromium, expect }, dispatchFixture(), fs, main(), path, PRIVATE, processMediaFixture() (+2 more)

### Community 62 - "Telegram channel (Bot API, long polling)"
Cohesion: 0.18
Nodes (11): Actors and authority, Configuration (names only), Database writes and transactions, Failures and recovery, Idempotency, Limits and cost, Open gaps, State transitions (+3 more)

### Community 63 - "AppShell.tsx"
Cohesion: 0.16
Nodes (16): AppShell(), navigation, ConversationThread(), SessionProvider(), Alert(), AlertDescription(), AlertTitle(), alertVariants (+8 more)

### Community 64 - "test_surface_inventory.py"
Cohesion: 0.24
Nodes (4): operations(), test_gateway_exposes_only_signed_receivers_and_no_documentation_or_staff_route(), test_staff_api_directly_mounted_paths_are_health_and_documentation_only(), test_staff_api_surface_is_the_reviewed_inventory_and_only_health_is_open()

### Community 65 - "bindings"
Cohesion: 0.10
Nodes (20): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/agents/luma_agent/graph.py, app/agents/luma_agent/nodes/extraction.py (+12 more)

### Community 66 - "whatsapp-channel"
Cohesion: 0.09
Nodes (23): app/agents/luma_agent/observability.py, app/backend/luma/core/config.py, app/backend/luma/features/google_sync/routes.py, app/backend/luma/features/messaging/inbound.py, app/backend/luma/features/messaging/outbound.py, app/backend/luma/features/messaging/webhook.py, app/backend/luma/features/messaging/whatsapp_client.py, supabase/migrations/20261102010000_whatsapp_inbox.sql (+15 more)

### Community 67 - "LumaQuote"
Cohesion: 0.17
Nodes (11): Accessibility & Inclusion, Brand Commitments, Capabilities and Constraints, Evidence on Hand, LumaQuote, Operating Context, Platform, Product Principles (+3 more)

### Community 68 - "start-local-supabase.cjs"
Cohesion: 0.18
Nodes (10): api(), databaseClients, { execFileSync, spawnSync }, fs, http, names, path, privateDir (+2 more)

### Community 69 - "ReceiptRequest"
Cohesion: 0.10
Nodes (8): ClaimRequest, drive_filename(), ExportEnvelope, ReceiptRequest, base_receipt(), test_media_hosts_must_be_meta_owned_https(), test_receipt_models_reject_incomplete_or_unsafe_outcomes(), test_valid_receipts_and_drive_filenames()

### Community 70 - "catalog-retrieval"
Cohesion: 0.10
Nodes (21): app/agents/luma_agent/budget.py, app/agents/luma_agent/nodes/retrieval.py, app/agents/luma_agent/nodes/workflow.py, app/agents/luma_agent/runtime/media.py, app/backend/luma/features/catalog/criteria.py, app/backend/luma/features/catalog/retrieval.py, app/backend/luma/features/catalog/semantic.py, bindings (+13 more)

### Community 71 - "system-boundaries"
Cohesion: 0.33
Nodes (6): system-boundaries, height, renderer_sha256, source_sha256, svg_sha256, width

### Community 72 - "diagrams"
Cohesion: 0.12
Nodes (15): diagrams, staff-operation, worker-tick, mermaid_version, height, renderer_sha256, source_sha256, svg_sha256 (+7 more)

### Community 73 - "google-snapshot"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/google_sync/callbacks.py, app/backend/luma/features/google_sync/snapshots.py, app/backend/luma/features/google_sync/validation.py, gas/Synchronization.gs, google-snapshot, bindings, height, renderer_sha256 (+3 more)

### Community 74 - "drive-export"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/google_sync/exports.py, app/backend/luma/features/quotations/documents.py, gas/Exports.gs, supabase/migrations/20261102000000_drive_exports.sql, drive-export, bindings, height, renderer_sha256 (+3 more)

### Community 75 - "workflow-data"
Cohesion: 0.12
Nodes (17): supabase/migrations/20261029010000_quotation_domain.sql, supabase/migrations/20261029100000_immutable_quotation_content.sql, supabase/migrations/20261029131000_versioned_embeddings.sql, evidence-data, workflow-data, bindings, height, renderer_sha256 (+9 more)

### Community 76 - "bindings"
Cohesion: 0.09
Nodes (24): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/backend/luma/core/admission.py, app/backend/luma/core/database.py (+16 more)

### Community 77 - "test_twilio.py"
Cohesion: 0.08
Nodes (19): count_inbox(), inbound(), post_form(), receipt(), sid(), sign(), start(), test_approved_quotation_is_offered_as_the_exact_pdf_behind_a_signed_link() (+11 more)

### Community 78 - "backend-modules"
Cohesion: 0.11
Nodes (21): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/agents/luma_agent/worker.py, app/backend/luma/features/media/sandbox.py (+13 more)

### Community 79 - "frontend-draft"
Cohesion: 0.09
Nodes (22): app/frontend/src/app/App.tsx, app/frontend/src/features/conversations/api.ts, app/frontend/src/features/quotations/QuotationPanel.tsx, app/frontend/src/features/quotations/useQuotationDraft.ts, app/frontend/src/features/workspace/api.ts, app/frontend/src/main.tsx, app/frontend/src/shared/api/client.ts, app/frontend/vite.config.ts (+14 more)

### Community 80 - "verification-scope"
Cohesion: 0.11
Nodes (18): .github/workflows/ci.yml, package.json, scripts/verify.cjs, tests/integration/test_browser_workflow.py, verification-scope, verify-gate, bindings, height (+10 more)

### Community 81 - "catalog.test.cjs"
Cohesion: 0.20
Nodes (5): assert, fs, os, path, test

### Community 82 - "psycopg"
Cohesion: 0.05
Nodes (35): test_voice_upload_limit_is_6_per_minute(), test_populated_tenant_restores_identically_with_checkpoints_and_objects(), pending(), run_next(), test_customer_clarification_resumes_after_restart(), test_descriptive_request_gets_cited_choices_before_selection(), test_duplicate_work_is_not_a_customer_answer(), test_manual_decision_job_cannot_start_an_agent_run() (+27 more)

### Community 83 - "conversation-data"
Cohesion: 0.22
Nodes (9): supabase/migrations/20261029110000_voice_intake.sql, supabase/migrations/20261029111000_media_message_binding.sql, bindings, height, renderer_sha256, source_sha256, svg_sha256, width (+1 more)

### Community 84 - "Local Supabase"
Cohesion: 0.22
Nodes (9): Conflicts, unavailable infrastructure and evidence, Credentials and application configuration, Local Supabase, Media and worker diagnosis, Native processes and optional provider work, Schema, Semantic index command under development, Services (+1 more)

### Community 85 - "database"
Cohesion: 0.07
Nodes (16): database(), membership(), search(), source_pdf(), authorize_upload(), admit_upload(), persist_upload(), receive_upload() (+8 more)

### Community 87 - "Morning actions"
Cohesion: 0.15
Nodes (13): Decision needed: failed requests are not rate limited, Evidence limits, Google callback preparation, Google Workspace / clasp, LangSmith account limit, Latest verification, Local Docker / WSL availability, Morning actions (+5 more)

### Community 88 - "LumaQuote"
Cohesion: 0.25
Nodes (8): Documentation, LumaQuote, LumaQuote request-to-reviewed-offer workflow, Run locally, Status and next actions, Structure, Verification, Workflow at a glance

### Community 89 - "Configuration and native process operation"
Cohesion: 0.29
Nodes (7): Configuration and native process operation, Messaging and Google configuration, Paid AI policy, Private generated files and reproducibility, Safe routine operation, Supabase and database identities, Tracing policy

### Community 90 - "page-review.cjs"
Cohesion: 0.13
Nodes (16): @axe-core/playwright@^4.13.0, @playwright/test@^1.64.1, @axe-core/playwright, @playwright/test, { chromium }, fs, main(), ROUTES (+8 more)

### Community 91 - "test_twilio_signature.py"
Cohesion: 0.15
Nodes (5): test_media_link_binds_outbox_id_and_expires(), test_media_link_refuses_without_a_token(), test_signature_matches_twilio_python_vector(), test_url_variants_add_or_remove_the_default_port(), token()

### Community 92 - "LumaQuote architecture"
Cohesion: 0.33
Nodes (6): Agent participation and recovery limits, Code ownership, Durable business state, LumaQuote architecture, Processes and trust boundaries, Semantic retrieval work in progress

### Community 93 - "observability.py"
Cohesion: 0.08
Nodes (22): embed_texts(), MediaReading, _read_label(), read_media(), extract(), configured_secrets(), flush(), job_trace() (+14 more)

### Community 94 - "appsscript.json"
Cohesion: 0.33
Nodes (5): dependencies, exceptionLogging, oauthScopes, runtimeVersion, timeZone

### Community 95 - "Apps Script transport and validated commercial snapshots"
Cohesion: 0.20
Nodes (10): Apps Script transport and validated commercial snapshots, Atomic publication and offer freshness, Authority and process boundary, Diagnosis without leaking integration data, Drive export of approved quotations, Envelope authentication and replay, GAS source responsibilities, Signed Apps Script snapshot validation and atomic publication (+2 more)

### Community 96 - "WhatsApp channel (Meta Cloud API or Twilio Sandbox)"
Cohesion: 0.33
Nodes (6): Configuration (names only), Data, Failure and recovery, Proof and limits, WhatsApp channel (Meta Cloud API or Twilio Sandbox), WhatsApp webhook ingress and gated egress

### Community 97 - "Sales and agent workflows"
Cohesion: 0.40
Nodes (5): Agent requests and evidence, Manual quotation, Notes, human replies and takeover, Sales and agent workflows, Voice and product-label photos

### Community 98 - "Google Apps Script integration"
Cohesion: 0.33
Nodes (6): Account setup, Evidence limits, Google Apps Script integration, Local receiver, Source responsibilities, Troubleshooting and verification

### Community 99 - "test_api_boundaries.py"
Cohesion: 0.09
Nodes (9): test_auth_outage_is_a_safe_503_not_an_open_door(), test_cors_allows_only_the_exact_local_origins(), test_declared_oversize_and_malformed_length_are_rejected_before_routing(), test_every_response_is_private_nosniff_and_unframed(), test_gateway_never_exposes_staff_routes_or_documentation(), test_missing_or_invalid_credentials_never_reach_business_code(), test_mutation_rate_limit_rejects_the_thirty_first_request_with_retry_guidance(), test_private_pdf_is_never_cacheable() (+1 more)

### Community 100 - "test_controlled_provider_cannot_invent_customer_confirmation"
Cohesion: 0.50
Nodes (3): test_controlled_provider_cannot_invent_customer_confirmation(), client_fixture(), parse_fixture()

### Community 101 - "embedding_inputs"
Cohesion: 0.11
Nodes (10): index_company(), embedding_inputs(), has_current_embeddings(), publish_embeddings(), Operator indexing, test_agent_semantic_fallback_preserves_action_and_source_boundaries(), test_live_embedding_index_and_query_roundtrip(), publish_fixture() (+2 more)

### Community 102 - "Visual guide to LumaQuote"
Cohesion: 0.40
Nodes (5): Data and runtime, Layer views, Maintaining a view, Visual guide to LumaQuote, Workflow and architecture

### Community 103 - "Project documentation"
Cohesion: 0.50
Nodes (4): Current verification boundaries, Detailed implementation references, Documentation coverage and update ownership, Project documentation

### Community 104 - "decide"
Cohesion: 0.08
Nodes (15): DomainError, unique_records(), validate_tables(), authorize_outbound(), check_quotation(), check_snapshot(), assert_dispatchable(), calculate() (+7 more)

### Community 105 - "rule-enforcement"
Cohesion: 0.17
Nodes (12): .claude/settings.json, scripts/check_docs.py, scripts/hooks/guard.py, scripts/skills.py, scripts/summarize_agent_run.py, rule-enforcement, bindings, height (+4 more)

### Community 106 - "test_staff_replies.py"
Cohesion: 0.21
Nodes (6): test_staff_reply_limit_is_10_per_minute(), queue_reply(), take_over(), test_human_reply_requires_takeover_and_remains_distinct_from_notes(), test_reply_author_revocation_is_checked_at_dispatch(), test_resuming_automation_cancels_unsent_human_reply()

### Community 108 - "Verified OpenAI contracts"
Cohesion: 0.67
Nodes (3): Embedding adapter under development, Photo label-reading contract, Verified OpenAI contracts

### Community 109 - "IMPLEMENTATION_PLAN.md"
Cohesion: 0.19
Nodes (6): Not shown (do not demonstrate or claim), Reproducible evidence behind each claim, Showcase shot list (90-120 seconds), Direction contract, Sales workspace direction, Synthetic development confirmation cases

### Community 110 - "accept_media"
Cohesion: 0.40
Nodes (3): accept_audio(), accept_media(), Intake and durable acceptance

### Community 111 - "test_agent_on_development_scenario"
Cohesion: 0.15
Nodes (4): seed_catalog(), spent(), test_agent_on_development_scenario(), test_workspace_reports_only_complete_tenant_mapped_gas_configuration()

### Community 114 - "test_browser_workflow.py"
Cohesion: 0.09
Nodes (6): run_review(), available_port(), test_complete_native_browser_workflow(), wait_for_server(), test_every_page_passes_axe_and_fits_both_viewports(), test_lighting_scene_review()

### Community 115 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.18
Nodes (11): 1. What went wrong so far (evidence from the work log and this session), 2. Principles, 3. The rulebook (replaces most of AGENTS.md + CLAUDE.md prose), 4.1 Make skills discoverable, 4.2 Consolidate 37 -> about 20 skills, 4.3 One routing table, 4. Skill routing, 5. Documentation: one home per fact (+3 more)

### Community 116 - "Working rules, skill routing and their enforcement"
Cohesion: 0.18
Nodes (11): Evaluation scoring pin (R11), Failure and recovery, Knowledge graph (decision D33), npm checks, Overview, Rule-to-enforcement map, `scripts/check_docs.py` details, `scripts/skills.py` details (+3 more)

### Community 117 - "media_links.py"
Cohesion: 0.13
Nodes (7): key(), load_pdf(), quotation_pdf(), quotation_url(), signature(), valid_signature(), test_signature_requires_the_sha256_prefix_hex_and_the_exact_body()

### Community 118 - "test_trace_canary.py"
Cohesion: 0.14
Nodes (6): test_live_structured_extraction_prepares_only_review(), running_job(), test_older_preparation_preserves_staff_revision(), test_stale_extraction_cannot_ask_or_replace_draft(), read_trace(), test_live_job_trace_is_detailed_and_masked()

### Community 119 - "early_in_minute"
Cohesion: 0.12
Nodes (8): early_in_minute(), first_denial(), test_approval_limit_is_10_per_minute(), test_catalog_search_limit_is_30_per_minute(), test_customer_messages_are_limited_per_conversation(), test_failed_requests_also_consume_admission(), test_read_limit_is_120_per_minute(), test_window_keeps_denied_attempts_and_isolates_keys()

### Community 144 - "media.py"
Cohesion: 0.12
Nodes (8): validate_media_provider(), reserve(), usage_totals(), Estimated allowance lifecycle, Expired-job fencing and conservative uncertainty recovery, test_duplicate_paid_operation_never_reserves_again(), test_retrieval_requires_settled_room_and_cannot_repeat(), test_unresolved_prior_day_call_still_consumes_daily_allowance()

### Community 145 - "Development tooling, verification and evidence interpretation"
Cohesion: 0.25
Nodes (8): Browser scenario and screenshots, Command ownership, Development tooling, verification and evidence interpretation, Explicit provider canaries, Historical checkpoint and remaining gates, Isolated integration environment, Offline and full gates, Offline, local integration and explicit live evidence boundaries

### Community 148 - "pin"
Cohesion: 0.21
Nodes (5): pin(), run_summarizer(), test_changed_or_missing_pin_is_refused_without_post_hoc(), test_matching_pin_is_scored_normally(), test_post_hoc_flag_labels_the_report()

### Community 149 - "User decisions register"
Cohesion: 0.40
Nodes (5): AI, evaluation and tracing, Integrations, Product and scope, User decisions register, Working method

### Community 150 - "dependency_unavailable"
Cohesion: 0.15
Nodes (12): dependency_unavailable(), domain_error(), response_boundaries(), Layer 2: Transport (staff API and signed gateway), Open gaps, Request pipeline, Status codes a caller should expect, Tests and evidence (+4 more)

### Community 151 - "_assert_no_canaries"
Cohesion: 0.25
Nodes (4): _assert_no_canaries(), _job(), test_exception_text_and_error_field_are_masked(), test_metadata_tags_and_job_payload_are_masked()

### Community 154 - "Tasks"
Cohesion: 0.12
Nodes (16): Acceptance for the whole plan, Branch, pull request and merge (decision D39), Execution protocol for Sonnet (read before every task), F0 - Baseline, branch and worktree, F1 - Truthful copy and a not-found route (G2, G8), F5 - Explicit approval confirmation (G5), F6 - Portrait inbox with a section switcher (G6), F7 - Capture-mode body masking (G7) (+8 more)

### Community 157 - "Layer 6: Data (PostgreSQL and private Storage)"
Cohesion: 0.29
Nodes (7): Changes on 2026-11-03, Extending safely, Layer 6: Data (PostgreSQL and private Storage), Migrations, Open gaps, Retention and recovery, Who may reach what

### Community 159 - "test_nested_tool_and_subgraph_runs_are_masked"
Cohesion: 0.67
Nodes (3): test_nested_tool_and_subgraph_runs_are_masked(), inner(), lookup_tool()

### Community 160 - "generated.ts"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 161 - "run"
Cohesion: 0.24
Nodes (4): object_paths(), run(), snapshot(), source_params()

### Community 164 - "bootstrap.py"
Cohesion: 0.10
Nodes (13): digest(), operation(), draft(), latest_quote(), DraftInput, Selection, detail(), workspace() (+5 more)

### Community 167 - "Layer 7: External integrations"
Cohesion: 0.33
Nodes (6): Changes on 2026-11-03, Extending safely, Gates and proof, Layer 7: External integrations, Open gaps, Shared rules

### Community 168 - "LumaQuote by layer"
Cohesion: 0.33
Nodes (6): Keeping these guides current, Layer map, LumaQuote by layer, One request through every layer, Other views, The layers

### Community 170 - "staff"
Cohesion: 0.10
Nodes (16): staff(), Command payloads and a review sequence, Errors and limits, Identity and mutation protocol, Regenerating contracts, Staff API reference, Staff identity, idempotency and optimistic mutation protocol, Admission and repeat submissions (+8 more)

### Community 171 - "Cross-cutting layer: verification and tooling"
Cohesion: 0.40
Nodes (5): Changes on 2026-11-03, Cross-cutting layer: verification and tooling, Open gaps, Test families by layer, The verify gate

## Knowledge Gaps
- **1 isolated node(s):** `lumaquote`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1678 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **58 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DomainError` connect `decide` to `create_request`, `semantic.py`, `conversation`, `decimal`, `test_whatsapp.py`, `Voice and product-label media lifecycle`, `media.py`, `worker.py`, `uuid`, `conversations/routes.py`, `dependency_unavailable`, `io`, `media/routes.py`, `webhook.py`, `google_sync/routes.py`, `workflow.py`, `bootstrap.py`, `staff`, `settings`, `twilio_webhook.py`, `database`, `test_twilio_signature.py`, `observability.py`, `embedding_inputs`, `accept_media`, `media_links.py`, `test_trace_canary.py`, `early_in_minute`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `DomainError` (e.g. with `embed_texts()` and `validate_embedding_provider()`) actually correct?**
  _`DomainError` has 49 INFERRED edges - model-reasoned connections that need verification._
- **What connects `lumaquote` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `create_request` be split into smaller, more focused modules?**
  _Cohesion score 0.0726950354609929 - nodes in this community are weakly interconnected._
- **Why does `What is stored` connect `check_frontend.cjs` to `conversation`, `Layer 6: Data (PostgreSQL and private Storage)`, `test_whatsapp.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `settings()` (e.g. with `Where it lives` and `Loading and restart semantics`) actually correct?**
  _`settings()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `settings` be split into smaller, more focused modules?**
  _Cohesion score 0.07507507507507508 - nodes in this community are weakly interconnected._