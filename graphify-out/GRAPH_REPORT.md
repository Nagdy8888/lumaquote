# Graph Report - Demo_Project_4  (2026-11-11)

## Corpus Check
- 447 files · ~389,437 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 55 file(s) not represented in the graph (top: .mmd 31, .css 10, .gs 7)

## Summary
- 4581 nodes · 11329 edges · 233 communities (158 shown, 75 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 862 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `de61dff3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- psycopg
- telegram_client.py
- test_semantic_catalog.py
- October 29, 2026 - Offline embedding contract tests and engine recovery result
- test_stock_staff_routes.py
- decimal
- frontend/package.json
- test_whatsapp.py
- evaluation_dataset.py
- StrictModel
- make_draft
- evaluate_scenarios.py
- ResponseModel
- Button
- AudioWaveform
- settings
- ConversationThread.tsx
- test_twilio.py
- clarification_for
- validate
- Overview.tsx
- DomainError
- re
- Development tooling, verification and evidence interpretation
- scripts
- ReceiptRequest
- json
- FixtureInspector.tsx
- skills.py
- test_stock_acceptance.py
- test_trace_masking.py
- Proposal: working rules, skill routing and documentation (draft for approval)
- prepare
- index.cjs
- post
- inventory/api.ts
- io
- steps
- retention.py
- Design System: LumaQuote
- lucide-react
- ref_node_path
- compilerOptions
- Stock, customer orders and supplier purchasing: implementation plan
- estimated-allowance
- quotation-approval
- Test layers
- test_approved_quotation_is_sent_as_the_exact_canonical_pdf
- ledger.py
- LumaQuote implementation tracker
- components.json
- Work log
- main
- useLiveUpdates.ts
- whatsapp_client.py
- rate_limit
- check_frontend.cjs
- operation
- package.json
- twilio_webhook.py
- manual-workflow.cjs
- deliver_one
- vitest
- job-recovery
- bindings
- whatsapp-channel
- LumaQuote
- start-local-supabase.cjs
- StockReceiptRequest
- catalog-retrieval
- Email channel (Gmail through Apps Script)
- diagrams
- google-snapshot
- drive-export
- workflow-data
- bindings
- dependencies
- backend-modules
- frontend-draft
- verification-scope
- ui-review.cjs
- purchasing/service.py
- authorization.py
- Local Supabase
- media/routes.py
- test_controlled_provider_cannot_invent_customer_confirmation
- Morning actions
- LumaQuote
- Configuration and native process operation
- page-review.cjs
- workflow.py
- LumaQuote architecture
- database.py
- appsscript.json
- inventory/exports.py
- frontend-live-updates
- Sales and agent workflows
- test_acceptance_phrases.py
- guard.py
- Backend contracts and business transactions
- order-lifecycle
- Visual guide to LumaQuote
- Project documentation
- uuid
- rule-enforcement
- test_embedding_contracts.py
- CLAUDE.md
- Verified OpenAI contracts
- IMPLEMENTATION_PLAN.md
- run
- scripts
- test_agent_rules.py
- inventory/queries.py
- health
- scan_secrets.py
- database
- test_stock_ledger.py
- test_brain.py
- reduce_mail
- settings
- lumaquote
- message
- Telegram channel (Bot API, long polling)
- Retry
- test_surface_inventory.py
- pin
- test_agent_semantic_fallback_preserves_action_and_source_boundaries
- http.py
- _assert_no_canaries
- test_migrations.py
- FakeSession
- Layer 1: Presentation (React staff workspace)
- time
- check_architecture.py
- re
- test_phone_numbers_are_masked
- test_workspace_reports_only_complete_tenant_mapped_gas_configuration
- backup_restore_drill.py
- inventory/service.py
- bootstrap.py
- test_job_trace_exports_graph_and_model_runs_masked
- poll_once
- Layer 5: Core infrastructure
- pull_request_template.md
- Layer 7: External integrations
- LumaQuote by layer
- freeze_evaluation.py
- brain
- Cross-cutting layer: verification and tooling
- events
- WhatsApp channel (Meta Cloud API or Twilio Sandbox)
- running_job
- conn
- test_twilio_signature.py
- validate
- Persistent data, privileges and migration lifecycle
- strip_quoted
- sender_authenticated
- Apps Script transport and validated commercial snapshots
- scene-review.cjs
- vite.config.ts
- Frontend ownership, server state and interaction contracts
- Layer 6: Data (PostgreSQL and private Storage)
- test_unresolved_prior_day_call_still_consumes_daily_allowance
- Google Apps Script integration
- AdjustmentInput
- MailReceipt
- environment
- test_hostile_media_text_only_receives_fixed_clarification
- test_two_approvals_race_for_the_last_units_and_exactly_one_wins
- acceptance.py
- test_telegram.py
- Layer 3: Business features
- test_storage_outage_leaves_nothing_half_written_and_recovers
- test_runtime_media_is_deleted_after_seven_days_but_text_and_thread_remain
- scripts
- test_provider_failure_and_worker_logs_do_not_leak_canaries
- test_lighting_scene_review
- conn
- Showcase shot list (90-120 seconds)
- conn
- conn
- test_handshake_requires_the_exact_verify_token_and_full_configuration
- test_oversized_context_is_not_trimmed_into_positive_order
- docs_root
- test_holdout_is_refused_unless_frozen_unspent_and_confirmed

## God Nodes (most connected - your core abstractions)
1. `DomainError` - 171 edges
2. `October 29, 2026 - Offline embedding contract tests and engine recovery result` - 151 edges
3. `database()` - 116 edges
4. `post()` - 110 edges
5. `get_detail()` - 104 edges
6. `settings()` - 89 edges
7. `create_request()` - 86 edges
8. `audit()` - 62 edges
9. `make_draft()` - 61 edges
10. `react` - 58 edges

## Surprising Connections (you probably didn't know these)
- `Agent fallback and publication recheck` --references--> `ask()`  [INFERRED]
  docs/reference/CATALOG.md → app/agents/luma_agent/nodes/workflow.py
- `Open gaps` --references--> `prepare()`  [INFERRED]
  docs/reference/INVENTORY.md → app/agents/luma_agent/nodes/workflow.py
- `Command ownership` --references--> `prepare()`  [INFERRED]
  docs/reference/TOOLING_AND_TESTS.md → app/agents/luma_agent/nodes/workflow.py
- `Two-step approval confirmation` --references--> `review()`  [INFERRED]
  docs/reference/FRONTEND.md → app/agents/luma_agent/nodes/workflow.py
- `2026-11-01 - Unit policy gate passed; persisted-workflow regressions added` --references--> `review()`  [INFERRED]
  docs/WORK_LOG.md → app/agents/luma_agent/nodes/workflow.py

## Import Cycles
- None detected.

## Communities (233 total, 75 thin omitted)

### Community 0 - "psycopg"
Cohesion: 0.03
Nodes (40): run_review(), test_populated_tenant_restores_identically_with_checkpoints_and_objects(), available_port(), test_complete_native_browser_workflow(), wait_for_server(), test_duplicate_paid_operation_never_reserves_again(), test_retrieval_requires_settled_room_and_cannot_repeat(), pending() (+32 more)

### Community 1 - "telegram_client.py"
Cohesion: 0.12
Nodes (11): answer_callback(), call(), fetch_media(), get_updates(), make_client(), message_ref(), ready(), send_pdf() (+3 more)

### Community 2 - "test_semantic_catalog.py"
Cohesion: 0.08
Nodes (22): reserve(), index_company(), embedding_inputs(), has_current_embeddings(), publish_embeddings(), semantic_search(), vector_literal(), Estimated allowance lifecycle (+14 more)

### Community 3 - "October 29, 2026 - Offline embedding contract tests and engine recovery result"
Cohesion: 0.02
Nodes (119): 2026-10-29 - Agent fallback boundary tests added, 2026-10-29 - Agent fallback checks passed and evidence consolidated, 2026-10-29 - All Mermaid views rendered locally, 2026-10-29 - Configuration and verification reference coverage, 2026-10-29 — Current workflow documentation and screenshot reviewed, 2026-10-29 — Database gates passed; browser startup assertion failed, 2026-10-29 - Deep agent, media and retrieval references, 2026-10-29 - Deep backend and persistence documentation (+111 more)

### Community 4 - "test_stock_staff_routes.py"
Cohesion: 0.05
Nodes (34): arrange(), test_queue_dedupes_and_latest_reports_progress(), as_salesperson(), conn(), get(), level(), movements(), pending_order() (+26 more)

### Community 6 - "frontend/package.json"
Cohesion: 0.11
Nodes (24): devDependencies, jsdom@^29.1.1, openapi-typescript@^7.13.0, tailwindcss@^4.3.3, @testing-library/jest-dom@^6.9.1, @testing-library/react@^16.3.3, @types/node@^22.0.0, @types/react@^19.3.0 (+16 more)

### Community 7 - "test_whatsapp.py"
Cohesion: 0.14
Nodes (19): conversation_for(), deliver_webhook(), drain(), envelope(), rows(), start(), test_concurrent_duplicate_webhooks_and_workers_process_each_event_once(), test_hostile_media_metadata_is_refused_without_fetching_or_storing() (+11 more)

### Community 8 - "evaluation_dataset.py"
Cohesion: 0.05
Nodes (23): _check_outcome(), subtotal(), supported(), loaded(), test_counts_and_family_split_match_the_plan(), test_family_table_matches_the_bootstrap_catalog(), test_fingerprints_are_stable_hex_digests(), test_freeze_blocks_the_holdout_until_pinned_unchanged_and_unspent() (+15 more)

### Community 9 - "StrictModel"
Cohesion: 0.08
Nodes (13): StrictModel, cancel(), create(), purchase_orders(), receive(), _distinct(), PurchaseLineInput, PurchaseLineRow (+5 more)

### Community 10 - "make_draft"
Cohesion: 0.05
Nodes (28): exports(), poller(), Poller, test_changed_pdf_blocks_the_export_instead_of_shipping_different_bytes(), test_concurrent_pollers_cannot_claim_the_same_export(), test_failures_retry_then_block_and_expired_leases_are_reclaimed(), test_forged_stale_cross_company_and_replayed_envelopes_are_rejected(), test_receipt_needs_the_current_claim_token_and_identical_digest() (+20 more)

### Community 11 - "evaluate_scenarios.py"
Cohesion: 0.08
Nodes (15): evaluate(), main(), decide(), evaluate(), load_catalog(), main(), run_scenario(), summarize() (+7 more)

### Community 12 - "ResponseModel"
Cohesion: 0.09
Nodes (14): ResponseModel, AlertAck, AlertCounts, AlertRow, AlertsView, LevelView, MovementRow, MovementsPage (+6 more)

### Community 13 - "Button"
Cohesion: 0.09
Nodes (56): AdjustDialog(), AdjustForm(), AlertsTab(), PurchaseOrderRow, StockRow, useCancelPurchaseOrder(), CancelForm(), CancelOrderDialog() (+48 more)

### Community 14 - "AudioWaveform"
Cohesion: 0.08
Nodes (31): PhotoReading, AudioWaveform(), decodeAudioData(), computePeaks(), formatClock(), normalizePeaks(), Acceptance for the whole plan, Branch, pull request and merge (decision D39) (+23 more)

### Community 15 - "settings"
Cohesion: 0.11
Nodes (13): settings(), Settings, delete_files(), get_file(), put_file(), storage_headers(), ready(), ready() (+5 more)

### Community 16 - "ConversationThread.tsx"
Cohesion: 0.05
Nodes (56): AppShell(), navigation, ConversationCommand, useConversation(), useConversationAction(), ConversationComposer(), ConversationThread(), InboxPage() (+48 more)

### Community 17 - "test_twilio.py"
Cohesion: 0.09
Nodes (18): count_inbox(), inbound(), post_form(), receipt(), sid(), sign(), start(), test_approved_quotation_is_offered_as_the_exact_pdf_behind_a_signed_link() (+10 more)

### Community 18 - "clarification_for"
Cohesion: 0.13
Nodes (12): clarification_for(), Integration coverage by responsibility, 2026-11-02 - Negative (mutation-style) checks for hostile-content tests, extracted(), test_duplicate_sku_requires_clarification(), test_empty_placeholder_lines_do_not_suppress_candidate_discovery(), test_explicit_matching_text_confirms_media_fields(), test_media_alone_cannot_confirm_itself() (+4 more)

### Community 19 - "validate"
Cohesion: 0.07
Nodes (23): catalog_context(), is_yes(), known_skus(), model_input(), restatement(), safe_reply(), transcript(), unknown_reply() (+15 more)

### Community 20 - "Overview.tsx"
Cohesion: 0.08
Nodes (35): App(), InventoryPage, PendantField, SignIn(), NewRequest(), ConnectionHub, connections, ConnectionsPage() (+27 more)

### Community 21 - "DomainError"
Cohesion: 0.04
Nodes (56): _deliver_local(), recover_expired(), enqueue(), audit(), DomainError, accept_customer_text(), accept_quote_button(), change_ownership() (+48 more)

### Community 22 - "re"
Cohesion: 0.10
Nodes (13): degrade(), draw_label(), font(), main(), make_photo(), make_voice(), mix(), noise() (+5 more)

### Community 23 - "Development tooling, verification and evidence interpretation"
Cohesion: 0.20
Nodes (10): Browser scenario and screenshots, Command ownership, Development tooling, verification and evidence interpretation, Explicit provider canaries, Git workflow, Historical checkpoint and remaining gates, Isolated integration environment, Offline and full gates (+2 more)

### Community 24 - "scripts"
Cohesion: 0.06
Nodes (36): scripts, build, check:architecture, check:docs, check:frontend, check:rules, check:secrets, db:configure (+28 more)

### Community 25 - "ReceiptRequest"
Cohesion: 0.15
Nodes (5): ReceiptRequest, base_receipt(), test_media_hosts_must_be_meta_owned_https(), test_receipt_models_reject_incomplete_or_unsafe_outcomes(), test_valid_receipts_and_drive_filenames()

### Community 26 - "json"
Cohesion: 0.10
Nodes (10): digest(), main(), sender(), sync_state(), test_complete_snapshot_import_and_rejections(), send(), test_inventory_table_is_optional_ignored_and_outside_the_digest(), record_holdout_consumption() (+2 more)

### Community 27 - "FixtureInspector.tsx"
Cohesion: 0.07
Nodes (69): fadeTexture(), FixtureInspector(), InspectedProduct, InspectorModel(), nearestTemperature(), Part, TEMPERATURES, BELL (+61 more)

### Community 28 - "skills.py"
Cohesion: 0.12
Nodes (13): active_skills(), check_frontmatter(), check_links(), check_manifests(), check_mirror(), check_routing(), digest(), located() (+5 more)

### Community 29 - "test_stock_acceptance.py"
Cohesion: 0.03
Nodes (69): Work identities are deliberately different, Tests and evidence, callback(), customer_messages(), jobs(), notices(), one(), quote_status() (+61 more)

### Community 30 - "test_trace_masking.py"
Cohesion: 0.09
Nodes (8): State, test_business_content_is_kept(), test_disabled_tracing_exports_nothing(), test_media_bytes_and_inline_data_are_omitted(), test_model_call_exports_tokens_and_estimated_cost(), test_production_client_masks_every_exported_field(), test_set_usage_is_a_noop_without_a_run(), test_tracing_is_forced_off_outside_a_job_trace()

### Community 31 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.14
Nodes (12): Code layout, Commands, Documentation (decisions D30, D33), LumaQuote working rules, Rules, Skill routing, Unattended work and accounts, AI, evaluation and tracing (+4 more)

### Community 32 - "prepare"
Cohesion: 0.10
Nodes (21): build_graph(), route(), retrieve(), ask(), clarify(), review(), has_explicit_lines(), AgentState (+13 more)

### Community 33 - "index.cjs"
Cohesion: 0.10
Nodes (25): crypto, embeddedBlock(), existingFile(), fingerprint(), fs, hash(), path, readCatalog() (+17 more)

### Community 34 - "post"
Cohesion: 0.03
Nodes (47): early_in_minute(), first_denial(), test_approval_limit_is_10_per_minute(), test_catalog_search_limit_is_30_per_minute(), test_customer_messages_are_limited_per_conversation(), test_failed_requests_also_consume_admission(), test_queue_capacity_refuses_work_at_100_with_a_recoverable_503(), test_read_limit_is_120_per_minute() (+39 more)

### Community 35 - "inventory/api.ts"
Cohesion: 0.07
Nodes (56): AlertItem(), describe(), AlertRow, AlertsView, inventoryKeys, MovementRow, MovementsPage, OrderRow (+48 more)

### Community 36 - "io"
Cohesion: 0.10
Nodes (9): inspect_audio(), inspect_image(), inspect_pdf(), main(), process_file(), test_corrupt_files_are_rejected(), test_image_is_normalized_without_metadata(), test_native_pdf_retains_original_page_text() (+1 more)

### Community 37 - "steps"
Cohesion: 0.09
Nodes (21): VITE_SUPABASE_ANON_KEY, VITE_SUPABASE_URL, jobs, local-contracts, runs-on, steps, timeout-minutes, name (+13 more)

### Community 38 - "retention.py"
Cohesion: 0.17
Nodes (9): connect(), expired_media(), idle_conversations(), main(), purge_conversations(), purge_media(), purge_records(), run() (+1 more)

### Community 39 - "Design System: LumaQuote"
Cohesion: 0.10
Nodes (21): Buttons, Cards / Containers, Chips, Colors, Components, Design System: LumaQuote, Do:, Do's and Don'ts (+13 more)

### Community 40 - "lucide-react"
Cohesion: 0.08
Nodes (35): CatalogPage(), FixtureCanvas, FixtureInspector, FixtureView, MediaPreview(), load(), QuotationPanel(), QuotationsPage() (+27 more)

### Community 41 - "ref_node_path"
Cohesion: 0.09
Nodes (16): fs, path, root, { spawnSync }, fs, path, root, { spawnSync } (+8 more)

### Community 42 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, baseUrl, esModuleInterop, jsx, lib, module, moduleResolution (+10 more)

### Community 43 - "Stock, customer orders and supplier purchasing: implementation plan"
Cohesion: 0.13
Nodes (17): prepare(), raise_shortage_alert(), 10. Out of scope (not decided, not built), 11. Open gaps, 1. Problem, 2. Actors and authority, 3.1 Tables (one migration, task T1), 3.3 Readers that change (task T1) (+9 more)

### Community 44 - "estimated-allowance"
Cohesion: 0.10
Nodes (20): app/agents/luma_agent/budget.py, app/agents/luma_agent/nodes/retrieval.py, app/agents/luma_agent/runtime/media.py, app/agents/luma_agent/runtime/recovery.py, app/backend/luma/features/media/intake.py, app/backend/luma/features/media/persistence.py, estimated-allowance, media-lifecycle (+12 more)

### Community 45 - "quotation-approval"
Cohesion: 0.11
Nodes (19): app/agents/luma_agent/runtime/delivery.py, app/backend/luma/features/conversations/participation.py, app/backend/luma/features/quotations/approval.py, app/backend/luma/features/quotations/drafting.py, app/backend/luma/features/quotations/freshness.py, quotation-approval, sales-workflow, bindings (+11 more)

### Community 46 - "Test layers"
Cohesion: 0.11
Nodes (19): 10. Security, privacy, and abuse tests, 11. Concurrency, fault injection, and recovery tests, 12. Performance, accessibility, and visual acceptance, 1. Static and build checks, 2. Unit tests, 3. Property and state-machine tests, 4. Frontend component tests, 5. API and provider contract tests (+11 more)

### Community 47 - "test_approved_quotation_is_sent_as_the_exact_canonical_pdf"
Cohesion: 0.12
Nodes (6): graph(), Graph, test_approved_quotation_is_sent_as_the_exact_canonical_pdf(), test_gates_block_without_calling_meta(), test_text_reply_is_submitted_once_with_the_provider_id_recorded(), test_uncertain_and_failed_submissions_are_recorded_and_never_retried()

### Community 48 - "ledger.py"
Cohesion: 0.14
Nodes (11): apply_movement(), convert_quote(), ensure_level(), _held(), _ids(), _line_quantities(), lock_levels(), _move() (+3 more)

### Community 49 - "LumaQuote implementation tracker"
Cohesion: 0.10
Nodes (20): 1. Design and foundations, 2. Manual quotation workflow, 3. Persistent agent and media, 4. Live Google and WhatsApp, 5. Visual finish and safeguards, 6. Frozen evaluation and showcase, 7. Stock, customer orders and purchasing (D49, [plan](proposals/2026-11-07-stock-orders-plan.md)), Decisions recorded 2026-11-02 (+12 more)

### Community 50 - "components.json"
Cohesion: 0.12
Nodes (16): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+8 more)

### Community 52 - "Work log"
Cohesion: 0.12
Nodes (17): October 29, 2026 - Agent semantic fallback wiring, October 29, 2026 - Application documentation reconciliation, October 29, 2026 - Chat documentation reconciliation, October 29, 2026 - Documentation reconciliation validation, October 29, 2026 - Documentation workflow rule, October 29, 2026 - Fixed embedding adapter and explicit index command, October 29, 2026 - Local engine availability diagnosis, October 29, 2026 - Photo browser fixture and attempted verification (+9 more)

### Community 53 - "main"
Cohesion: 0.20
Nodes (8): check_encoding(), check_evidence(), check_links(), check_plan(), documentation_files(), evidence_header(), main(), relative()

### Community 54 - "useLiveUpdates.ts"
Cohesion: 0.13
Nodes (15): followStream(), reconnectDelay(), encoder, MockStream, renderLive(), signOut, wait(), ApiError (+7 more)

### Community 55 - "whatsapp_client.py"
Cohesion: 0.10
Nodes (16): fetch_media(), call(), download(), endpoint(), fetch_media(), GraphError, headers(), make_client() (+8 more)

### Community 56 - "rate_limit"
Cohesion: 0.14
Nodes (14): rate_limit(), membership(), acknowledge(), adjustments(), alerts(), export_xlsx(), latest_sheet_export(), movements() (+6 more)

### Community 57 - "check_frontend.cjs"
Cohesion: 0.17
Nodes (13): What is stored, Identity and evidence records, definitionName(), fs, inspect(), walk(), main(), visit() (+5 more)

### Community 58 - "operation"
Cohesion: 0.13
Nodes (7): operation(), cancel(), confirm(), orders(), CancelInput, decision(), draft()

### Community 59 - "package.json"
Cohesion: 0.16
Nodes (15): devDependencies, @google/clasp@3.4.1, mermaid@11.17.2, supabase@2.122.0, typescript@5.9.3, typescript, name, overrides (+7 more)

### Community 60 - "twilio_webhook.py"
Cohesion: 0.12
Nodes (13): addressed_to_us(), configured(), expected_signature(), first(), message_event(), receive_message(), receive_status(), status_event() (+5 more)

### Community 61 - "manual-workflow.cjs"
Cohesion: 0.25
Nodes (10): beat(), { chromium, expect }, dispatchFixture(), fs, main(), path, PRIVATE, processMediaFixture() (+2 more)

### Community 62 - "deliver_one"
Cohesion: 0.07
Nodes (20): deliver_one(), allowed(), allowed_email_senders(), allowed_senders(), allowed_telegram_users(), answer_buttons(), begin(), submit() (+12 more)

### Community 63 - "vitest"
Cohesion: 0.14
Nodes (18): request, base, request, request, request, purchase, request, order (+10 more)

### Community 64 - "job-recovery"
Cohesion: 0.12
Nodes (17): app/agents/luma_agent/lease.py, app/agents/luma_agent/runtime/jobs.py, app/backend/luma/features/messaging/inbound.py, job-recovery, worker-tick, bindings, height, renderer_sha256 (+9 more)

### Community 65 - "bindings"
Cohesion: 0.10
Nodes (20): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/agents/luma_agent/graph.py, app/agents/luma_agent/nodes/extraction.py (+12 more)

### Community 66 - "whatsapp-channel"
Cohesion: 0.10
Nodes (21): app/agents/luma_agent/observability.py, app/backend/luma/core/config.py, app/backend/luma/features/google_sync/routes.py, app/backend/luma/features/messaging/outbound.py, app/backend/luma/features/messaging/webhook.py, app/backend/luma/features/messaging/whatsapp_client.py, supabase/migrations/20261102010000_whatsapp_inbox.sql, integrations-map (+13 more)

### Community 67 - "LumaQuote"
Cohesion: 0.17
Nodes (11): Accessibility & Inclusion, Brand Commitments, Capabilities and Constraints, Evidence on Hand, LumaQuote, Operating Context, Platform, Product Principles (+3 more)

### Community 68 - "start-local-supabase.cjs"
Cohesion: 0.18
Nodes (10): api(), databaseClients, { execFileSync, spawnSync }, fs, http, names, path, privateDir (+2 more)

### Community 70 - "catalog-retrieval"
Cohesion: 0.18
Nodes (11): app/agents/luma_agent/nodes/workflow.py, app/backend/luma/features/catalog/criteria.py, app/backend/luma/features/catalog/retrieval.py, app/backend/luma/features/catalog/semantic.py, bindings, height, renderer_sha256, source_sha256 (+3 more)

### Community 71 - "Email channel (Gmail through Apps Script)"
Cohesion: 0.18
Nodes (11): Actors and authority, Configuration (names only), Email channel (Gmail through Apps Script), External effects and secrets, Failures and recovery, How threads are found (fix of 2026-11-11), Idempotency, Limits and cost (+3 more)

### Community 72 - "diagrams"
Cohesion: 0.12
Nodes (15): height, renderer_sha256, source_sha256, svg_sha256, width, diagrams, api-pipeline, layer-map (+7 more)

### Community 73 - "google-snapshot"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/google_sync/callbacks.py, app/backend/luma/features/google_sync/snapshots.py, app/backend/luma/features/google_sync/validation.py, gas/Synchronization.gs, google-snapshot, bindings, height, renderer_sha256 (+3 more)

### Community 74 - "drive-export"
Cohesion: 0.09
Nodes (23): app/backend/luma/features/google_sync/exports.py, app/backend/luma/features/google_sync/stock_exports.py, app/backend/luma/features/inventory/exports.py, app/backend/luma/features/inventory/sheet_queue.py, app/backend/luma/features/quotations/documents.py, gas/Exports.gs, gas/Stock.gs, supabase/migrations/20261102000000_drive_exports.sql (+15 more)

### Community 75 - "workflow-data"
Cohesion: 0.08
Nodes (26): supabase/migrations/20261029010000_quotation_domain.sql, supabase/migrations/20261029100000_immutable_quotation_content.sql, supabase/migrations/20261029110000_voice_intake.sql, supabase/migrations/20261029111000_media_message_binding.sql, supabase/migrations/20261029131000_versioned_embeddings.sql, bindings, height, renderer_sha256 (+18 more)

### Community 76 - "bindings"
Cohesion: 0.09
Nodes (24): bindings, app/backend/luma/core/admission.py, app/backend/luma/core/database.py, app/backend/luma/core/errors.py, app/backend/luma/core/http.py, app/backend/luma/core/idempotency.py, app/backend/luma/core/identity.py, app/backend/luma/features/conversations/routes.py (+16 more)

### Community 77 - "dependencies"
Cohesion: 0.08
Nodes (25): dependencies, class-variance-authority@^0.7.1, clsx@^2.1.1, cn@^0.4.0, @fontsource/ibm-plex-sans@^5.3.0, @fontsource-variable/space-grotesk@^5.3.0, lucide-react@^1.63.0, radix-ui@^1.8.1 (+17 more)

### Community 78 - "backend-modules"
Cohesion: 0.11
Nodes (21): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/agents/luma_agent/worker.py, app/backend/luma/features/media/sandbox.py (+13 more)

### Community 79 - "frontend-draft"
Cohesion: 0.10
Nodes (21): app/frontend/src/app/App.tsx, app/frontend/src/features/conversations/api.ts, app/frontend/src/features/quotations/QuotationPanel.tsx, app/frontend/src/features/quotations/useQuotationDraft.ts, app/frontend/src/main.tsx, app/frontend/src/shared/api/client.ts, app/frontend/vite.config.ts, frontend-draft (+13 more)

### Community 80 - "verification-scope"
Cohesion: 0.11
Nodes (19): .github/workflows/ci.yml, package.json, scripts/verify.cjs, tests/integration/test_browser_workflow.py, tests/integration/test_ui_review.py, verification-scope, verify-gate, bindings (+11 more)

### Community 81 - "ui-review.cjs"
Cohesion: 0.26
Nodes (12): { chromium }, fs, keyboardPass(), livePass(), main(), measure(), PRIVATE, reviewView() (+4 more)

### Community 82 - "purchasing/service.py"
Cohesion: 0.14
Nodes (9): require_admin(), next_number(), create_order(), cancel(), create(), list_orders(), _lock(), order_rows() (+1 more)

### Community 83 - "authorization.py"
Cohesion: 0.08
Nodes (15): held_quantities(), authorize_outbound(), check_quotation(), check_snapshot(), assert_dispatchable(), calculate(), Drafting an immutable offer, Actors and authority (+7 more)

### Community 84 - "Local Supabase"
Cohesion: 0.22
Nodes (9): Conflicts, unavailable infrastructure and evidence, Credentials and application configuration, Local Supabase, Media and worker diagnosis, Native processes and optional provider work, Schema, Semantic index command under development, Services (+1 more)

### Community 85 - "media/routes.py"
Cohesion: 0.10
Nodes (10): accept_audio(), accept_media(), authorize_upload(), admit_upload(), audio_playback(), image_preview(), persist_upload(), receive_upload() (+2 more)

### Community 86 - "test_controlled_provider_cannot_invent_customer_confirmation"
Cohesion: 0.33
Nodes (4): test_controlled_provider_cannot_invent_customer_confirmation(), client_fixture(), parse_fixture(), test_unsupported_latest_intent_pauses_then_complete_restatement_resumes()

### Community 87 - "Morning actions"
Cohesion: 0.11
Nodes (18): Decision needed: Apps Script lock contention (seen live 2026-11-11), Decision needed: failed requests are not rate limited, Evidence limits, Gmail requests (D47), Google callback preparation, Google Workspace / clasp, LangSmith account limit, Latest verification (+10 more)

### Community 88 - "LumaQuote"
Cohesion: 0.25
Nodes (8): Documentation, LumaQuote, LumaQuote request-to-reviewed-offer workflow, Run locally, Status and next actions, Structure, Verification, Workflow at a glance

### Community 89 - "Configuration and native process operation"
Cohesion: 0.22
Nodes (9): Auth succeeds but the workspace request fails, Configuration and native process operation, Local sign-in fails while Windows reserves the Supabase ports, Messaging and Google configuration, Paid AI policy, Private generated files and reproducibility, Safe routine operation, Supabase and database identities (+1 more)

### Community 90 - "page-review.cjs"
Cohesion: 0.25
Nodes (8): @axe-core/playwright@^4.13.0, @axe-core/playwright, { chromium }, fs, main(), ROUTES, signIn(), VIEWPORTS

### Community 91 - "workflow.py"
Cohesion: 0.08
Nodes (17): assert_job(), assert_request_version(), query_constraints(), SearchCriteria, candidate_question(), search_catalog(), search(), source_pdf() (+9 more)

### Community 92 - "LumaQuote architecture"
Cohesion: 0.40
Nodes (5): Agent participation and recovery limits, Code ownership, LumaQuote architecture, Processes and trust boundaries, Semantic retrieval work in progress

### Community 93 - "database.py"
Cohesion: 0.03
Nodes (48): embed_texts(), validate_embedding_provider(), MediaReading, _read_label(), read_media(), validate_media_provider(), configured_secrets(), finish() (+40 more)

### Community 94 - "appsscript.json"
Cohesion: 0.33
Nodes (5): dependencies, exceptionLogging, oauthScopes, runtimeVersion, timeZone

### Community 95 - "inventory/exports.py"
Cohesion: 0.05
Nodes (23): build_workbook(), collect(), export_filename(), ExportTable, _movement_rows(), _order_rows(), _purchase_rows(), safe_text() (+15 more)

### Community 96 - "frontend-live-updates"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/workspace/routes.py, app/frontend/src/features/workspace/api.ts, app/frontend/src/features/workspace/useLiveUpdates.ts, app/frontend/src/shared/api/events.ts, frontend-live-updates, bindings, height, renderer_sha256 (+3 more)

### Community 97 - "Sales and agent workflows"
Cohesion: 0.40
Nodes (5): Agent requests and evidence, Manual quotation, Notes, human replies and takeover, Sales and agent workflows, Voice and product-label photos

### Community 98 - "test_acceptance_phrases.py"
Cohesion: 0.15
Nodes (7): test_a_bare_courtesy_word_does_not_change_the_answer(), test_a_mobile_signature_is_cut_from_an_email_reply(), test_accept_phrases(), test_courtesy_never_turns_other_text_into_an_answer(), test_decline_phrases(), test_everything_else_is_ordinary_text(), test_non_text_is_not_an_answer()

### Community 99 - "guard.py"
Cohesion: 0.14
Nodes (12): `bash` (PreToolUse on Bash, R15), Claude Code hooks, `edit` (PostToolUse on Edit and Write, R6), `stop` (Stop, R14 and R8-R10), bash(), block(), changed_paths(), edit() (+4 more)

### Community 100 - "Backend contracts and business transactions"
Cohesion: 0.12
Nodes (15): Binary attachment protocol, Command payloads and a review sequence, Errors and limits, Identity and mutation protocol, Regenerating contracts, Staff API reference, Staff identity, idempotency and optimistic mutation protocol, Stock, order and purchase-order endpoints (decision D49, task T4) (+7 more)

### Community 101 - "order-lifecycle"
Cohesion: 0.10
Nodes (21): app/backend/luma/features/inventory/ledger.py, app/backend/luma/features/orders/acceptance.py, app/backend/luma/features/orders/management.py, app/backend/luma/features/orders/service.py, app/backend/luma/features/purchasing/routes.py, app/backend/luma/features/purchasing/service.py, supabase/migrations/20261107030000_stock_ledger.sql, order-lifecycle (+13 more)

### Community 102 - "Visual guide to LumaQuote"
Cohesion: 0.40
Nodes (5): Data and runtime, Layer views, Maintaining a view, Visual guide to LumaQuote, Workflow and architecture

### Community 103 - "Project documentation"
Cohesion: 0.50
Nodes (4): Current verification boundaries, Detailed implementation references, Documentation coverage and update ownership, Project documentation

### Community 104 - "uuid"
Cohesion: 0.04
Nodes (27): EditHint, verify_hint(), verify_mapping(), verify_signature(), InputRecord, PolicyInput, PriceInput, ProductInput (+19 more)

### Community 105 - "rule-enforcement"
Cohesion: 0.17
Nodes (12): .claude/settings.json, scripts/check_docs.py, scripts/hooks/guard.py, scripts/skills.py, scripts/summarize_agent_run.py, rule-enforcement, bindings, height (+4 more)

### Community 106 - "test_embedding_contracts.py"
Cohesion: 0.15
Nodes (6): test_embedding_response_indices_bind_each_vector_to_its_requested_record(), create(), test_invalid_provider_vectors_fail_closed(), test_shared_filters_refuse_ambiguous_or_negated_requirements(), test_valid_vector_has_only_finite_numeric_json(), unit_vector()

### Community 108 - "Verified OpenAI contracts"
Cohesion: 0.67
Nodes (3): Embedding adapter under development, Photo label-reading contract, Verified OpenAI contracts

### Community 109 - "IMPLEMENTATION_PLAN.md"
Cohesion: 0.25
Nodes (3): Direction contract, Sales workspace direction, Synthetic development confirmation cases

### Community 110 - "run"
Cohesion: 0.14
Nodes (12): 2026-11-07 - Stock ledger tables and single writer (phase 7, local), reply_texts(), run(), start(), test_free_wording_is_restated_then_yes_prepares_review(), test_model_reads_conversation_and_catalog_without_prices(), test_unknown_sku_is_not_restated_and_yes_then_asks_the_model(), test_unsafe_model_reply_is_replaced_by_the_fixed_question() (+4 more)

### Community 111 - "scripts"
Cohesion: 0.08
Nodes (27): 1. What went wrong so far (evidence from the work log and this session), 2. Principles, 3. The rulebook (replaces most of AGENTS.md + CLAUDE.md prose), 4.1 Make skills discoverable, 4.2 Consolidate 37 -> about 20 skills, 4.3 One routing table, 4. Skill routing, 5. Documentation: one home per fact (+19 more)

### Community 114 - "test_agent_rules.py"
Cohesion: 0.13
Nodes (8): test_r10_ticked_items_need_evidence_and_phase_4_needs_live(), test_r14_stop_requires_work_log_and_docs_for_code(), test_r15_bash_guard(), test_r6_edit_guard_warns_on_large_deletions(), test_r8_flags_mojibake_crlf_and_broken_links_but_not_quoted_code(), test_r9_requires_header_and_allowed_label_for_new_evidence(), test_skills_frontmatter_and_routing(), write()

### Community 115 - "inventory/queries.py"
Cohesion: 0.17
Nodes (7): low_stock_count(), low_stock_rows(), movements_page(), open_alerts(), stock_rows(), alerts(), How the rest of the application reads stock

### Community 116 - "health"
Cohesion: 0.18
Nodes (11): Evaluation scoring pin (R11), Failure and recovery, Knowledge graph (decision D33), npm checks, Overview, Rule-to-enforcement map, `scripts/check_docs.py` details, `scripts/skills.py` details (+3 more)

### Community 117 - "scan_secrets.py"
Cohesion: 0.13
Nodes (9): load_secrets(), main(), run(), scan_files(), tracked_files(), make_repo(), test_clean_repo_reports_no_leaks(), test_only_secret_looking_long_nonpublic_values_are_loaded() (+1 more)

### Community 118 - "database"
Cohesion: 0.04
Nodes (40): database(), accept_hint(), claim_export(), ClaimRequest, drive_filename(), ExportEnvelope, record_nonce(), record_receipt() (+32 more)

### Community 119 - "test_stock_ledger.py"
Cohesion: 0.06
Nodes (33): reconcile(), block(), refusal_reason(), 3.2 Single writer, 3.4 Freshness at approval and dispatch (task T2), 9. Task list (one Sonnet subagent each, sequential, one commit per task), Approval, freshness and dispatch, Customer acceptance and orders (task T3) (+25 more)

### Community 123 - "test_brain.py"
Cohesion: 0.13
Nodes (8): make(), test_anything_more_than_agreement_is_not_yes(), test_plain_agreement_is_yes(), test_plain_reply_passes_trimmed(), test_restatement_is_built_from_pairs_only(), test_unsafe_or_empty_replies_are_dropped(), test_unusable_model_orders_are_rejected(), test_valid_lines_normalize_case()

### Community 127 - "reduce_mail"
Cohesion: 0.19
Nodes (5): MailItem, item(), test_empty_body_uses_subject_and_attachments_only_is_unsupported(), test_reduce_builds_an_email_event(), test_unparseable_sender_is_skipped()

### Community 128 - "settings"
Cohesion: 0.08
Nodes (16): send_pdf(), send_text(), ProviderError, quotation_url(), account_base(), auth(), call(), create_message() (+8 more)

### Community 144 - "message"
Cohesion: 0.19
Nodes (9): customer_reply(), execute(), detail(), intake(), message(), execute(), ownership(), execute() (+1 more)

### Community 145 - "Telegram channel (Bot API, long polling)"
Cohesion: 0.13
Nodes (16): acknowledge_button(), clear_buttons(), message_id(), Actors and authority, Configuration (names only), Failures and recovery, Idempotency, Inputs and outputs (+8 more)

### Community 147 - "test_surface_inventory.py"
Cohesion: 0.24
Nodes (4): operations(), test_gateway_exposes_only_signed_receivers_and_no_documentation_or_staff_route(), test_staff_api_directly_mounted_paths_are_health_and_documentation_only(), test_staff_api_surface_is_the_reviewed_inventory_and_only_health_is_open()

### Community 148 - "pin"
Cohesion: 0.22
Nodes (5): pin(), run_summarizer(), test_changed_or_missing_pin_is_refused_without_post_hoc(), test_matching_pin_is_scored_normally(), test_post_hoc_flag_labels_the_report()

### Community 150 - "http.py"
Cohesion: 0.09
Nodes (14): auth_client(), dependency_unavailable(), domain_error(), response_boundaries(), staff(), health(), Layer 2: Transport (staff API and signed gateway), Open gaps (+6 more)

### Community 151 - "_assert_no_canaries"
Cohesion: 0.19
Nodes (7): _assert_no_canaries(), _job(), test_exception_text_and_error_field_are_masked(), test_metadata_tags_and_job_payload_are_masked(), test_nested_tool_and_subgraph_runs_are_masked(), inner(), lookup_tool()

### Community 152 - "test_migrations.py"
Cohesion: 0.15
Nodes (8): Data model, apply(), scratch(), shape(), test_all_migrations_apply_cleanly_and_match_the_live_schema(), test_stock_ledger_backfills_every_product_then_drops_available(), test_stock_tables_are_protected_and_the_ledger_is_append_only(), test_upgrade_keeps_pending_work()

### Community 154 - "Layer 1: Presentation (React staff workspace)"
Cohesion: 0.33
Nodes (6): Changes on 2026-11-03, Extending safely, Layer 1: Presentation (React staff workspace), Open gaps, Routes, Tests and evidence

### Community 155 - "time"
Cohesion: 0.07
Nodes (12): test_auth_outage_is_a_safe_503_not_an_open_door(), test_cors_allows_only_the_exact_local_origins(), test_declared_oversize_and_malformed_length_are_rejected_before_routing(), test_every_response_is_private_nosniff_and_unframed(), test_gateway_never_exposes_staff_routes_or_documentation(), test_missing_or_invalid_credentials_never_reach_business_code(), test_mutation_rate_limit_rejects_the_thirty_first_request_with_retry_guidance(), test_signed_callback_receipts() (+4 more)

### Community 157 - "re"
Cohesion: 0.07
Nodes (15): key(), load_pdf(), quotation_pdf(), signature(), configured(), extract_events(), handshake(), message_event() (+7 more)

### Community 160 - "backup_restore_drill.py"
Cohesion: 0.16
Nodes (7): docker(), main(), object_paths(), prepare_scratch(), run(), snapshot(), source_params()

### Community 161 - "inventory/service.py"
Cohesion: 0.17
Nodes (6): adjust(), level_view(), movements(), parse_cursor(), set_reorder_level(), stock_view()

### Community 162 - "bootstrap.py"
Cohesion: 0.20
Nodes (6): DraftInput, Selection, main(), stable(), test_concurrent_edits_allow_only_one_observed_version(), save()

### Community 164 - "poll_once"
Cohesion: 0.21
Nodes (6): poll_telegram(), largest_photo(), poll_once(), reduce_callback(), reduce_update(), Modules and call flow

### Community 165 - "Layer 5: Core infrastructure"
Cohesion: 0.33
Nodes (6): Admission, Changes on 2026-11-03, Extending safely, Idempotency, Layer 5: Core infrastructure, Open gaps

### Community 166 - "pull_request_template.md"
Cohesion: 0.40
Nodes (4): Changes, Problem, Risks and open items, Validation

### Community 167 - "Layer 7: External integrations"
Cohesion: 0.33
Nodes (6): Changes on 2026-11-03, Extending safely, Gates and proof, Layer 7: External integrations, Open gaps, Shared rules

### Community 168 - "LumaQuote by layer"
Cohesion: 0.33
Nodes (6): Keeping these guides current, Layer map, LumaQuote by layer, One request through every layer, Other views, The layers

### Community 169 - "freeze_evaluation.py"
Cohesion: 0.19
Nodes (6): freeze_fingerprints(), freeze_problems(), load_freeze(), check(), main(), write()

### Community 171 - "Cross-cutting layer: verification and tooling"
Cohesion: 0.40
Nodes (5): Changes on 2026-11-03, Cross-cutting layer: verification and tooling, Open gaps, Test families by layer, The verify gate

### Community 172 - "events"
Cohesion: 0.25
Nodes (4): events(), stream(), inspect(), workspace()

### Community 173 - "WhatsApp channel (Meta Cloud API or Twilio Sandbox)"
Cohesion: 0.33
Nodes (6): Configuration (names only), Data, Failure and recovery, Proof and limits, WhatsApp channel (Meta Cloud API or Twilio Sandbox), WhatsApp webhook ingress and gated egress

### Community 174 - "running_job"
Cohesion: 0.15
Nodes (6): test_live_structured_extraction_prepares_only_review(), running_job(), test_older_preparation_preserves_staff_revision(), test_stale_extraction_cannot_ask_or_replace_draft(), read_trace(), test_live_job_trace_is_detailed_and_masked()

### Community 186 - "test_twilio_signature.py"
Cohesion: 0.15
Nodes (5): test_media_link_binds_outbox_id_and_expires(), test_media_link_refuses_without_a_token(), test_signature_matches_twilio_python_vector(), test_url_variants_add_or_remove_the_default_port(), token()

### Community 187 - "validate"
Cohesion: 0.17
Nodes (7): Unit and component coverage, 2026-11-03 - Pre-freeze Recall@5 relabel: 7 to 14 retrieval cases (phase 6, local), catalog_model(), _check_retrieval(), _check_structure(), _check_turns(), validate()

### Community 188 - "Persistent data, privileges and migration lifecycle"
Cohesion: 0.18
Nodes (11): Catalog, commercial snapshot and current embedding relationships, Checkpoints, retention and preservation, Conversation and quotation records, Conversation, offer, approval, media and work relationships, Exact conversation and attachment binding, Google synchronization records, Migration sequence and local application, Persistent data, privileges and migration lifecycle (+3 more)

### Community 189 - "strip_quoted"
Cohesion: 0.25
Nodes (5): strip_quoted(), Inputs and outputs, 2026-11-11 - Courtesy words and mobile signatures in accept replies (phase 7, local), test_a_signature_line_only_cuts_when_it_is_the_whole_line(), test_an_email_reply_with_quoted_history_reduces_to_the_phrase()

### Community 190 - "sender_authenticated"
Cohesion: 0.15
Nodes (7): sender_authenticated(), Sender authentication, test_anything_else_is_unauthenticated(), test_each_passing_mechanism_counts(), test_gmail_pass_authenticates_the_from_domain(), test_quoted_history_is_removed(), test_sender_address()

### Community 191 - "Apps Script transport and validated commercial snapshots"
Cohesion: 0.18
Nodes (11): Apps Script transport and validated commercial snapshots, Atomic publication and offer freshness, Authority and process boundary, Diagnosis without leaking integration data, Drive export of approved quotations, Envelope authentication and replay, GAS source responsibilities, Invalidation hint versus full snapshot (+3 more)

### Community 192 - "scene-review.cjs"
Cohesion: 0.28
Nodes (8): @playwright/test@^1.64.1, @playwright/test, axeViolations(), { chromium }, fs, main(), PRIVATE, signIn()

### Community 193 - "vite.config.ts"
Cohesion: 0.25
Nodes (6): @tailwindcss/vite@^4.3.3, vite@^8.3.5, @vitejs/plugin-react@^6.1.2, @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 194 - "Frontend ownership, server state and interaction contracts"
Cohesion: 0.25
Nodes (8): Authored, generated and vendor-owned source, Frontend ownership, server state and interaction contracts, Live updates over an authenticated event stream, Mutations and canonical reconciliation, Quotation editing and conflict preservation, Two-step approval confirmation, Unsaved quotation edits survive polling and conflicts, Whole-app review and its limits

### Community 204 - "Layer 6: Data (PostgreSQL and private Storage)"
Cohesion: 0.29
Nodes (7): Changes on 2026-11-03, Extending safely, Layer 6: Data (PostgreSQL and private Storage), Migrations, Open gaps, Retention and recovery, Who may reach what

### Community 206 - "Google Apps Script integration"
Cohesion: 0.25
Nodes (8): Account setup, Backend contracts and persistence, Evidence limits, Gmail channel (D47), Google Apps Script integration, Local receiver, Source responsibilities, Troubleshooting and verification

### Community 209 - "environment"
Cohesion: 0.20
Nodes (4): seed_opening(), Operation, environment(), TestEnvironment

### Community 211 - "test_two_approvals_race_for_the_last_units_and_exactly_one_wins"
Cohesion: 0.50
Nodes (3): Decision, test_two_approvals_race_for_the_last_units_and_exactly_one_wins(), run()

### Community 213 - "test_telegram.py"
Cohesion: 0.09
Nodes (19): External effects and secrets, Bot, bot(), start(), telegram_conversation(), test_allowlisted_user_opens_a_telegram_conversation_and_others_are_ignored(), test_approved_quotation_is_uploaded_as_the_exact_canonical_pdf(), test_bot_token_never_reaches_logs() (+11 more)

### Community 214 - "Layer 3: Business features"
Cohesion: 0.29
Nodes (7): Changes on 2026-11-03, Extending safely, Features, Layer 3: Business features, Open gaps, Rules every feature follows, Tests and evidence

### Community 216 - "test_runtime_media_is_deleted_after_seven_days_but_text_and_thread_remain"
Cohesion: 0.33
Nodes (3): age(), one(), test_runtime_media_is_deleted_after_seven_days_but_text_and_thread_remain()

### Community 217 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, test, typecheck

### Community 222 - "Showcase shot list (90-120 seconds)"
Cohesion: 0.67
Nodes (3): Not shown (do not demonstrate or claim), Reproducible evidence behind each claim, Showcase shot list (90-120 seconds)

## Knowledge Gaps
- **1 isolated node(s):** `lumaquote`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2259 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **75 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DomainError` connect `DomainError` to `psycopg`, `test_semantic_catalog.py`, `October 29, 2026 - Offline embedding contract tests and engine recovery result`, `decimal`, `validate`, `http.py`, `json`, `re`, `test_stock_acceptance.py`, `prepare`, `inventory/service.py`, `post`, `bootstrap.py`, `io`, `Stock, customer orders and supplier purchasing: implementation plan`, `events`, `running_job`, `ledger.py`, `rate_limit`, `operation`, `test_twilio_signature.py`, `twilio_webhook.py`, `deliver_one`, `purchasing/service.py`, `authorization.py`, `test_two_approvals_race_for_the_last_units_and_exactly_one_wins`, `media/routes.py`, `workflow.py`, `database.py`, `uuid`, `test_embedding_contracts.py`, `database`, `test_stock_ledger.py`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 63 inferred relationships involving `DomainError` (e.g. with `embed_texts()` and `validate_embedding_provider()`) actually correct?**
  _`DomainError` has 63 INFERRED edges - model-reasoned connections that need verification._
- **What connects `lumaquote` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `psycopg` be split into smaller, more focused modules?**
  _Cohesion score 0.03394340079013142 - nodes in this community are weakly interconnected._
- **Why does `audit()` connect `DomainError` to `inventory/service.py`, `test_semantic_catalog.py`, `test_job_trace_exports_graph_and_model_runs_masked`, `AudioWaveform`, `ledger.py`, `ConversationThread.tsx`, `purchasing/service.py`, `test_stock_acceptance.py`, `database`, `test_stock_ledger.py`, `rate_limit`, `check_frontend.cjs`, `database.py`, `deliver_one`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Should `telegram_client.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12333333333333334 - nodes in this community are weakly interconnected._
- **Why does `Inventory page, order banner and stock card` connect `inventory/api.ts` to `Frontend ownership, server state and interaction contracts`, `lucide-react`, `Button`, `ConversationThread.tsx`, `DomainError`, `test_stock_acceptance.py`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._