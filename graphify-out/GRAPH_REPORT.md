# Graph Report - Demo_Project_4  (2026-11-03)

## Corpus Check
- 292 files · ~202,178 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 38 file(s) not represented in the graph (top: .mmd 18, .css 8, .gs 5)

## Summary
- 2604 nodes · 5914 edges · 163 communities (110 shown, 53 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 304 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ebc1b4a9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- psycopg
- test_expired_operation_is_fenced_visible_and_not_retried
- semantic.py
- October 29, 2026 - Offline embedding contract tests and engine recovery result
- conversation
- hashlib
- frontend/package.json
- test_whatsapp.py
- test_evaluation_dataset.py
- database
- test_drive_exports.py
- evaluate_scenarios.py
- cn
- test_agent_rules.py
- Button
- datetime
- App.tsx
- worker.py
- workflow.py
- extraction.py
- catalog/schemas.py
- clarification_for
- re
- test_browser_workflow.py
- scripts
- media/routes.py
- workspace/schemas.py
- media_host_allowed
- skills.py
- Apps Script transport and validated commercial snapshots
- whatsapp_client.py
- Proposal: working rules, skill routing and documentation (draft for approval)
- begin
- index.cjs
- catalog_index.py
- settings
- scan_secrets.py
- steps
- retention.py
- Design System: LumaQuote
- useQuotationDraft
- ref_node_path
- compilerOptions
- backup_restore_drill.py
- job-recovery
- quotation-approval
- Test layers
- Persistent data, privileges and migration lifecycle
- create_request
- LumaQuote implementation tracker
- components.json
- Work log
- main
- api/client.ts
- guard.py
- argparse
- check_frontend.cjs
- freeze_evaluation.py
- DomainError
- processor.py
- manual-workflow.cjs
- test_embedding_response_indices_bind_each_vector_to_its_requested_record
- Button
- message_id
- bindings
- whatsapp-channel
- LumaQuote
- start-local-supabase.cjs
- pin
- catalog-retrieval
- system-boundaries
- staff-operation
- google-snapshot
- drive-export
- workflow-data
- requirement-policy/README.md
- evaluation_dataset.py
- estimated-allowance
- frontend-draft
- verification-scope
- catalog.test.cjs
- wav_bytes
- conversation-data
- Local Supabase
- database.py
- check_architecture.py
- environment
- LumaQuote
- Configuration and native process operation
- ref_node_fs
- LightingScene.tsx
- LumaQuote architecture
- test_semantic_catalog.py
- appsscript.json
- test_trace_exports_only_opaque_identity_and_safe_outcome
- subprocess
- Sales and agent workflows
- test_agent_semantic_fallback_preserves_action_and_source_boundaries
- test_every_response_is_private_nosniff_and_unframed
- pending
- outbound.py
- Visual guide to LumaQuote
- Project documentation
- test_operator_index_settles_or_blocks_uncertain_retries
- rule-enforcement
- test_staff_replies.py
- CLAUDE.md
- Verified OpenAI contracts
- Showcase shot list (90-120 seconds)
- UI_DIRECTION.md
- test_workspace_reports_only_complete_tenant_mapped_gas_configuration
- Proposal: working rules, skill routing and documentation (draft for approval)
- Working rules, skill routing and their enforcement
- re
- lumaquote
- validate
- Development tooling, verification and evidence interpretation
- GraphError
- Voice and product-label media lifecycle
- staff
- allowed_senders
- sales-workflow
- Agent state, participation, spending and recovery
- Google Apps Script integration
- record_holdout_consumption
- test_controlled_provider_cannot_invent_customer_confirmation
- test_unresolved_prior_day_call_still_consumes_daily_allowance
- test_signed_callback_receipts
- test_provider_failure_and_worker_logs_do_not_leak_canaries
- test_oversized_context_is_not_trimmed_into_positive_order
- test_holdout_is_refused_unless_frozen_unspent_and_confirmed
- test_staff_escalation_is_an_accepted_safe_alternative_for_media_only
- test_counts_and_family_split_match_the_plan

## God Nodes (most connected - your core abstractions)
1. `DomainError` - 118 edges
2. `October 29, 2026 - Offline embedding contract tests and engine recovery result` - 81 edges
3. `database()` - 72 edges
4. `get_detail()` - 69 edges
5. `create_request()` - 61 edges
6. `settings()` - 54 edges
7. `post()` - 54 edges
8. `cn()` - 42 edges
9. `make_draft()` - 36 edges
10. `scripts` - 35 edges

## Surprising Connections (you probably didn't know these)
- `Agent fallback and publication recheck` --references--> `ask()`  [INFERRED]
  docs/reference/CATALOG.md → app/agents/luma_agent/nodes/workflow.py
- `Command ownership` --references--> `prepare()`  [INFERRED]
  docs/reference/TOOLING_AND_TESTS.md → app/agents/luma_agent/nodes/workflow.py
- `2. Principles` --references--> `review()`  [INFERRED]
  docs/proposals/2026-11-03-working-rules.md → app/agents/luma_agent/nodes/workflow.py
- `2026-11-01 - Unit policy gate passed; persisted-workflow regressions added` --references--> `review()`  [INFERRED]
  docs/WORK_LOG.md → app/agents/luma_agent/nodes/workflow.py
- `Trace privacy and debugging` --references--> `trace_outcome()`  [INFERRED]
  docs/reference/AGENT_RUNTIME.md → app/agents/luma_agent/observability.py

## Import Cycles
- None detected.

## Communities (163 total, 53 thin omitted)

### Community 0 - "psycopg"
Cohesion: 0.06
Nodes (22): test_duplicate_paid_operation_never_reserves_again(), test_retrieval_requires_settled_room_and_cannot_repeat(), test_expiry_recovery_skips_another_transactions_locked_job(), observe(), run_turns(), seed_catalog(), spent(), test_agent_on_development_scenario() (+14 more)

### Community 1 - "test_expired_operation_is_fenced_visible_and_not_retried"
Cohesion: 0.12
Nodes (9): test_expired_operation_is_fenced_visible_and_not_retried(), test_live_label_reading_remains_unconfirmed(), photo_bytes(), photo_job(), test_corrupt_photo_is_rejected_before_provider_use(), test_photo_normalizes_to_private_jpeg_without_paid_reading(), test_photo_stream_limit_and_replay_binding(), test_unknown_provider_outcome_retains_reservation_and_never_retries() (+1 more)

### Community 2 - "semantic.py"
Cohesion: 0.08
Nodes (21): query_constraints(), SearchCriteria, candidate_question(), search_catalog(), CatalogHit, CatalogSearch, has_current_embeddings(), semantic_search() (+13 more)

### Community 3 - "October 29, 2026 - Offline embedding contract tests and engine recovery result"
Cohesion: 0.03
Nodes (74): 2026-10-29 - Agent fallback boundary tests added, 2026-10-29 - Agent fallback checks passed and evidence consolidated, 2026-10-29 - All Mermaid views rendered locally, 2026-10-29 - Configuration and verification reference coverage, 2026-10-29 — Current workflow documentation and screenshot reviewed, 2026-10-29 — Database gates passed; browser startup assertion failed, 2026-10-29 - Deep agent, media and retrieval references, 2026-10-29 - Deep backend and persistence documentation (+66 more)

### Community 4 - "conversation"
Cohesion: 0.07
Nodes (26): _deliver_local(), enqueue(), audit(), accept_customer_text(), change_ownership(), queue_staff_reply(), record_customer_reply(), record_note() (+18 more)

### Community 5 - "hashlib"
Cohesion: 0.03
Nodes (36): accept_hint(), EditHint, verify_hint(), verify_mapping(), verify_signature(), claim_export(), ClaimRequest, drive_filename() (+28 more)

### Community 6 - "frontend/package.json"
Cohesion: 0.04
Nodes (65): dependencies, class-variance-authority@^0.7.1, clsx@^2.1.1, cn@^0.4.0, @fontsource/ibm-plex-sans@^5.3.0, @fontsource-variable/space-grotesk@^5.3.0, lucide-react@^1.63.0, radix-ui@^1.8.1 (+57 more)

### Community 7 - "test_whatsapp.py"
Cohesion: 0.08
Nodes (29): deliver_one(), conversation_for(), deliver_webhook(), drain(), envelope(), graph(), Graph, outbox() (+21 more)

### Community 8 - "test_evaluation_dataset.py"
Cohesion: 0.09
Nodes (11): 2026-11-02 - Holdout freeze guard (phase 6 preparation, offline), loaded(), test_every_media_turn_has_a_hashed_asset_and_stays_unconfirmed(), test_family_table_matches_the_bootstrap_catalog(), test_freeze_blocks_the_holdout_until_pinned_unchanged_and_unspent(), test_media_manifest_never_records_outcomes(), test_runtime_code_never_reads_the_answer_key(), test_scenarios_never_contain_answers() (+3 more)

### Community 9 - "database"
Cohesion: 0.07
Nodes (25): rate_limit(), database(), operation(), membership(), search(), source_pdf(), customer_reply(), execute() (+17 more)

### Community 10 - "test_drive_exports.py"
Cohesion: 0.13
Nodes (13): 2026-11-02 - Concurrency tests, showcase shot list and screenshots; CI result, approve(), approved_quote(), exports(), poller(), Poller, test_changed_pdf_blocks_the_export_instead_of_shipping_different_bytes(), test_concurrent_pollers_cannot_claim_the_same_export() (+5 more)

### Community 11 - "evaluate_scenarios.py"
Cohesion: 0.12
Nodes (9): decide(), evaluate(), load_catalog(), main(), run_scenario(), denominators(), fingerprints(), load() (+1 more)

### Community 12 - "cn"
Cohesion: 0.10
Nodes (37): SignIn(), ConversationCommand, NewRequest(), Conversation, cn(), Badge(), badgeVariants, Empty() (+29 more)

### Community 13 - "test_agent_rules.py"
Cohesion: 0.11
Nodes (9): docs_root(), test_r10_ticked_items_need_evidence_and_phase_4_needs_live(), test_r14_stop_requires_work_log_and_docs_for_code(), test_r15_bash_guard(), test_r6_edit_guard_warns_on_large_deletions(), test_r8_flags_mojibake_crlf_and_broken_links_but_not_quoted_code(), test_r9_requires_header_and_allowed_label_for_new_evidence(), test_skills_frontmatter_and_routing() (+1 more)

### Community 14 - "Button"
Cohesion: 0.11
Nodes (19): load(), QuotationPanel(), ProductSelections(), QuoteSummary(), ReviewActions(), EditableLine, documentUrl(), ConversationDetail (+11 more)

### Community 15 - "datetime"
Cohesion: 0.09
Nodes (16): assert_dispatchable(), calculate(), Admission and repeat submissions, Approval, freshness and dispatch, Backend contracts and business transactions, Canonical quotation, exact approval and final dispatch checks, Composition and dependency direction, Drafting an immutable offer (+8 more)

### Community 16 - "App.tsx"
Cohesion: 0.25
Nodes (17): App(), CatalogPage(), InboxPage(), connections, ConnectionsPage(), LightingScene, Overview(), QuotationsPage() (+9 more)

### Community 17 - "worker.py"
Cohesion: 0.07
Nodes (25): trace_outcome(), process_audio(), process_conversation(), claim_job(), finish_job(), process_media(), recover_expired(), main() (+17 more)

### Community 18 - "workflow.py"
Cohesion: 0.09
Nodes (19): build_graph(), route(), assert_job(), assert_request_version(), retrieve(), ask(), clarify(), prepare() (+11 more)

### Community 19 - "extraction.py"
Cohesion: 0.12
Nodes (12): baseline_extract(), extract(), clarification_for(), Extraction, RequestedLine, parse_written_request(), Extraction and consequential-field confirmation, test_development_confirmation_policy() (+4 more)

### Community 20 - "catalog/schemas.py"
Cohesion: 0.22
Nodes (5): StrictModel, DraftInput, Selection, test_concurrent_edits_allow_only_one_observed_version(), save()

### Community 21 - "clarification_for"
Cohesion: 0.12
Nodes (11): Integration coverage by responsibility, 2026-11-02 - Negative (mutation-style) checks for hostile-content tests, extracted(), test_duplicate_sku_requires_clarification(), test_empty_placeholder_lines_do_not_suppress_candidate_discovery(), test_explicit_matching_text_confirms_media_fields(), test_media_alone_cannot_confirm_itself(), test_media_requires_exact_written_critical_fields() (+3 more)

### Community 22 - "re"
Cohesion: 0.14
Nodes (9): degrade(), main(), make_voice(), mix(), noise(), read_wave(), spoken(), synthesize() (+1 more)

### Community 23 - "test_browser_workflow.py"
Cohesion: 0.21
Nodes (3): available_port(), test_complete_native_browser_workflow(), wait_for_server()

### Community 24 - "scripts"
Cohesion: 0.04
Nodes (48): devDependencies, @google/clasp@3.4.1, supabase@2.122.0, typescript@5.9.3, typescript, name, overrides, typescript (+40 more)

### Community 25 - "media/routes.py"
Cohesion: 0.19
Nodes (4): audio_playback(), image_preview(), upload_audio(), upload_image()

### Community 26 - "workspace/schemas.py"
Cohesion: 0.09
Nodes (14): ActivityView, CompanyView, ConversationDetail, ConversationView, DeliveryView, JobView, MessageView, ProductView (+6 more)

### Community 28 - "skills.py"
Cohesion: 0.12
Nodes (13): active_skills(), check_frontmatter(), check_links(), check_manifests(), check_mirror(), check_routing(), digest(), located() (+5 more)

### Community 29 - "Apps Script transport and validated commercial snapshots"
Cohesion: 0.20
Nodes (10): Apps Script transport and validated commercial snapshots, Atomic publication and offer freshness, Authority and process boundary, Diagnosis without leaking integration data, Drive export of approved quotations, Envelope authentication and replay, GAS source responsibilities, Signed Apps Script snapshot validation and atomic publication (+2 more)

### Community 30 - "whatsapp_client.py"
Cohesion: 0.23
Nodes (5): call(), download(), fetch_media(), headers(), make_client()

### Community 31 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.15
Nodes (12): Code layout, Commands, Documentation (decisions D30, D33), LumaQuote working rules, Rules, Skill routing, Unattended work and accounts, AI, evaluation and tracing (+4 more)

### Community 32 - "begin"
Cohesion: 0.14
Nodes (13): begin(), block(), record(), Configuration (names only), Data, Egress, Failure and recovery, Inbound media (+5 more)

### Community 33 - "index.cjs"
Cohesion: 0.14
Nodes (22): mermaid@11.17.2, mermaid, crypto, embeddedBlock(), existingFile(), fingerprint(), fs, hash() (+14 more)

### Community 34 - "catalog_index.py"
Cohesion: 0.08
Nodes (11): embed_texts(), validate_embedding_provider(), MediaReading, PhotoReading, read_media(), validate_media_provider(), reserve(), usage_totals() (+3 more)

### Community 35 - "settings"
Cohesion: 0.11
Nodes (12): run_media(), settings(), Settings, delete_files(), get_file(), put_file(), storage_headers(), quotation_pdf() (+4 more)

### Community 36 - "scan_secrets.py"
Cohesion: 0.14
Nodes (9): load_secrets(), main(), run(), scan_files(), tracked_files(), make_repo(), test_clean_repo_reports_no_leaks(), test_only_secret_looking_long_nonpublic_values_are_loaded() (+1 more)

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
Cohesion: 0.14
Nodes (18): draftSuite(), capturesLatestCleanVersion(), preservesConflict(), fixture(), useQuotationDraft(), beginEdit(), updateDiscount(), updateLines() (+10 more)

### Community 41 - "ref_node_path"
Cohesion: 0.11
Nodes (12): fs, path, root, { spawnSync }, fs, path, root, { spawnSync } (+4 more)

### Community 42 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, baseUrl, esModuleInterop, jsx, lib, module, moduleResolution (+10 more)

### Community 43 - "backup_restore_drill.py"
Cohesion: 0.13
Nodes (8): docker(), main(), object_paths(), prepare_scratch(), run(), snapshot(), source_params(), main()

### Community 44 - "job-recovery"
Cohesion: 0.11
Nodes (19): app/agents/luma_agent/lease.py, app/agents/luma_agent/runtime/jobs.py, app/agents/luma_agent/runtime/recovery.py, app/backend/luma/features/media/intake.py, app/backend/luma/features/media/persistence.py, job-recovery, media-lifecycle, bindings (+11 more)

### Community 45 - "quotation-approval"
Cohesion: 0.33
Nodes (6): quotation-approval, height, renderer_sha256, source_sha256, svg_sha256, width

### Community 46 - "Test layers"
Cohesion: 0.11
Nodes (19): 10. Security, privacy, and abuse tests, 11. Concurrency, fault injection, and recovery tests, 12. Performance, accessibility, and visual acceptance, 1. Static and build checks, 2. Unit tests, 3. Property and state-machine tests, 4. Frontend component tests, 5. API and provider contract tests (+11 more)

### Community 47 - "Persistent data, privileges and migration lifecycle"
Cohesion: 0.11
Nodes (18): components, $defs, operations, paths, webhooks, Catalog, commercial snapshot and current embedding relationships, Checkpoints, retention and preservation, Conversation and quotation records (+10 more)

### Community 48 - "create_request"
Cohesion: 0.05
Nodes (29): test_auth_outage_is_a_safe_503_not_an_open_door(), test_cors_allows_only_the_exact_local_origins(), test_declared_oversize_and_malformed_length_are_rejected_before_routing(), test_gateway_never_exposes_staff_routes_or_documentation(), test_mutation_rate_limit_rejects_the_thirty_first_request_with_retry_guidance(), test_private_pdf_is_never_cacheable(), test_populated_tenant_restores_identically_with_checkpoints_and_objects(), search() (+21 more)

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

### Community 54 - "api/client.ts"
Cohesion: 0.24
Nodes (10): useConversation(), useWorkspace(), ApiError, request(), Workspace, auth, SessionContext, useSession() (+2 more)

### Community 55 - "guard.py"
Cohesion: 0.14
Nodes (12): `bash` (PreToolUse on Bash, R15), Claude Code hooks, `edit` (PostToolUse on Edit and Write, R6), `stop` (Stop, R14 and R8-R10), bash(), block(), changed_paths(), edit() (+4 more)

### Community 56 - "argparse"
Cohesion: 0.16
Nodes (6): evaluate(), main(), summarize(), divergence(), main(), summarize()

### Community 57 - "check_frontend.cjs"
Cohesion: 0.21
Nodes (11): definitionName(), fs, inspect(), walk(), main(), visit(), path, resolveImport() (+3 more)

### Community 58 - "freeze_evaluation.py"
Cohesion: 0.19
Nodes (6): freeze_fingerprints(), freeze_problems(), load_freeze(), check(), main(), write()

### Community 59 - "DomainError"
Cohesion: 0.06
Nodes (22): digest(), DomainError, InputRecord, InventoryInput, PolicyInput, PriceInput, ProductInput, SnapshotEnvelope (+14 more)

### Community 60 - "processor.py"
Cohesion: 0.22
Nodes (4): inspect_audio(), inspect_image(), inspect_pdf(), main()

### Community 61 - "manual-workflow.cjs"
Cohesion: 0.31
Nodes (8): { chromium, expect }, dispatchFixture(), fs, main(), path, processMediaFixture(), { spawnSync }, syntheticVoice()

### Community 62 - "test_embedding_response_indices_bind_each_vector_to_its_requested_record"
Cohesion: 0.15
Nodes (6): test_embedding_response_indices_bind_each_vector_to_its_requested_record(), create(), test_invalid_provider_vectors_fail_closed(), test_shared_filters_refuse_ambiguous_or_negated_requirements(), test_valid_vector_has_only_finite_numeric_json(), unit_vector()

### Community 63 - "Button"
Cohesion: 0.16
Nodes (16): AppShell(), navigation, useConversationAction(), ConversationComposer(), ConversationThread(), MediaPreview(), MediaUpload(), Alert() (+8 more)

### Community 64 - "message_id"
Cohesion: 0.22
Nodes (7): message_id(), Binary attachment protocol, Command payloads and a review sequence, Errors and limits, Regenerating contracts, Staff API reference, Staff identity, idempotency and optimistic mutation protocol

### Community 65 - "bindings"
Cohesion: 0.17
Nodes (12): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/agents/luma_agent/graph.py, app/agents/luma_agent/nodes/extraction.py (+4 more)

### Community 66 - "whatsapp-channel"
Cohesion: 0.11
Nodes (19): app/agents/luma_agent/runtime/delivery.py, app/backend/luma/features/conversations/participation.py, app/backend/luma/features/messaging/inbound.py, app/backend/luma/features/messaging/outbound.py, app/backend/luma/features/messaging/webhook.py, app/backend/luma/features/messaging/whatsapp_client.py, app/backend/luma/features/quotations/approval.py, app/backend/luma/features/quotations/drafting.py (+11 more)

### Community 67 - "LumaQuote"
Cohesion: 0.17
Nodes (11): Accessibility & Inclusion, Brand Commitments, Capabilities and Constraints, Evidence on Hand, LumaQuote, Operating Context, Platform, Product Principles (+3 more)

### Community 68 - "start-local-supabase.cjs"
Cohesion: 0.18
Nodes (10): api(), databaseClients, { execFileSync, spawnSync }, fs, http, names, path, privateDir (+2 more)

### Community 69 - "pin"
Cohesion: 0.22
Nodes (5): pin(), run_summarizer(), test_changed_or_missing_pin_is_refused_without_post_hoc(), test_matching_pin_is_scored_normally(), test_post_hoc_flag_labels_the_report()

### Community 70 - "catalog-retrieval"
Cohesion: 0.20
Nodes (9): height, renderer_sha256, source_sha256, svg_sha256, width, diagrams, catalog-retrieval, mermaid_version (+1 more)

### Community 71 - "system-boundaries"
Cohesion: 0.18
Nodes (11): app/agents/luma_agent/worker.py, app/backend/luma/features/media/sandbox.py, app/backend/luma/google_gateway.py, app/backend/luma/main.py, system-boundaries, bindings, height, renderer_sha256 (+3 more)

### Community 72 - "staff-operation"
Cohesion: 0.18
Nodes (11): app/backend/luma/core/database.py, app/backend/luma/core/http.py, app/backend/luma/core/idempotency.py, app/backend/luma/features/quotations/routes.py, staff-operation, bindings, height, renderer_sha256 (+3 more)

### Community 73 - "google-snapshot"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/google_sync/callbacks.py, app/backend/luma/features/google_sync/snapshots.py, app/backend/luma/features/google_sync/validation.py, gas/Synchronization.gs, google-snapshot, bindings, height, renderer_sha256 (+3 more)

### Community 74 - "drive-export"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/google_sync/exports.py, app/backend/luma/features/quotations/documents.py, gas/Exports.gs, supabase/migrations/20261102000000_drive_exports.sql, drive-export, bindings, height, renderer_sha256 (+3 more)

### Community 75 - "workflow-data"
Cohesion: 0.12
Nodes (17): supabase/migrations/20261029010000_quotation_domain.sql, supabase/migrations/20261029100000_immutable_quotation_content.sql, supabase/migrations/20261029131000_versioned_embeddings.sql, evidence-data, workflow-data, bindings, height, renderer_sha256 (+9 more)

### Community 77 - "evaluation_dataset.py"
Cohesion: 0.12
Nodes (8): _check_outcome(), subtotal(), supported(), test_fingerprints_are_stable_hex_digests(), test_validator_rejects_a_family_crossing_the_holdout_boundary(), test_validator_rejects_a_wrong_subtotal(), test_validator_rejects_media_confirming_a_field(), test_validator_rejects_missing_oracle_entry()

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

### Community 82 - "wav_bytes"
Cohesion: 0.13
Nodes (7): test_image_is_normalized_without_metadata(), test_native_pdf_retains_original_page_text(), test_overlong_audio_is_rejected_before_transcription(), age(), one(), test_runtime_media_is_deleted_after_seven_days_but_text_and_thread_remain(), wav_bytes()

### Community 83 - "conversation-data"
Cohesion: 0.22
Nodes (9): supabase/migrations/20261029110000_voice_intake.sql, supabase/migrations/20261029111000_media_message_binding.sql, bindings, height, renderer_sha256, source_sha256, svg_sha256, width (+1 more)

### Community 84 - "Local Supabase"
Cohesion: 0.22
Nodes (9): Conflicts, unavailable infrastructure and evidence, Credentials and application configuration, Local Supabase, Media and worker diagnosis, Native processes and optional provider work, Schema, Semantic index command under development, Services (+1 more)

### Community 85 - "database.py"
Cohesion: 0.09
Nodes (8): domain_error(), response_boundaries(), receive_upload(), workspace(), events(), stream(), workspace(), health()

### Community 88 - "LumaQuote"
Cohesion: 0.25
Nodes (8): Documentation, LumaQuote, LumaQuote request-to-reviewed-offer workflow, Run locally, Status and next actions, Structure, Verification, Workflow at a glance

### Community 89 - "Configuration and native process operation"
Cohesion: 0.29
Nodes (7): Configuration and native process operation, Messaging and Google configuration, Paid AI policy, Private generated files and reproducibility, Safe routine operation, Supabase and database identities, Tracing policy

### Community 90 - "ref_node_fs"
Cohesion: 0.29
Nodes (4): fs, path, root, { spawnSync }

### Community 91 - "LightingScene.tsx"
Cohesion: 0.18
Nodes (9): @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2, LightingScene(), Luminaire(), LightingFallback(), SceneBoundary, Optional 3D and presentation limits, @react-three/drei (+1 more)

### Community 92 - "LumaQuote architecture"
Cohesion: 0.33
Nodes (6): Agent participation and recovery limits, Code ownership, Durable business state, LumaQuote architecture, Processes and trust boundaries, Semantic retrieval work in progress

### Community 93 - "test_semantic_catalog.py"
Cohesion: 0.22
Nodes (6): embedding_inputs(), publish_embeddings(), Operator indexing, publish_fixture(), test_index_publication_rejects_changed_input(), test_semantic_candidates_obey_scope_specs_and_exact_codes()

### Community 94 - "appsscript.json"
Cohesion: 0.33
Nodes (5): dependencies, exceptionLogging, oauthScopes, runtimeVersion, timeZone

### Community 96 - "subprocess"
Cohesion: 0.23
Nodes (3): bounded_output(), process_file(), test_corrupt_files_are_rejected()

### Community 97 - "Sales and agent workflows"
Cohesion: 0.40
Nodes (5): Agent requests and evidence, Manual quotation, Notes, human replies and takeover, Sales and agent workflows, Voice and product-label photos

### Community 100 - "pending"
Cohesion: 0.11
Nodes (11): pending(), run_next(), test_customer_clarification_resumes_after_restart(), test_descriptive_request_gets_cited_choices_before_selection(), test_duplicate_work_is_not_a_customer_answer(), test_staff_decision_resumes_review_after_restart(), test_voice_waits_for_processing_and_exact_written_confirmation(), _snapshot() (+3 more)

### Community 101 - "outbound.py"
Cohesion: 0.24
Nodes (5): submit(), endpoint(), send_document(), send_text(), upload_pdf()

### Community 102 - "Visual guide to LumaQuote"
Cohesion: 0.50
Nodes (4): Data and runtime, Maintaining a view, Visual guide to LumaQuote, Workflow and architecture

### Community 103 - "Project documentation"
Cohesion: 0.50
Nodes (4): Current verification boundaries, Detailed implementation references, Documentation coverage and update ownership, Project documentation

### Community 105 - "rule-enforcement"
Cohesion: 0.17
Nodes (12): .claude/settings.json, scripts/check_docs.py, scripts/hooks/guard.py, scripts/skills.py, scripts/summarize_agent_run.py, rule-enforcement, bindings, height (+4 more)

### Community 106 - "test_staff_replies.py"
Cohesion: 0.26
Nodes (5): queue_reply(), take_over(), test_human_reply_requires_takeover_and_remains_distinct_from_notes(), test_reply_author_revocation_is_checked_at_dispatch(), test_resuming_automation_cancels_unsent_human_reply()

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

### Community 117 - "re"
Cohesion: 0.22
Nodes (4): draw_label(), font(), make_photo(), sticker_text()

### Community 144 - "validate"
Cohesion: 0.20
Nodes (5): catalog_model(), _check_retrieval(), _check_structure(), _check_turns(), validate()

### Community 145 - "Development tooling, verification and evidence interpretation"
Cohesion: 0.22
Nodes (9): Browser scenario and screenshots, Command ownership, Development tooling, verification and evidence interpretation, Explicit provider canaries, Historical checkpoint and remaining gates, Isolated integration environment, Offline and full gates, Offline, local integration and explicit live evidence boundaries (+1 more)

### Community 147 - "Voice and product-label media lifecycle"
Cohesion: 0.29
Nodes (7): Durable state and provider admission, Failure response and evidence, Fixed sandbox boundary, Intake and durable acceptance, Publication and customer confirmation, Voice and product-label media lifecycle, Voice reading contract

### Community 150 - "sales-workflow"
Cohesion: 0.33
Nodes (6): sales-workflow, height, renderer_sha256, source_sha256, svg_sha256, width

### Community 151 - "Agent state, participation, spending and recovery"
Cohesion: 0.33
Nodes (6): Agent state, participation, spending and recovery, Durable thread routing and restart, Estimated allowance lifecycle, Expired-job fencing and conservative uncertainty recovery, Interrupted work and unknown outcomes, Trace privacy and debugging

### Community 152 - "Google Apps Script integration"
Cohesion: 0.33
Nodes (6): Account setup, Evidence limits, Google Apps Script integration, Local receiver, Source responsibilities, Troubleshooting and verification

### Community 154 - "test_controlled_provider_cannot_invent_customer_confirmation"
Cohesion: 0.50
Nodes (3): test_controlled_provider_cannot_invent_customer_confirmation(), client_fixture(), parse_fixture()

## Knowledge Gaps
- **1 isolated node(s):** `lumaquote`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1349 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **53 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Voice and product-label media lifecycle` connect `Voice and product-label media lifecycle` to `catalog_index.py`, `docs/README.md`, `Button`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Are the 44 inferred relationships involving `DomainError` (e.g. with `embed_texts()` and `validate_embedding_provider()`) actually correct?**
  _`DomainError` has 44 INFERRED edges - model-reasoned connections that need verification._
- **What connects `lumaquote` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `psycopg` be split into smaller, more focused modules?**
  _Cohesion score 0.05669050051072523 - nodes in this community are weakly interconnected._
- **Why does `DomainError` connect `DomainError` to `psycopg`, `test_expired_operation_is_fenced_visible_and_not_retried`, `semantic.py`, `conversation`, `hashlib`, `test_whatsapp.py`, `database`, `datetime`, `worker.py`, `workflow.py`, `extraction.py`, `staff`, `Voice and product-label media lifecycle`, `catalog/schemas.py`, `media/routes.py`, `catalog_index.py`, `settings`, `test_embedding_response_indices_bind_each_vector_to_its_requested_record`, `wav_bytes`, `database.py`, `test_semantic_catalog.py`, `subprocess`, `test_operator_index_settles_or_blocks_uncertain_retries`?**
  _High betweenness centrality (0.155) - this node is a cross-community bridge._
- **Should `test_expired_operation_is_fenced_visible_and_not_retried` be split into smaller, more focused modules?**
  _Cohesion score 0.12105263157894737 - nodes in this community are weakly interconnected._
- **Why does `MediaUpload()` connect `Button` to `Voice and product-label media lifecycle`, `cn`, `api/client.ts`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._