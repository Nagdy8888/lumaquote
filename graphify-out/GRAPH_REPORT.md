# Graph Report - Demo_Project_4  (2026-11-07)

## Corpus Check
- 362 files · ~290,646 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 48 file(s) not represented in the graph (top: .mmd 28, .css 8, .gs 5)

## Summary
- 3437 nodes · 7871 edges · 191 communities (132 shown, 59 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 540 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `336155d4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- psycopg
- settings
- semantic.py
- October 29, 2026 - Offline embedding contract tests and engine recovery result
- conversation
- decimal
- frontend/package.json
- test_whatsapp.py
- evaluation_dataset.py
- test_catalog_retrieval.py
- test_drive_exports.py
- json
- cn
- scan_secrets.py
- DocumentButton
- ConversationThread.tsx
- App.tsx
- worker.py
- clarification_for
- extraction.py
- DomainError
- database
- re
- io
- scripts
- subprocess
- workspace/schemas.py
- LightingScene.tsx
- skills.py
- argparse
- test_trace_masking.py
- Proposal: working rules, skill routing and documentation (draft for approval)
- workflow.py
- index.cjs
- provider.py
- run
- call
- steps
- retention.py
- Design System: LumaQuote
- useQuotationDraft
- ref_node_path
- compilerOptions
- settings
- estimated-allowance
- quotation-approval
- Test layers
- Persistent data, privileges and migration lifecycle
- test_brain.py
- LumaQuote implementation tracker
- components.json
- Work log
- main
- AppShell.tsx
- whatsapp_client.py
- apply
- check_frontend.cjs
- freeze_evaluation.py
- package.json
- webhook.py
- manual-workflow.cjs
- Telegram channel (Bot API, long polling)
- ConversationThread
- job-recovery
- bindings
- whatsapp-channel
- LumaQuote
- start-local-supabase.cjs
- ReceiptRequest
- catalog-retrieval
- workspace/routes.py
- diagrams
- google-snapshot
- drive-export
- workflow-data
- bindings
- test_twilio.py
- backend-modules
- frontend-draft
- verification-scope
- ui-review.cjs
- create_request
- conversation-data
- Local Supabase
- core/errors.py
- processor.py
- Morning actions
- LumaQuote
- Configuration and native process operation
- page-review.cjs
- test_twilio_signature.py
- LumaQuote architecture
- observability.py
- appsscript.json
- Apps Script transport and validated commercial snapshots
- frontend-live-updates
- Sales and agent workflows
- Google Apps Script integration
- test_api_boundaries.py
- Layer 3: Business features
- embedding_inputs
- Visual guide to LumaQuote
- Project documentation
- test_quotation_rules.py
- rule-enforcement
- Layer 1: Presentation (React staff workspace)
- CLAUDE.md
- Verified OpenAI contracts
- IMPLEMENTATION_PLAN.md
- ExportEnvelope
- test_live_job_trace_is_detailed_and_masked
- test_browser_workflow.py
- Proposal: working rules, skill routing and documentation (draft for approval)
- Working rules, skill routing and their enforcement
- media_links.py
- test_embedding_response_indices_bind_each_vector_to_its_requested_record
- test_admission_limits.py
- lumaquote
- queue_drive_export
- Development tooling, verification and evidence interpretation
- catalog.test.cjs
- test_surface_inventory.py
- pin
- Showcase shot list (90-120 seconds)
- dependency_unavailable
- _assert_no_canaries
- Voice and product-label media lifecycle
- FakeSession
- Frontend work plan (for Sonnet execution)
- environment
- check_architecture.py
- Layer 6: Data (PostgreSQL and private Storage)
- test_phone_numbers_are_masked
- test_workspace_reports_only_complete_tenant_mapped_gas_configuration
- get_detail
- json
- State
- test_job_trace_exports_graph_and_model_runs_masked
- drafting.py
- Layer 4: Agent worker
- pull_request_template.md
- Layer 7: External integrations
- LumaQuote by layer
- test_every_route_passes_axe_fits_both_viewports_and_masks_capture
- brain
- Cross-cutting layer: verification and tooling
- health
- test_unresolved_prior_day_call_still_consumes_daily_allowance
- scratch
- test_holdout_is_refused_unless_frozen_unspent_and_confirmed

## God Nodes (most connected - your core abstractions)
1. `DomainError` - 130 edges
2. `October 29, 2026 - Offline embedding contract tests and engine recovery result` - 121 edges
3. `settings()` - 84 edges
4. `get_detail()` - 80 edges
5. `database()` - 76 edges
6. `create_request()` - 75 edges
7. `post()` - 72 edges
8. `make_draft()` - 47 edges
9. `cn()` - 42 edges
10. `deliver_one()` - 36 edges

## Surprising Connections (you probably didn't know these)
- `Agent fallback and publication recheck` --references--> `ask()`  [INFERRED]
  docs/reference/CATALOG.md → app/agents/luma_agent/nodes/workflow.py
- `Command ownership` --references--> `prepare()`  [INFERRED]
  docs/reference/TOOLING_AND_TESTS.md → app/agents/luma_agent/nodes/workflow.py
- `2. Principles` --references--> `review()`  [INFERRED]
  docs/proposals/2026-11-03-working-rules.md → app/agents/luma_agent/nodes/workflow.py
- `Two-step approval confirmation` --references--> `review()`  [INFERRED]
  docs/reference/FRONTEND.md → app/agents/luma_agent/nodes/workflow.py
- `2026-11-01 - Unit policy gate passed; persisted-workflow regressions added` --references--> `review()`  [INFERRED]
  docs/WORK_LOG.md → app/agents/luma_agent/nodes/workflow.py

## Import Cycles
- None detected.

## Communities (191 total, 59 thin omitted)

### Community 0 - "psycopg"
Cohesion: 0.05
Nodes (17): test_duplicate_paid_operation_never_reserves_again(), test_retrieval_requires_settled_room_and_cannot_repeat(), test_authoritative_family_is_searchable_when_name_uses_different_words(), pending(), run_next(), test_customer_clarification_resumes_after_restart(), seed_catalog(), spent() (+9 more)

### Community 1 - "settings"
Cohesion: 0.08
Nodes (17): ProviderError, largest_photo(), poll_once(), reduce_update(), account_base(), auth(), call(), create_message() (+9 more)

### Community 2 - "semantic.py"
Cohesion: 0.07
Nodes (15): reserve(), usage_totals(), query_constraints(), SearchCriteria, candidate_question(), search_catalog(), search(), source_pdf() (+7 more)

### Community 3 - "October 29, 2026 - Offline embedding contract tests and engine recovery result"
Cohesion: 0.02
Nodes (105): 2026-10-29 - Agent fallback boundary tests added, 2026-10-29 - Agent fallback checks passed and evidence consolidated, 2026-10-29 - All Mermaid views rendered locally, 2026-10-29 - Configuration and verification reference coverage, 2026-10-29 — Current workflow documentation and screenshot reviewed, 2026-10-29 — Database gates passed; browser startup assertion failed, 2026-10-29 - Deep agent, media and retrieval references, 2026-10-29 - Deep backend and persistence documentation (+97 more)

### Community 4 - "conversation"
Cohesion: 0.06
Nodes (31): _deliver_local(), recover_expired(), enqueue(), audit(), accept_customer_text(), change_ownership(), record_customer_reply(), conversation() (+23 more)

### Community 6 - "frontend/package.json"
Cohesion: 0.04
Nodes (63): dependencies, class-variance-authority@^0.7.1, clsx@^2.1.1, cn@^0.4.0, @fontsource/ibm-plex-sans@^5.3.0, @fontsource-variable/space-grotesk@^5.3.0, lucide-react@^1.63.0, radix-ui@^1.8.1 (+55 more)

### Community 7 - "test_whatsapp.py"
Cohesion: 0.07
Nodes (31): telegram_conversation(), test_allowlisted_user_opens_a_telegram_conversation_and_others_are_ignored(), test_hostile_file_metadata_is_refused_without_downloading(), test_only_private_human_chats_reduce_to_events(), test_start_command_queues_one_greeting_and_no_agent_work(), test_voice_note_is_downloaded_within_limits_and_enters_the_media_pipeline(), update(), test_voice_note_uses_auth_on_twilio_only_and_enters_the_media_pipeline() (+23 more)

### Community 8 - "evaluation_dataset.py"
Cohesion: 0.04
Nodes (32): Unit and component coverage, 2026-11-02 - Holdout freeze guard (phase 6 preparation, offline), 2026-11-03 - Pre-freeze Recall@5 relabel: 7 to 14 retrieval cases (phase 6, local), catalog_model(), _check_outcome(), _check_retrieval(), _check_structure(), _check_turns() (+24 more)

### Community 9 - "test_catalog_retrieval.py"
Cohesion: 0.20
Nodes (5): search(), test_changed_product_evidence_requires_another_review(), test_description_lookup_retains_original_page_version_and_explicit_specs(), test_exact_sku_precedes_descriptive_similarity(), test_retired_catalog_cannot_be_recommended_or_finalized()

### Community 10 - "test_drive_exports.py"
Cohesion: 0.10
Nodes (15): Features, approve(), approved_quote(), exports(), poller(), Poller, test_changed_pdf_blocks_the_export_instead_of_shipping_different_bytes(), test_concurrent_pollers_cannot_claim_the_same_export() (+7 more)

### Community 11 - "json"
Cohesion: 0.11
Nodes (9): decide(), evaluate(), load_catalog(), main(), run_scenario(), denominators(), fingerprints(), load() (+1 more)

### Community 12 - "cn"
Cohesion: 0.12
Nodes (32): PendantField, SignIn(), NewRequest(), cn(), Badge(), badgeVariants, Empty(), EmptyContent() (+24 more)

### Community 13 - "scan_secrets.py"
Cohesion: 0.14
Nodes (9): load_secrets(), main(), run(), scan_files(), tracked_files(), make_repo(), test_clean_repo_reports_no_leaks(), test_only_secret_looking_long_nonpublic_values_are_loaded() (+1 more)

### Community 14 - "DocumentButton"
Cohesion: 0.22
Nodes (14): AudioWaveform(), decodeAudioData(), MediaPreview(), load(), computePeaks(), formatClock(), normalizePeaks(), documentUrl() (+6 more)

### Community 15 - "ConversationThread.tsx"
Cohesion: 0.11
Nodes (22): ConversationCommand, useConversationAction(), ConversationComposer(), InboxSection, SectionSwitch(), components, $defs, operations (+14 more)

### Community 16 - "App.tsx"
Cohesion: 0.10
Nodes (26): App(), CatalogPage(), connections, ConnectionsPage(), NotFoundPage(), QuotationPanel(), QuotationsPage(), ProductSelections() (+18 more)

### Community 17 - "worker.py"
Cohesion: 0.08
Nodes (16): validate_media_provider(), finish(), process_audio(), process_conversation(), claim_job(), finish_job(), process_media(), main() (+8 more)

### Community 18 - "clarification_for"
Cohesion: 0.13
Nodes (12): clarification_for(), Integration coverage by responsibility, 2026-11-02 - Negative (mutation-style) checks for hostile-content tests, extracted(), test_duplicate_sku_requires_clarification(), test_empty_placeholder_lines_do_not_suppress_candidate_discovery(), test_explicit_matching_text_confirms_media_fields(), test_media_alone_cannot_confirm_itself() (+4 more)

### Community 19 - "extraction.py"
Cohesion: 0.07
Nodes (23): catalog_context(), is_yes(), known_skus(), model_input(), restatement(), safe_reply(), transcript(), unknown_reply() (+15 more)

### Community 20 - "DomainError"
Cohesion: 0.05
Nodes (30): DomainError, domain_error(), accept_hint(), EditHint, verify_hint(), verify_mapping(), verify_signature(), claim_export() (+22 more)

### Community 21 - "database"
Cohesion: 0.08
Nodes (29): rate_limit(), database(), operation(), membership(), queue_staff_reply(), record_note(), customer_reply(), detail() (+21 more)

### Community 22 - "re"
Cohesion: 0.10
Nodes (13): degrade(), draw_label(), font(), main(), make_photo(), make_voice(), mix(), noise() (+5 more)

### Community 23 - "io"
Cohesion: 0.13
Nodes (7): bounded_output(), process_file(), Fixed sandbox boundary, test_corrupt_files_are_rejected(), test_image_is_normalized_without_metadata(), test_native_pdf_retains_original_page_text(), test_overlong_audio_is_rejected_before_transcription()

### Community 24 - "scripts"
Cohesion: 0.06
Nodes (36): scripts, build, check:architecture, check:docs, check:frontend, check:rules, check:secrets, db:configure (+28 more)

### Community 25 - "subprocess"
Cohesion: 0.06
Nodes (21): `bash` (PreToolUse on Bash, R15), Claude Code hooks, `edit` (PostToolUse on Edit and Write, R6), `stop` (Stop, R14 and R8-R10), bash(), block(), changed_paths(), edit() (+13 more)

### Community 26 - "workspace/schemas.py"
Cohesion: 0.09
Nodes (14): ActivityView, CompanyView, ConversationDetail, ConversationView, DeliveryView, JobView, MessageView, ProductView (+6 more)

### Community 27 - "LightingScene.tsx"
Cohesion: 0.13
Nodes (24): beamFade(), beamGeometry(), CameraDrift(), FlutedWall(), HeadParts, HEADS, LightingScene(), TrackHeads() (+16 more)

### Community 28 - "skills.py"
Cohesion: 0.12
Nodes (13): active_skills(), check_frontmatter(), check_links(), check_manifests(), check_mirror(), check_routing(), digest(), located() (+5 more)

### Community 29 - "argparse"
Cohesion: 0.13
Nodes (7): evaluate(), main(), summarize(), main(), divergence(), main(), summarize()

### Community 30 - "test_trace_masking.py"
Cohesion: 0.10
Nodes (7): test_business_content_is_kept(), test_disabled_tracing_exports_nothing(), test_media_bytes_and_inline_data_are_omitted(), test_model_call_exports_tokens_and_estimated_cost(), test_production_client_masks_every_exported_field(), test_set_usage_is_a_noop_without_a_run(), test_tracing_is_forced_off_outside_a_job_trace()

### Community 31 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.15
Nodes (12): Code layout, Commands, Documentation (decisions D30, D33), LumaQuote working rules, Rules, Skill routing, Unattended work and accounts, AI, evaluation and tracing (+4 more)

### Community 32 - "workflow.py"
Cohesion: 0.09
Nodes (26): build_graph(), route(), assert_job(), assert_request_version(), retrieve(), ask(), clarify(), prepare() (+18 more)

### Community 33 - "index.cjs"
Cohesion: 0.15
Nodes (20): crypto, embeddedBlock(), existingFile(), fingerprint(), fs, hash(), path, readCatalog() (+12 more)

### Community 34 - "provider.py"
Cohesion: 0.07
Nodes (25): allowed(), allowed_senders(), allowed_telegram_users(), begin(), block(), record(), submit(), adapter() (+17 more)

### Community 35 - "run"
Cohesion: 0.15
Nodes (11): reply_texts(), run(), start(), test_free_wording_is_restated_then_yes_prepares_review(), test_model_reads_conversation_and_catalog_without_prices(), test_unknown_sku_is_not_restated_and_yes_then_asks_the_model(), test_unsafe_model_reply_is_replaced_by_the_fixed_question(), test_written_order_matching_the_model_prepares_directly() (+3 more)

### Community 36 - "call"
Cohesion: 0.14
Nodes (9): call(), fetch_media(), get_updates(), make_client(), message_ref(), ready(), send_pdf(), send_text() (+1 more)

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
Cohesion: 0.11
Nodes (22): draftSuite(), capturesLatestCleanVersion(), preservesConflict(), fixture(), useQuotationDraft(), beginEdit(), updateDiscount(), updateLines() (+14 more)

### Community 41 - "ref_node_path"
Cohesion: 0.09
Nodes (16): fs, path, root, { spawnSync }, fs, path, root, { spawnSync } (+8 more)

### Community 42 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, baseUrl, esModuleInterop, jsx, lib, module, moduleResolution (+10 more)

### Community 43 - "settings"
Cohesion: 0.09
Nodes (15): run_media(), settings(), Settings, staff(), delete_files(), get_file(), put_file(), storage_headers() (+7 more)

### Community 44 - "estimated-allowance"
Cohesion: 0.10
Nodes (20): app/agents/luma_agent/budget.py, app/agents/luma_agent/nodes/retrieval.py, app/agents/luma_agent/runtime/media.py, app/agents/luma_agent/runtime/recovery.py, app/backend/luma/features/media/intake.py, app/backend/luma/features/media/persistence.py, estimated-allowance, media-lifecycle (+12 more)

### Community 45 - "quotation-approval"
Cohesion: 0.11
Nodes (19): app/agents/luma_agent/runtime/delivery.py, app/backend/luma/features/conversations/participation.py, app/backend/luma/features/quotations/approval.py, app/backend/luma/features/quotations/drafting.py, app/backend/luma/features/quotations/freshness.py, quotation-approval, sales-workflow, bindings (+11 more)

### Community 46 - "Test layers"
Cohesion: 0.11
Nodes (19): 10. Security, privacy, and abuse tests, 11. Concurrency, fault injection, and recovery tests, 12. Performance, accessibility, and visual acceptance, 1. Static and build checks, 2. Unit tests, 3. Property and state-machine tests, 4. Frontend component tests, 5. API and provider contract tests (+11 more)

### Community 47 - "Persistent data, privileges and migration lifecycle"
Cohesion: 0.18
Nodes (11): Catalog, commercial snapshot and current embedding relationships, Checkpoints, retention and preservation, Conversation and quotation records, Conversation, offer, approval, media and work relationships, Exact conversation and attachment binding, Google synchronization records, Migration sequence and local application, Persistent data, privileges and migration lifecycle (+3 more)

### Community 48 - "test_brain.py"
Cohesion: 0.13
Nodes (8): make(), test_anything_more_than_agreement_is_not_yes(), test_plain_agreement_is_yes(), test_plain_reply_passes_trimmed(), test_restatement_is_built_from_pairs_only(), test_unsafe_or_empty_replies_are_dropped(), test_unusable_model_orders_are_rejected(), test_valid_lines_normalize_case()

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
Cohesion: 0.20
Nodes (8): check_encoding(), check_evidence(), check_links(), check_plan(), documentation_files(), evidence_header(), main(), relative()

### Community 54 - "AppShell.tsx"
Cohesion: 0.09
Nodes (28): AppShell(), navigation, useConversation(), MediaUpload(), useWorkspace(), followStream(), reconnectDelay(), encoder (+20 more)

### Community 55 - "whatsapp_client.py"
Cohesion: 0.10
Nodes (17): call(), download(), endpoint(), fetch_media(), GraphError, headers(), make_client(), media_host_allowed() (+9 more)

### Community 56 - "apply"
Cohesion: 0.25
Nodes (4): apply(), shape(), test_all_migrations_apply_cleanly_and_match_the_live_schema(), test_upgrade_keeps_pending_work()

### Community 57 - "check_frontend.cjs"
Cohesion: 0.17
Nodes (13): What is stored, Identity and evidence records, definitionName(), fs, inspect(), walk(), main(), visit() (+5 more)

### Community 58 - "freeze_evaluation.py"
Cohesion: 0.19
Nodes (6): freeze_fingerprints(), freeze_problems(), load_freeze(), check(), main(), write()

### Community 59 - "package.json"
Cohesion: 0.16
Nodes (15): devDependencies, @google/clasp@3.4.1, mermaid@11.17.2, supabase@2.122.0, typescript@5.9.3, typescript, name, overrides (+7 more)

### Community 60 - "webhook.py"
Cohesion: 0.06
Nodes (21): addressed_to_us(), configured(), expected_signature(), first(), message_event(), receive_message(), receive_status(), status_event() (+13 more)

### Community 61 - "manual-workflow.cjs"
Cohesion: 0.25
Nodes (10): beat(), { chromium, expect }, dispatchFixture(), fs, main(), path, PRIVATE, processMediaFixture() (+2 more)

### Community 62 - "Telegram channel (Bot API, long polling)"
Cohesion: 0.10
Nodes (17): Binary attachment protocol, Command payloads and a review sequence, Errors and limits, Identity and mutation protocol, Regenerating contracts, Staff API reference, Staff identity, idempotency and optimistic mutation protocol, Configuration (names only) (+9 more)

### Community 63 - "ConversationThread"
Cohesion: 0.12
Nodes (26): ConversationThread(), InboxPage(), JobState(), Job, customerName(), captureText(), looksLikePhone(), maskForCapture() (+18 more)

### Community 64 - "job-recovery"
Cohesion: 0.11
Nodes (19): app/agents/luma_agent/lease.py, app/agents/luma_agent/runtime/jobs.py, app/backend/luma/features/conversations/routes.py, app/backend/luma/features/conversations/service.py, app/frontend/src/shared/api/client.ts, job-recovery, request-trace, bindings (+11 more)

### Community 65 - "bindings"
Cohesion: 0.10
Nodes (21): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/agents/luma_agent/graph.py, app/agents/luma_agent/nodes/extraction.py (+13 more)

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
Cohesion: 0.12
Nodes (7): ReceiptRequest, base_receipt(), test_allowlist_parses_plus_whitespace_and_empty(), test_graph_error_codes_are_short_and_opaque(), test_media_hosts_must_be_meta_owned_https(), test_receipt_models_reject_incomplete_or_unsafe_outcomes(), test_valid_receipts_and_drive_filenames()

### Community 70 - "catalog-retrieval"
Cohesion: 0.18
Nodes (11): app/agents/luma_agent/nodes/workflow.py, app/backend/luma/features/catalog/criteria.py, app/backend/luma/features/catalog/retrieval.py, app/backend/luma/features/catalog/semantic.py, bindings, height, renderer_sha256, source_sha256 (+3 more)

### Community 71 - "workspace/routes.py"
Cohesion: 0.16
Nodes (4): workspace(), events(), stream(), workspace()

### Community 72 - "diagrams"
Cohesion: 0.12
Nodes (15): diagrams, system-boundaries, worker-tick, mermaid_version, height, renderer_sha256, source_sha256, svg_sha256 (+7 more)

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
Cohesion: 0.11
Nodes (20): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/backend/luma/core/admission.py, app/backend/luma/core/errors.py (+12 more)

### Community 77 - "test_twilio.py"
Cohesion: 0.05
Nodes (31): deliver_one(), Bot, bot(), start(), test_approved_quotation_is_uploaded_as_the_exact_canonical_pdf(), test_gates_block_without_calling_telegram(), test_text_reply_is_sent_once_without_a_service_window(), test_uncertain_and_failed_sends_are_never_retried() (+23 more)

### Community 78 - "backend-modules"
Cohesion: 0.11
Nodes (21): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/agents/luma_agent/worker.py, app/backend/luma/features/media/sandbox.py (+13 more)

### Community 79 - "frontend-draft"
Cohesion: 0.10
Nodes (20): app/frontend/src/app/App.tsx, app/frontend/src/features/conversations/api.ts, app/frontend/src/features/quotations/QuotationPanel.tsx, app/frontend/src/features/quotations/useQuotationDraft.ts, app/frontend/src/main.tsx, app/frontend/vite.config.ts, frontend-draft, frontend-layer (+12 more)

### Community 80 - "verification-scope"
Cohesion: 0.11
Nodes (19): .github/workflows/ci.yml, package.json, scripts/verify.cjs, tests/integration/test_browser_workflow.py, tests/integration/test_ui_review.py, verification-scope, verify-gate, bindings (+11 more)

### Community 81 - "ui-review.cjs"
Cohesion: 0.26
Nodes (12): { chromium }, fs, keyboardPass(), livePass(), main(), measure(), PRIVATE, reviewView() (+4 more)

### Community 82 - "create_request"
Cohesion: 0.06
Nodes (21): test_private_pdf_is_never_cacheable(), test_populated_tenant_restores_identically_with_checkpoints_and_objects(), test_manual_decision_job_cannot_start_an_agent_run(), test_staff_decision_resumes_review_after_restart(), test_voice_waits_for_processing_and_exact_written_confirmation(), test_expiry_recovery_skips_another_transactions_locked_job(), test_real_synthetic_voice_is_readable_but_unconfirmed(), create_request() (+13 more)

### Community 83 - "conversation-data"
Cohesion: 0.22
Nodes (9): supabase/migrations/20261029110000_voice_intake.sql, supabase/migrations/20261029111000_media_message_binding.sql, bindings, height, renderer_sha256, source_sha256, svg_sha256, width (+1 more)

### Community 84 - "Local Supabase"
Cohesion: 0.22
Nodes (9): Conflicts, unavailable infrastructure and evidence, Credentials and application configuration, Local Supabase, Media and worker diagnosis, Native processes and optional provider work, Schema, Semantic index command under development, Services (+1 more)

### Community 85 - "core/errors.py"
Cohesion: 0.10
Nodes (10): accept_audio(), accept_media(), authorize_upload(), admit_upload(), audio_playback(), image_preview(), persist_upload(), receive_upload() (+2 more)

### Community 86 - "processor.py"
Cohesion: 0.22
Nodes (4): inspect_audio(), inspect_image(), inspect_pdf(), main()

### Community 87 - "Morning actions"
Cohesion: 0.14
Nodes (14): Decision needed: failed requests are not rate limited, Evidence limits, Google callback preparation, Google Workspace / clasp, LangSmith account limit, Latest verification, Local Docker / WSL availability, Morning actions (+6 more)

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
Cohesion: 0.22
Nodes (3): test_media_link_binds_outbox_id_and_expires(), test_media_link_refuses_without_a_token(), token()

### Community 92 - "LumaQuote architecture"
Cohesion: 0.40
Nodes (5): Agent participation and recovery limits, Code ownership, LumaQuote architecture, Processes and trust boundaries, Semantic retrieval work in progress

### Community 93 - "observability.py"
Cohesion: 0.08
Nodes (21): embed_texts(), validate_embedding_provider(), MediaReading, _read_label(), read_media(), configured_secrets(), flush(), job_trace() (+13 more)

### Community 94 - "appsscript.json"
Cohesion: 0.33
Nodes (5): dependencies, exceptionLogging, oauthScopes, runtimeVersion, timeZone

### Community 95 - "Apps Script transport and validated commercial snapshots"
Cohesion: 0.20
Nodes (10): Apps Script transport and validated commercial snapshots, Atomic publication and offer freshness, Authority and process boundary, Diagnosis without leaking integration data, Drive export of approved quotations, Envelope authentication and replay, GAS source responsibilities, Signed Apps Script snapshot validation and atomic publication (+2 more)

### Community 96 - "frontend-live-updates"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/workspace/routes.py, app/frontend/src/features/workspace/api.ts, app/frontend/src/features/workspace/useLiveUpdates.ts, app/frontend/src/shared/api/events.ts, frontend-live-updates, bindings, height, renderer_sha256 (+3 more)

### Community 97 - "Sales and agent workflows"
Cohesion: 0.40
Nodes (5): Agent requests and evidence, Manual quotation, Notes, human replies and takeover, Sales and agent workflows, Voice and product-label photos

### Community 98 - "Google Apps Script integration"
Cohesion: 0.33
Nodes (6): Account setup, Evidence limits, Google Apps Script integration, Local receiver, Source responsibilities, Troubleshooting and verification

### Community 99 - "test_api_boundaries.py"
Cohesion: 0.05
Nodes (16): test_auth_outage_is_a_safe_503_not_an_open_door(), test_cors_allows_only_the_exact_local_origins(), test_declared_oversize_and_malformed_length_are_rejected_before_routing(), test_every_response_is_private_nosniff_and_unframed(), test_gateway_never_exposes_staff_routes_or_documentation(), test_missing_or_invalid_credentials_never_reach_business_code(), test_mutation_rate_limit_rejects_the_thirty_first_request_with_retry_guidance(), test_complete_snapshot_import_and_rejections() (+8 more)

### Community 100 - "Layer 3: Business features"
Cohesion: 0.29
Nodes (7): Changes on 2026-11-03, Extending safely, Layer 3: Business features, Open gaps, Rules every feature follows, Tests and evidence, Who calls what

### Community 101 - "embedding_inputs"
Cohesion: 0.07
Nodes (20): index_company(), embedding_inputs(), has_current_embeddings(), publish_embeddings(), semantic_search(), vector_literal(), Agent fallback and publication recheck, Cache identity and vector validation (+12 more)

### Community 102 - "Visual guide to LumaQuote"
Cohesion: 0.40
Nodes (5): Data and runtime, Layer views, Maintaining a view, Visual guide to LumaQuote, Workflow and architecture

### Community 103 - "Project documentation"
Cohesion: 0.50
Nodes (4): Current verification boundaries, Detailed implementation references, Documentation coverage and update ownership, Project documentation

### Community 104 - "test_quotation_rules.py"
Cohesion: 0.09
Nodes (15): assert_dispatchable(), calculate(), Admission and repeat submissions, Backend contracts and business transactions, Canonical quotation, exact approval and final dispatch checks, Composition and dependency direction, Drafting an immutable offer, Failure boundaries and evidence (+7 more)

### Community 105 - "rule-enforcement"
Cohesion: 0.17
Nodes (12): .claude/settings.json, scripts/check_docs.py, scripts/hooks/guard.py, scripts/skills.py, scripts/summarize_agent_run.py, rule-enforcement, bindings, height (+4 more)

### Community 106 - "Layer 1: Presentation (React staff workspace)"
Cohesion: 0.33
Nodes (6): Changes on 2026-11-03, Extending safely, Layer 1: Presentation (React staff workspace), Open gaps, Routes, Tests and evidence

### Community 108 - "Verified OpenAI contracts"
Cohesion: 0.67
Nodes (3): Embedding adapter under development, Photo label-reading contract, Verified OpenAI contracts

### Community 109 - "IMPLEMENTATION_PLAN.md"
Cohesion: 0.24
Nodes (3): Direction contract, Sales workspace direction, Synthetic development confirmation cases

### Community 111 - "test_live_job_trace_is_detailed_and_masked"
Cohesion: 0.15
Nodes (6): test_live_structured_extraction_prepares_only_review(), running_job(), test_older_preparation_preserves_staff_revision(), test_stale_extraction_cannot_ask_or_replace_draft(), read_trace(), test_live_job_trace_is_detailed_and_masked()

### Community 114 - "test_browser_workflow.py"
Cohesion: 0.13
Nodes (6): F8 - Whole-app visual and accessibility review with evidence (G9), run_review(), available_port(), test_complete_native_browser_workflow(), wait_for_server(), test_lighting_scene_review()

### Community 115 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.18
Nodes (11): 1. What went wrong so far (evidence from the work log and this session), 2. Principles, 3. The rulebook (replaces most of AGENTS.md + CLAUDE.md prose), 4.1 Make skills discoverable, 4.2 Consolidate 37 -> about 20 skills, 4.3 One routing table, 4. Skill routing, 5. Documentation: one home per fact (+3 more)

### Community 116 - "Working rules, skill routing and their enforcement"
Cohesion: 0.18
Nodes (11): Evaluation scoring pin (R11), Failure and recovery, Knowledge graph (decision D33), npm checks, Overview, Rule-to-enforcement map, `scripts/check_docs.py` details, `scripts/skills.py` details (+3 more)

### Community 117 - "media_links.py"
Cohesion: 0.16
Nodes (7): key(), load_pdf(), quotation_pdf(), quotation_url(), signature(), valid_signature(), test_signature_requires_the_sha256_prefix_hex_and_the_exact_body()

### Community 118 - "test_embedding_response_indices_bind_each_vector_to_its_requested_record"
Cohesion: 0.18
Nodes (5): test_embedding_response_indices_bind_each_vector_to_its_requested_record(), create(), test_invalid_provider_vectors_fail_closed(), test_valid_vector_has_only_finite_numeric_json(), unit_vector()

### Community 119 - "test_admission_limits.py"
Cohesion: 0.08
Nodes (16): early_in_minute(), first_denial(), test_approval_limit_is_10_per_minute(), test_catalog_search_limit_is_30_per_minute(), test_customer_messages_are_limited_per_conversation(), test_failed_requests_also_consume_admission(), test_queue_capacity_refuses_work_at_100_with_a_recoverable_503(), test_read_limit_is_120_per_minute() (+8 more)

### Community 145 - "Development tooling, verification and evidence interpretation"
Cohesion: 0.20
Nodes (10): Browser scenario and screenshots, Command ownership, Development tooling, verification and evidence interpretation, Explicit provider canaries, Git workflow, Historical checkpoint and remaining gates, Isolated integration environment, Offline and full gates (+2 more)

### Community 146 - "catalog.test.cjs"
Cohesion: 0.20
Nodes (5): assert, fs, os, path, test

### Community 147 - "test_surface_inventory.py"
Cohesion: 0.24
Nodes (4): operations(), test_gateway_exposes_only_signed_receivers_and_no_documentation_or_staff_route(), test_staff_api_directly_mounted_paths_are_health_and_documentation_only(), test_staff_api_surface_is_the_reviewed_inventory_and_only_health_is_open()

### Community 148 - "pin"
Cohesion: 0.22
Nodes (5): pin(), run_summarizer(), test_changed_or_missing_pin_is_refused_without_post_hoc(), test_matching_pin_is_scored_normally(), test_post_hoc_flag_labels_the_report()

### Community 149 - "Showcase shot list (90-120 seconds)"
Cohesion: 0.67
Nodes (3): Not shown (do not demonstrate or claim), Reproducible evidence behind each claim, Showcase shot list (90-120 seconds)

### Community 150 - "dependency_unavailable"
Cohesion: 0.17
Nodes (11): dependency_unavailable(), response_boundaries(), Layer 2: Transport (staff API and signed gateway), Open gaps, Request pipeline, Status codes a caller should expect, Tests and evidence, The two processes (+3 more)

### Community 151 - "_assert_no_canaries"
Cohesion: 0.19
Nodes (7): _assert_no_canaries(), _job(), test_exception_text_and_error_field_are_masked(), test_metadata_tags_and_job_payload_are_masked(), test_nested_tool_and_subgraph_runs_are_masked(), inner(), lookup_tool()

### Community 152 - "Voice and product-label media lifecycle"
Cohesion: 0.22
Nodes (8): PhotoReading, Durable state and provider admission, Failure response and evidence, Intake and durable acceptance, Photo reading contract, Publication and customer confirmation, Voice and product-label media lifecycle, Voice reading contract

### Community 154 - "Frontend work plan (for Sonnet execution)"
Cohesion: 0.25
Nodes (8): Acceptance for the whole plan, Branch, pull request and merge (decision D39), Execution protocol for Sonnet (read before every task), Frontend work plan (for Sonnet execution), How to start, Open questions for the user (not blocking any task; use the stated default), Run to completion (user instruction, 2026-11-03), Why this plan exists

### Community 157 - "Layer 6: Data (PostgreSQL and private Storage)"
Cohesion: 0.29
Nodes (7): Changes on 2026-11-03, Extending safely, Layer 6: Data (PostgreSQL and private Storage), Migrations, Open gaps, Retention and recovery, Who may reach what

### Community 160 - "get_detail"
Cohesion: 0.06
Nodes (19): test_descriptive_request_gets_cited_choices_before_selection(), test_duplicate_work_is_not_a_customer_answer(), _snapshot(), test_hostile_media_text_only_receives_fixed_clarification(), test_expired_operation_is_fenced_visible_and_not_retried(), observe(), test_live_label_reading_remains_unconfirmed(), get_detail() (+11 more)

### Community 161 - "json"
Cohesion: 0.12
Nodes (9): docker(), main(), object_paths(), prepare_scratch(), run(), snapshot(), source_params(), record_holdout_consumption() (+1 more)

### Community 164 - "drafting.py"
Cohesion: 0.12
Nodes (12): digest(), StrictModel, draft(), latest_quote(), Decision, DraftInput, Selection, detail() (+4 more)

### Community 165 - "Layer 4: Agent worker"
Cohesion: 0.40
Nodes (5): Layer 4: Agent worker, One tick, Open gaps, Spending and tracing, Tests and evidence

### Community 166 - "pull_request_template.md"
Cohesion: 0.40
Nodes (4): Changes, Problem, Risks and open items, Validation

### Community 167 - "Layer 7: External integrations"
Cohesion: 0.33
Nodes (6): Changes on 2026-11-03, Extending safely, Gates and proof, Layer 7: External integrations, Open gaps, Shared rules

### Community 168 - "LumaQuote by layer"
Cohesion: 0.33
Nodes (6): Keeping these guides current, Layer map, LumaQuote by layer, One request through every layer, Other views, The layers

### Community 171 - "Cross-cutting layer: verification and tooling"
Cohesion: 0.40
Nodes (5): Changes on 2026-11-03, Cross-cutting layer: verification and tooling, Open gaps, Test families by layer, The verify gate

## Knowledge Gaps
- **1 isolated node(s):** `lumaquote`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1764 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **59 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `audit()` connect `conversation` to `provider.py`, `test_job_trace_exports_graph_and_model_runs_masked`, `drafting.py`, `embedding_inputs`, `test_twilio.py`, `DocumentButton`, `Persistent data, privileges and migration lifecycle`, `DomainError`, `database`, `AppShell.tsx`, `check_frontend.cjs`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `DomainError` (e.g. with `embed_texts()` and `validate_embedding_provider()`) actually correct?**
  _`DomainError` has 49 INFERRED edges - model-reasoned connections that need verification._
- **What connects `lumaquote` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `psycopg` be split into smaller, more focused modules?**
  _Cohesion score 0.05130818892286782 - nodes in this community are weakly interconnected._
- **Why does `DomainError` connect `DomainError` to `psycopg`, `semantic.py`, `conversation`, `decimal`, `worker.py`, `extraction.py`, `database`, `io`, `Voice and product-label media lifecycle`, `workflow.py`, `get_detail`, `drafting.py`, `Layer 4: Agent worker`, `settings`, `webhook.py`, `workspace/routes.py`, `test_twilio.py`, `core/errors.py`, `test_twilio_signature.py`, `observability.py`, `embedding_inputs`, `test_quotation_rules.py`, `test_live_job_trace_is_detailed_and_masked`, `media_links.py`, `test_embedding_response_indices_bind_each_vector_to_its_requested_record`, `test_admission_limits.py`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `settings()` (e.g. with `Where it lives` and `Loading and restart semantics`) actually correct?**
  _`settings()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `settings` be split into smaller, more focused modules?**
  _Cohesion score 0.07575757575757576 - nodes in this community are weakly interconnected._