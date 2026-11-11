# Graph Report - Demo_Project_4  (2026-11-11)

## Corpus Check
- 439 files · ~380,484 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 55 file(s) not represented in the graph (top: .mmd 31, .css 10, .gs 7)

## Summary
- 4503 nodes · 11044 edges · 226 communities (156 shown, 70 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 821 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cc64b88c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- psycopg
- ProviderError
- test_semantic_catalog.py
- October 29, 2026 - Offline embedding contract tests and engine recovery result
- conn
- decimal
- frontend/package.json
- test_whatsapp.py
- evaluation_dataset.py
- StrictModel
- make_draft
- evaluate_scenarios.py
- cn
- react
- AudioWaveform
- bootstrap.py
- Button
- test_twilio.py
- clarification_for
- validate
- Overview.tsx
- conversation
- re
- pathlib
- scripts
- ReceiptRequest
- workspace/schemas.py
- glowTexture
- skills.py
- test_stock_acceptance.py
- test_trace_masking.py
- Proposal: working rules, skill routing and documentation (draft for approval)
- prepare
- index.cjs
- post
- inventory/api.ts
- processor.py
- steps
- retention.py
- Design System: LumaQuote
- useQuotationDraft
- ref_node_path
- compilerOptions
- Stock, customer orders and supplier purchasing: implementation plan
- estimated-allowance
- quotation-approval
- Test layers
- deliver_one
- DomainError
- LumaQuote implementation tracker
- components.json
- Work log
- main
- AppShell.tsx
- whatsapp_client.py
- database
- Persistent data, privileges and migration lifecycle
- .claim
- package.json
- webhook.py
- manual-workflow.cjs
- outbound.py
- vitest
- job-recovery
- bindings
- whatsapp-channel
- LumaQuote
- start-local-supabase.cjs
- ExportEnvelope
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
- test_approved_quotation_is_claimed_with_the_exact_canonical_pdf
- authorization.py
- Local Supabase
- upload_audio
- worker.py
- Morning actions
- LumaQuote
- Configuration and native process operation
- page-review.cjs
- CatalogSearch
- LumaQuote architecture
- media.py
- appsscript.json
- inventory/exports.py
- frontend-live-updates
- Sales and agent workflows
- test_acceptance_phrases.py
- test_every_response_is_private_nosniff_and_unframed
- staff
- order-lifecycle
- Visual guide to LumaQuote
- Project documentation
- hashlib
- rule-enforcement
- test_embedding_contracts.py
- CLAUDE.md
- Verified OpenAI contracts
- IMPLEMENTATION_PLAN.md
- run
- scripts
- Graph
- inventory/queries.py
- health
- subprocess
- google_sync/routes.py
- email_dispatch.py
- test_brain.py
- reduce_mail
- settings
- lumaquote
- CatalogHit
- claim_stock_export
- process_next
- test_surface_inventory.py
- pin
- test_agent_semantic_fallback_preserves_action_and_source_boundaries
- dependency_unavailable
- _assert_no_canaries
- test_migrations.py
- FakeSession
- FRONTEND.md
- test_agent_on_development_scenario
- check_architecture.py
- allowlist.py
- test_phone_numbers_are_masked
- test_workspace_reports_only_complete_tenant_mapped_gas_configuration
- safe_text
- io
- State
- test_job_trace_exports_graph_and_model_runs_masked
- test_safe_text.py
- Layer 5: Core infrastructure
- pull_request_template.md
- Layer 7: External integrations
- LumaQuote by layer
- sceneKit.ts
- brain
- Cross-cutting layer: verification and tooling
- events
- WhatsApp channel (Meta Cloud API or Twilio Sandbox)
- fixtureModels.tsx
- conn
- token
- strip_quoted
- sender_authenticated
- calculate
- process_file
- PendantField.tsx
- FixtureInspector.tsx
- LightingScene.tsx
- Google Apps Script integration
- useScenePlayback
- Voice and product-label media lifecycle
- TestEnvironment
- test_hostile_media_text_only_receives_fixed_clarification
- search
- semantic.py
- test_telegram.py
- Layer 3: Business features
- _stock_rows
- test_runtime_media_is_deleted_after_seven_days_but_text_and_thread_remain
- scripts
- User decisions register
- Layer 4: Agent worker
- sender_address
- queue_drive_export
- Showcase shot list (90-120 seconds)
- conn
- conn
- test_handshake_requires_the_exact_verify_token_and_full_configuration

## God Nodes (most connected - your core abstractions)
1. `DomainError` - 166 edges
2. `October 29, 2026 - Offline embedding contract tests and engine recovery result` - 145 edges
3. `database()` - 112 edges
4. `post()` - 102 edges
5. `get_detail()` - 101 edges
6. `settings()` - 89 edges
7. `create_request()` - 86 edges
8. `make_draft()` - 61 edges
9. `audit()` - 60 edges
10. `react` - 58 edges

## Surprising Connections (you probably didn't know these)
- `Agent fallback and publication recheck` --references--> `ask()`  [INFERRED]
  docs/reference/CATALOG.md → app/agents/luma_agent/nodes/workflow.py
- `1. Problem` --references--> `prepare()`  [INFERRED]
  docs/proposals/2026-11-07-stock-orders-plan.md → app/agents/luma_agent/nodes/workflow.py
- `3.3 Readers that change (task T1)` --references--> `prepare()`  [INFERRED]
  docs/proposals/2026-11-07-stock-orders-plan.md → app/agents/luma_agent/nodes/workflow.py
- `8. Tests and evidence (every task)` --references--> `prepare()`  [INFERRED]
  docs/proposals/2026-11-07-stock-orders-plan.md → app/agents/luma_agent/nodes/workflow.py
- `Command ownership` --references--> `prepare()`  [INFERRED]
  docs/reference/TOOLING_AND_TESTS.md → app/agents/luma_agent/nodes/workflow.py

## Import Cycles
- None detected.

## Communities (226 total, 70 thin omitted)

### Community 0 - "psycopg"
Cohesion: 0.03
Nodes (33): reserve(), usage_totals(), recover_expired(), test_duplicate_paid_operation_never_reserves_again(), test_retrieval_requires_settled_room_and_cannot_repeat(), test_unresolved_prior_day_call_still_consumes_daily_allowance(), pending(), run_next() (+25 more)

### Community 1 - "ProviderError"
Cohesion: 0.06
Nodes (21): send_pdf(), send_text(), ProviderError, answer_callback(), call(), fetch_media(), get_updates(), make_client() (+13 more)

### Community 2 - "test_semantic_catalog.py"
Cohesion: 0.13
Nodes (10): index_company(), embedding_inputs(), has_current_embeddings(), publish_embeddings(), Operator indexing, test_live_embedding_index_and_query_roundtrip(), publish_fixture(), test_index_publication_rejects_changed_input() (+2 more)

### Community 3 - "October 29, 2026 - Offline embedding contract tests and engine recovery result"
Cohesion: 0.02
Nodes (118): 2026-10-29 - Agent fallback boundary tests added, 2026-10-29 - Agent fallback checks passed and evidence consolidated, 2026-10-29 - All Mermaid views rendered locally, 2026-10-29 - Configuration and verification reference coverage, 2026-10-29 — Current workflow documentation and screenshot reviewed, 2026-10-29 — Database gates passed; browser startup assertion failed, 2026-10-29 - Deep agent, media and retrieval references, 2026-10-29 - Deep backend and persistence documentation (+110 more)

### Community 6 - "frontend/package.json"
Cohesion: 0.08
Nodes (30): devDependencies, jsdom@^29.1.1, openapi-typescript@^7.13.0, tailwindcss@^4.3.3, @tailwindcss/vite@^4.3.3, @testing-library/jest-dom@^6.9.1, @testing-library/react@^16.3.3, @types/node@^22.0.0 (+22 more)

### Community 7 - "test_whatsapp.py"
Cohesion: 0.14
Nodes (19): conversation_for(), deliver_webhook(), drain(), envelope(), rows(), start(), test_concurrent_duplicate_webhooks_and_workers_process_each_event_once(), test_hostile_media_metadata_is_refused_without_fetching_or_storing() (+11 more)

### Community 8 - "evaluation_dataset.py"
Cohesion: 0.04
Nodes (35): Unit and component coverage, 2026-11-02 - Holdout freeze guard (phase 6 preparation, offline), 2026-11-03 - Pre-freeze Recall@5 relabel: 7 to 14 retrieval cases (phase 6, local), catalog_model(), _check_outcome(), _check_retrieval(), _check_structure(), _check_turns() (+27 more)

### Community 9 - "StrictModel"
Cohesion: 0.04
Nodes (28): ResponseModel, StrictModel, AdjustmentInput, AlertAck, AlertCounts, AlertRow, AlertsView, LevelView (+20 more)

### Community 10 - "make_draft"
Cohesion: 0.08
Nodes (18): approve(), approved_quote(), exports(), poller(), Poller, test_changed_pdf_blocks_the_export_instead_of_shipping_different_bytes(), test_concurrent_pollers_cannot_claim_the_same_export(), test_failures_retry_then_block_and_expired_leases_are_reclaimed() (+10 more)

### Community 11 - "evaluate_scenarios.py"
Cohesion: 0.06
Nodes (22): main(), evaluate(), main(), evaluate(), load_catalog(), main(), run_scenario(), summarize() (+14 more)

### Community 12 - "cn"
Cohesion: 0.11
Nodes (30): PendantField, SignIn(), NewRequest(), cn(), Badge(), badgeVariants, Empty(), EmptyContent() (+22 more)

### Community 13 - "react"
Cohesion: 0.18
Nodes (24): AdjustDialog(), AdjustForm(), CancelForm(), CancelOrderDialog(), MovementsDrawer(), DraftLine, lineIsValid(), NewOrderForm() (+16 more)

### Community 14 - "AudioWaveform"
Cohesion: 0.16
Nodes (18): AudioWaveform(), decodeAudioData(), MediaPreview(), load(), computePeaks(), formatClock(), normalizePeaks(), documentUrl() (+10 more)

### Community 15 - "bootstrap.py"
Cohesion: 0.06
Nodes (22): validate_media_provider(), run_media(), digest(), delete_files(), get_file(), put_file(), storage_headers(), seed_opening() (+14 more)

### Community 16 - "Button"
Cohesion: 0.08
Nodes (40): ConversationCommand, useConversationAction(), ConversationComposer(), ConversationThread(), InboxPage(), JobState(), InboxSection, SectionSwitch() (+32 more)

### Community 17 - "test_twilio.py"
Cohesion: 0.09
Nodes (17): count_inbox(), inbound(), post_form(), receipt(), sid(), sign(), start(), test_approved_quotation_is_offered_as_the_exact_pdf_behind_a_signed_link() (+9 more)

### Community 18 - "clarification_for"
Cohesion: 0.11
Nodes (13): clarification_for(), Integration coverage by responsibility, 2026-11-02 - Negative (mutation-style) checks for hostile-content tests, test_provider_failure_and_worker_logs_do_not_leak_canaries(), extracted(), test_duplicate_sku_requires_clarification(), test_empty_placeholder_lines_do_not_suppress_candidate_discovery(), test_explicit_matching_text_confirms_media_fields() (+5 more)

### Community 19 - "validate"
Cohesion: 0.07
Nodes (23): catalog_context(), is_yes(), known_skus(), model_input(), restatement(), safe_reply(), transcript(), unknown_reply() (+15 more)

### Community 20 - "Overview.tsx"
Cohesion: 0.10
Nodes (33): App(), InventoryPage, CatalogPage(), FixtureCanvas, FixtureInspector, FixtureView, ConnectionHub, connections (+25 more)

### Community 21 - "conversation"
Cohesion: 0.07
Nodes (27): _deliver_local(), enqueue(), change_ownership(), queue_staff_reply(), record_customer_reply(), record_note(), conversation(), execute() (+19 more)

### Community 22 - "re"
Cohesion: 0.10
Nodes (12): degrade(), draw_label(), font(), make_photo(), make_voice(), mix(), noise(), read_wave() (+4 more)

### Community 23 - "pathlib"
Cohesion: 0.08
Nodes (17): F8 - Whole-app visual and accessibility review with evidence (G9), Browser scenario and screenshots, Command ownership, Development tooling, verification and evidence interpretation, Explicit provider canaries, Git workflow, Historical checkpoint and remaining gates, Isolated integration environment (+9 more)

### Community 24 - "scripts"
Cohesion: 0.06
Nodes (36): scripts, build, check:architecture, check:docs, check:frontend, check:rules, check:secrets, db:configure (+28 more)

### Community 25 - "ReceiptRequest"
Cohesion: 0.15
Nodes (5): ReceiptRequest, base_receipt(), test_media_hosts_must_be_meta_owned_https(), test_receipt_models_reject_incomplete_or_unsafe_outcomes(), test_valid_receipts_and_drive_filenames()

### Community 26 - "workspace/schemas.py"
Cohesion: 0.09
Nodes (14): ActivityView, CompanyView, ConversationDetail, ConversationView, DeliveryView, JobView, MessageView, ProductView (+6 more)

### Community 27 - "glowTexture"
Cohesion: 0.28
Nodes (14): ConnectionHub(), Constellation(), Floor(), Hub(), HubNode, labels, labelTexture(), Satellite() (+6 more)

### Community 28 - "skills.py"
Cohesion: 0.12
Nodes (13): active_skills(), check_frontmatter(), check_links(), check_manifests(), check_mirror(), check_routing(), digest(), located() (+5 more)

### Community 29 - "test_stock_acceptance.py"
Cohesion: 0.02
Nodes (94): health(), callback(), customer_messages(), jobs(), notices(), one(), quote_status(), refusal_setup() (+86 more)

### Community 30 - "test_trace_masking.py"
Cohesion: 0.10
Nodes (7): test_business_content_is_kept(), test_disabled_tracing_exports_nothing(), test_media_bytes_and_inline_data_are_omitted(), test_model_call_exports_tokens_and_estimated_cost(), test_production_client_masks_every_exported_field(), test_set_usage_is_a_noop_without_a_run(), test_tracing_is_forced_off_outside_a_job_trace()

### Community 31 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.24
Nodes (7): Code layout, Commands, Documentation (decisions D30, D33), LumaQuote working rules, Rules, Skill routing, Unattended work and accounts

### Community 32 - "prepare"
Cohesion: 0.08
Nodes (30): validate_embedding_provider(), build_graph(), route(), assert_job(), assert_request_version(), retrieve(), ask(), clarify() (+22 more)

### Community 33 - "index.cjs"
Cohesion: 0.10
Nodes (25): crypto, embeddedBlock(), existingFile(), fingerprint(), fs, hash(), path, readCatalog() (+17 more)

### Community 34 - "post"
Cohesion: 0.02
Nodes (64): early_in_minute(), first_denial(), test_approval_limit_is_10_per_minute(), test_catalog_search_limit_is_30_per_minute(), test_customer_messages_are_limited_per_conversation(), test_failed_requests_also_consume_admission(), test_queue_capacity_refuses_work_at_100_with_a_recoverable_503(), test_read_limit_is_120_per_minute() (+56 more)

### Community 35 - "inventory/api.ts"
Cohesion: 0.06
Nodes (71): AlertItem(), AlertsTab(), describe(), AlertRow, AlertsView, inventoryKeys, MovementRow, MovementsPage (+63 more)

### Community 36 - "processor.py"
Cohesion: 0.24
Nodes (4): inspect_audio(), inspect_image(), inspect_pdf(), main()

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
Cohesion: 0.13
Nodes (18): draftSuite(), capturesLatestCleanVersion(), preservesConflict(), fixture(), useQuotationDraft(), beginEdit(), updateDiscount(), updateLines() (+10 more)

### Community 41 - "ref_node_path"
Cohesion: 0.09
Nodes (16): fs, path, root, { spawnSync }, fs, path, root, { spawnSync } (+8 more)

### Community 42 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, baseUrl, esModuleInterop, jsx, lib, module, moduleResolution (+10 more)

### Community 43 - "Stock, customer orders and supplier purchasing: implementation plan"
Cohesion: 0.17
Nodes (12): 10. Out of scope (not decided, not built), 11. Open gaps, 1. Problem, 2. Actors and authority, 3.1 Tables (one migration, task T1), 3.3 Readers that change (task T1), 3. Stock model, 5. Staff actions, purchasing and alerts (task T4) (+4 more)

### Community 44 - "estimated-allowance"
Cohesion: 0.10
Nodes (20): app/agents/luma_agent/budget.py, app/agents/luma_agent/nodes/retrieval.py, app/agents/luma_agent/runtime/media.py, app/agents/luma_agent/runtime/recovery.py, app/backend/luma/features/media/intake.py, app/backend/luma/features/media/persistence.py, estimated-allowance, media-lifecycle (+12 more)

### Community 45 - "quotation-approval"
Cohesion: 0.11
Nodes (19): app/agents/luma_agent/runtime/delivery.py, app/backend/luma/features/conversations/participation.py, app/backend/luma/features/quotations/approval.py, app/backend/luma/features/quotations/drafting.py, app/backend/luma/features/quotations/freshness.py, quotation-approval, sales-workflow, bindings (+11 more)

### Community 46 - "Test layers"
Cohesion: 0.11
Nodes (19): 10. Security, privacy, and abuse tests, 11. Concurrency, fault injection, and recovery tests, 12. Performance, accessibility, and visual acceptance, 1. Static and build checks, 2. Unit tests, 3. Property and state-machine tests, 4. Frontend component tests, 5. API and provider contract tests (+11 more)

### Community 47 - "deliver_one"
Cohesion: 0.13
Nodes (13): deliver_one(), start(), test_approved_quotation_is_uploaded_as_the_exact_canonical_pdf(), test_gates_block_without_calling_telegram(), test_text_reply_is_sent_once_without_a_service_window(), test_uncertain_and_failed_sends_are_never_retried(), test_text_reply_is_submitted_once_as_a_twilio_message(), outbox() (+5 more)

### Community 48 - "DomainError"
Cohesion: 0.04
Nodes (43): audit(), DomainError, require_admin(), next_number(), queue_notice(), apply_movement(), convert_quote(), ensure_level() (+35 more)

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

### Community 54 - "AppShell.tsx"
Cohesion: 0.07
Nodes (39): AppShell(), navigation, useConversation(), MediaUpload(), useAlerts(), InventoryNavCount(), useWorkspace(), followStream() (+31 more)

### Community 55 - "whatsapp_client.py"
Cohesion: 0.10
Nodes (16): call(), download(), endpoint(), fetch_media(), GraphError, headers(), make_client(), media_host_allowed() (+8 more)

### Community 56 - "database"
Cohesion: 0.05
Nodes (42): rate_limit(), database(), domain_error(), operation(), membership(), search(), source_pdf(), customer_reply() (+34 more)

### Community 57 - "Persistent data, privileges and migration lifecycle"
Cohesion: 0.07
Nodes (31): Changes on 2026-11-03, Extending safely, Layer 6: Data (PostgreSQL and private Storage), Migrations, Open gaps, Retention and recovery, What is stored, Who may reach what (+23 more)

### Community 58 - ".claim"
Cohesion: 0.09
Nodes (12): conn(), exports_of(), other_company(), poller(), queue(), StockPoller, test_claim_carries_this_company_only(), test_concurrent_pollers_cannot_claim_the_same_export() (+4 more)

### Community 59 - "package.json"
Cohesion: 0.16
Nodes (15): devDependencies, @google/clasp@3.4.1, mermaid@11.17.2, supabase@2.122.0, typescript@5.9.3, typescript, name, overrides (+7 more)

### Community 60 - "webhook.py"
Cohesion: 0.05
Nodes (26): addressed_to_us(), configured(), expected_signature(), first(), message_event(), receive_message(), receive_status(), status_event() (+18 more)

### Community 61 - "manual-workflow.cjs"
Cohesion: 0.25
Nodes (10): beat(), { chromium, expect }, dispatchFixture(), fs, main(), path, PRIVATE, processMediaFixture() (+2 more)

### Community 62 - "outbound.py"
Cohesion: 0.08
Nodes (19): answer_buttons(), begin(), block(), submit(), adapter(), fetch_media(), live_enabled(), ready() (+11 more)

### Community 63 - "vitest"
Cohesion: 0.16
Nodes (14): request, request, request, purchase, request, order, request, items (+6 more)

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

### Community 69 - "ExportEnvelope"
Cohesion: 0.10
Nodes (7): ClaimRequest, ExportEnvelope, StockClaimRequest, StockReceiptRequest, MailClaim, MailReceipt, MailPush

### Community 70 - "catalog-retrieval"
Cohesion: 0.18
Nodes (11): app/agents/luma_agent/nodes/workflow.py, app/backend/luma/features/catalog/criteria.py, app/backend/luma/features/catalog/retrieval.py, app/backend/luma/features/catalog/semantic.py, bindings, height, renderer_sha256, source_sha256 (+3 more)

### Community 71 - "Email channel (Gmail through Apps Script)"
Cohesion: 0.18
Nodes (11): Actors and authority, Configuration (names only), Email channel (Gmail through Apps Script), External effects and secrets, Failures and recovery, Idempotency, Limits and cost, Open gaps (+3 more)

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

### Community 82 - "test_approved_quotation_is_claimed_with_the_exact_canonical_pdf"
Cohesion: 0.29
Nodes (4): 2026-11-07 - Gmail quotation PDF live test (phase 4, live), conversation_for(), process(), test_approved_quotation_is_claimed_with_the_exact_canonical_pdf()

### Community 83 - "authorization.py"
Cohesion: 0.12
Nodes (7): check_quotation(), assert_dispatchable(), product(), test_dispatch_rejects_invalid_approval_bindings(), test_independently_calculated_discount_and_shipping(), test_invalid_commercial_input_cannot_be_quoted(), test_salesperson_cannot_grant_discount()

### Community 84 - "Local Supabase"
Cohesion: 0.22
Nodes (9): Conflicts, unavailable infrastructure and evidence, Credentials and application configuration, Local Supabase, Media and worker diagnosis, Native processes and optional provider work, Schema, Semantic index command under development, Services (+1 more)

### Community 85 - "upload_audio"
Cohesion: 0.23
Nodes (3): image_preview(), upload_audio(), upload_image()

### Community 86 - "worker.py"
Cohesion: 0.09
Nodes (16): finish(), process_audio(), process_conversation(), claim_job(), finish_job(), process_media(), main(), poll_telegram() (+8 more)

### Community 87 - "Morning actions"
Cohesion: 0.12
Nodes (16): Decision needed: failed requests are not rate limited, Evidence limits, Gmail requests (D47), Google callback preparation, Google Workspace / clasp, LangSmith account limit, Latest verification, Local Docker / WSL availability (+8 more)

### Community 88 - "LumaQuote"
Cohesion: 0.25
Nodes (8): Documentation, LumaQuote, LumaQuote request-to-reviewed-offer workflow, Run locally, Status and next actions, Structure, Verification, Workflow at a glance

### Community 89 - "Configuration and native process operation"
Cohesion: 0.22
Nodes (9): Auth succeeds but the workspace request fails, Configuration and native process operation, Local sign-in fails while Windows reserves the Supabase ports, Messaging and Google configuration, Paid AI policy, Private generated files and reproducibility, Safe routine operation, Supabase and database identities (+1 more)

### Community 90 - "page-review.cjs"
Cohesion: 0.13
Nodes (16): @axe-core/playwright@^4.13.0, @playwright/test@^1.64.1, @axe-core/playwright, @playwright/test, { chromium }, fs, main(), ROUTES (+8 more)

### Community 91 - "CatalogSearch"
Cohesion: 0.16
Nodes (6): query_constraints(), SearchCriteria, search_catalog(), CatalogSearch, test_lookup_is_tenant_scoped_and_cannot_accept_client_authority(), test_shared_filters_keep_explicit_model_and_specs()

### Community 92 - "LumaQuote architecture"
Cohesion: 0.40
Nodes (5): Agent participation and recovery limits, Code ownership, LumaQuote architecture, Processes and trust boundaries, Semantic retrieval work in progress

### Community 93 - "media.py"
Cohesion: 0.08
Nodes (21): embed_texts(), MediaReading, _read_label(), read_media(), configured_secrets(), flush(), job_trace(), mask() (+13 more)

### Community 94 - "appsscript.json"
Cohesion: 0.33
Nodes (5): dependencies, exceptionLogging, oauthScopes, runtimeVersion, timeZone

### Community 95 - "inventory/exports.py"
Cohesion: 0.13
Nodes (6): export_filename(), _movement_rows(), _order_rows(), _purchase_rows(), _sheet_cell(), _utc_naive()

### Community 96 - "frontend-live-updates"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/workspace/routes.py, app/frontend/src/features/workspace/api.ts, app/frontend/src/features/workspace/useLiveUpdates.ts, app/frontend/src/shared/api/events.ts, frontend-live-updates, bindings, height, renderer_sha256 (+3 more)

### Community 97 - "Sales and agent workflows"
Cohesion: 0.40
Nodes (5): Agent requests and evidence, Manual quotation, Notes, human replies and takeover, Sales and agent workflows, Voice and product-label photos

### Community 98 - "test_acceptance_phrases.py"
Cohesion: 0.15
Nodes (7): test_a_bare_courtesy_word_does_not_change_the_answer(), test_a_mobile_signature_is_cut_from_an_email_reply(), test_accept_phrases(), test_courtesy_never_turns_other_text_into_an_answer(), test_decline_phrases(), test_everything_else_is_ordinary_text(), test_non_text_is_not_an_answer()

### Community 100 - "staff"
Cohesion: 0.12
Nodes (11): auth_client(), staff(), Binary attachment protocol, Command payloads and a review sequence, Errors and limits, Identity and mutation protocol, Regenerating contracts, Staff API reference (+3 more)

### Community 101 - "order-lifecycle"
Cohesion: 0.10
Nodes (21): app/backend/luma/features/inventory/ledger.py, app/backend/luma/features/orders/acceptance.py, app/backend/luma/features/orders/management.py, app/backend/luma/features/orders/service.py, app/backend/luma/features/purchasing/routes.py, app/backend/luma/features/purchasing/service.py, supabase/migrations/20261107030000_stock_ledger.sql, order-lifecycle (+13 more)

### Community 102 - "Visual guide to LumaQuote"
Cohesion: 0.33
Nodes (5): Data and runtime, Layer views, Maintaining a view, Visual guide to LumaQuote, Workflow and architecture

### Community 103 - "Project documentation"
Cohesion: 0.50
Nodes (4): Current verification boundaries, Detailed implementation references, Documentation coverage and update ownership, Project documentation

### Community 104 - "hashlib"
Cohesion: 0.04
Nodes (25): verify_hint(), verify_mapping(), verify_signature(), claim_export(), drive_filename(), record_nonce(), record_receipt(), verify_envelope() (+17 more)

### Community 105 - "rule-enforcement"
Cohesion: 0.17
Nodes (12): .claude/settings.json, scripts/check_docs.py, scripts/hooks/guard.py, scripts/skills.py, scripts/summarize_agent_run.py, rule-enforcement, bindings, height (+4 more)

### Community 106 - "test_embedding_contracts.py"
Cohesion: 0.15
Nodes (6): test_embedding_response_indices_bind_each_vector_to_its_requested_record(), create(), test_invalid_provider_vectors_fail_closed(), test_shared_filters_refuse_ambiguous_or_negated_requirements(), test_valid_vector_has_only_finite_numeric_json(), unit_vector()

### Community 108 - "Verified OpenAI contracts"
Cohesion: 0.67
Nodes (3): Embedding adapter under development, Photo label-reading contract, Verified OpenAI contracts

### Community 110 - "run"
Cohesion: 0.14
Nodes (12): 2026-11-07 - Stock ledger tables and single writer (phase 7, local), reply_texts(), run(), start(), test_free_wording_is_restated_then_yes_prepares_review(), test_model_reads_conversation_and_catalog_without_prices(), test_unknown_sku_is_not_restated_and_yes_then_asks_the_model(), test_unsafe_model_reply_is_replaced_by_the_fixed_question() (+4 more)

### Community 111 - "scripts"
Cohesion: 0.07
Nodes (23): 1. What went wrong so far (evidence from the work log and this session), 2. Principles, 3. The rulebook (replaces most of AGENTS.md + CLAUDE.md prose), 4.1 Make skills discoverable, 4.2 Consolidate 37 -> about 20 skills, 4.3 One routing table, 4. Skill routing, 5. Documentation: one home per fact (+15 more)

### Community 115 - "inventory/queries.py"
Cohesion: 0.19
Nodes (6): low_stock_count(), low_stock_rows(), movements_page(), open_alerts(), stock_rows(), How the rest of the application reads stock

### Community 116 - "health"
Cohesion: 0.18
Nodes (11): Evaluation scoring pin (R11), Failure and recovery, Knowledge graph (decision D33), npm checks, Overview, Rule-to-enforcement map, `scripts/check_docs.py` details, `scripts/skills.py` details (+3 more)

### Community 117 - "subprocess"
Cohesion: 0.04
Nodes (31): `bash` (PreToolUse on Bash, R15), Claude Code hooks, `edit` (PostToolUse on Edit and Write, R6), `stop` (Stop, R14 and R8-R10), docker(), bash(), block(), changed_paths() (+23 more)

### Community 118 - "google_sync/routes.py"
Cohesion: 0.06
Nodes (31): accept_hint(), EditHint, drive_export_claim(), drive_export_receipt(), google_callback(), signed_body(), stock_export_claim(), stock_export_receipt() (+23 more)

### Community 119 - "email_dispatch.py"
Cohesion: 0.05
Nodes (45): accept_customer_text(), accept_quote_button(), held_quantities(), reconcile(), release_quote(), authorize_outbound(), claim_mail(), queue() (+37 more)

### Community 123 - "test_brain.py"
Cohesion: 0.13
Nodes (8): make(), test_anything_more_than_agreement_is_not_yes(), test_plain_agreement_is_yes(), test_plain_reply_passes_trimmed(), test_restatement_is_built_from_pairs_only(), test_unsafe_or_empty_replies_are_dropped(), test_unusable_model_orders_are_rejected(), test_valid_lines_normalize_case()

### Community 127 - "reduce_mail"
Cohesion: 0.19
Nodes (6): MailItem, reduce_mail(), item(), test_empty_body_uses_subject_and_attachments_only_is_unsupported(), test_reduce_builds_an_email_event(), test_unparseable_sender_is_skipped()

### Community 128 - "settings"
Cohesion: 0.06
Nodes (24): settings(), Settings, ready(), key(), load_pdf(), quotation_pdf(), quotation_url(), signature() (+16 more)

### Community 144 - "CatalogHit"
Cohesion: 0.16
Nodes (11): candidate_question(), CatalogHit, Agent fallback and publication recheck, Catalog evidence, lexical search and semantic fallback, Evaluation and what the evidence proves, Exact and lexical lookup before admitted semantic fallback, Lexical retrieval, Record and result contracts (+3 more)

### Community 145 - "claim_stock_export"
Cohesion: 0.19
Nodes (7): claim_stock_export(), build_workbook(), collect(), ExportTable, sheet_payload(), export_xlsx(), 2026-11-08 - Excel download and Google Sheets stock export (phase 7, local)

### Community 146 - "process_next"
Cohesion: 0.15
Nodes (5): apply_status(), claim(), finish(), process_next(), Retry

### Community 147 - "test_surface_inventory.py"
Cohesion: 0.24
Nodes (4): operations(), test_gateway_exposes_only_signed_receivers_and_no_documentation_or_staff_route(), test_staff_api_directly_mounted_paths_are_health_and_documentation_only(), test_staff_api_surface_is_the_reviewed_inventory_and_only_health_is_open()

### Community 148 - "pin"
Cohesion: 0.21
Nodes (5): pin(), run_summarizer(), test_changed_or_missing_pin_is_refused_without_post_hoc(), test_matching_pin_is_scored_normally(), test_post_hoc_flag_labels_the_report()

### Community 150 - "dependency_unavailable"
Cohesion: 0.17
Nodes (11): dependency_unavailable(), response_boundaries(), Layer 2: Transport (staff API and signed gateway), Open gaps, Request pipeline, Status codes a caller should expect, Tests and evidence, The two processes (+3 more)

### Community 151 - "_assert_no_canaries"
Cohesion: 0.19
Nodes (7): _assert_no_canaries(), _job(), test_exception_text_and_error_field_are_masked(), test_metadata_tags_and_job_payload_are_masked(), test_nested_tool_and_subgraph_runs_are_masked(), inner(), lookup_tool()

### Community 152 - "test_migrations.py"
Cohesion: 0.14
Nodes (8): Data model, apply(), scratch(), shape(), test_all_migrations_apply_cleanly_and_match_the_live_schema(), test_stock_ledger_backfills_every_product_then_drops_available(), test_stock_tables_are_protected_and_the_ledger_is_append_only(), test_upgrade_keeps_pending_work()

### Community 154 - "FRONTEND.md"
Cohesion: 0.11
Nodes (16): Changes on 2026-11-03, Extending safely, Layer 1: Presentation (React staff workspace), Open gaps, Routes, Tests and evidence, Acceptance for the whole plan, Branch, pull request and merge (decision D39) (+8 more)

### Community 155 - "test_agent_on_development_scenario"
Cohesion: 0.29
Nodes (3): seed_catalog(), spent(), test_agent_on_development_scenario()

### Community 157 - "allowlist.py"
Cohesion: 0.21
Nodes (5): allowed(), allowed_email_senders(), allowed_senders(), allowed_telegram_users(), test_allowlist_parses_plus_whitespace_and_empty()

### Community 160 - "safe_text"
Cohesion: 0.20
Nodes (5): safe_text(), test_control_characters_are_removed_and_length_is_bounded(), test_every_formula_lead_gets_a_leading_apostrophe(), test_non_strings_stay_what_they_are(), test_ordinary_text_is_untouched()

### Community 161 - "io"
Cohesion: 0.25
Nodes (3): test_image_is_normalized_without_metadata(), test_native_pdf_retains_original_page_text(), test_overlong_audio_is_rejected_before_transcription()

### Community 164 - "test_safe_text.py"
Cohesion: 0.22
Nodes (4): tables(), test_export_filename_uses_the_utc_day(), test_sheet_payload_guards_text_and_keeps_numbers_numeric(), test_workbook_cells_are_typed_and_text_is_never_a_formula()

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

### Community 169 - "sceneKit.ts"
Cohesion: 0.33
Nodes (8): LostPendant(), Pendant(), sputter(), Studio(), LIGHT_COLOURS, LightTemperature, rooms, studioEnvironment()

### Community 171 - "Cross-cutting layer: verification and tooling"
Cohesion: 0.40
Nodes (5): Changes on 2026-11-03, Cross-cutting layer: verification and tooling, Open gaps, Test families by layer, The verify gate

### Community 173 - "WhatsApp channel (Meta Cloud API or Twilio Sandbox)"
Cohesion: 0.22
Nodes (9): Configuration (names only), Data, Failure and recovery, Inbound media, Ingress, Module and call flow, Proof and limits, WhatsApp channel (Meta Cloud API or Twilio Sandbox) (+1 more)

### Community 174 - "fixtureModels.tsx"
Cohesion: 0.32
Nodes (13): BELL, Brass(), Downlight(), Emergency(), Family, FamilySpec, HighBay(), Housing() (+5 more)

### Community 189 - "strip_quoted"
Cohesion: 0.20
Nodes (6): strip_quoted(), Inputs and outputs, 2026-11-11 - Courtesy words and mobile signatures in accept replies (phase 7, local), test_a_signature_line_only_cuts_when_it_is_the_whole_line(), test_an_email_reply_with_quoted_history_reduces_to_the_phrase(), test_quoted_history_is_removed()

### Community 190 - "sender_authenticated"
Cohesion: 0.22
Nodes (5): sender_authenticated(), Sender authentication, test_anything_else_is_unauthenticated(), test_each_passing_mechanism_counts(), test_gmail_pass_authenticates_the_from_domain()

### Community 191 - "calculate"
Cohesion: 0.12
Nodes (11): calculate(), Admission and repeat submissions, Backend contracts and business transactions, Canonical quotation, exact approval and final dispatch checks, Composition and dependency direction, Drafting an immutable offer, Failure boundaries and evidence, Identity, company selection and transactions (+3 more)

### Community 193 - "process_file"
Cohesion: 0.22
Nodes (4): bounded_output(), process_file(), Fixed sandbox boundary, test_corrupt_files_are_rejected()

### Community 194 - "PendantField.tsx"
Cohesion: 0.47
Nodes (5): layout(), PendantField(), Pendants(), PendantSpec, three

### Community 204 - "FixtureInspector.tsx"
Cohesion: 0.21
Nodes (14): fadeTexture(), FixtureInspector(), InspectedProduct, InspectorModel(), nearestTemperature(), Part, TEMPERATURES, FAMILIES (+6 more)

### Community 205 - "LightingScene.tsx"
Cohesion: 0.36
Nodes (8): beamFade(), beamGeometry(), CameraDrift(), FlutedWall(), HeadParts, HEADS, LightingScene(), TrackHeads()

### Community 206 - "Google Apps Script integration"
Cohesion: 0.29
Nodes (7): Account setup, Evidence limits, Gmail channel (D47), Google Apps Script integration, Local receiver, Source responsibilities, Troubleshooting and verification

### Community 207 - "useScenePlayback"
Cohesion: 0.27
Nodes (7): FixtureCanvas(), paperTexture(), RevisionStack(), settle(), Stack(), useScenePlayback(), Optional 3D and presentation limits

### Community 208 - "Voice and product-label media lifecycle"
Cohesion: 0.25
Nodes (7): PhotoReading, Durable state and provider admission, Failure response and evidence, Photo reading contract, Publication and customer confirmation, Voice and product-label media lifecycle, Voice reading contract

### Community 211 - "search"
Cohesion: 0.25
Nodes (4): search(), test_authoritative_family_is_searchable_when_name_uses_different_words(), test_description_lookup_retains_original_page_version_and_explicit_specs(), test_exact_sku_precedes_descriptive_similarity()

### Community 212 - "semantic.py"
Cohesion: 0.38
Nodes (3): semantic_search(), vector_literal(), Cache identity and vector validation

### Community 213 - "test_telegram.py"
Cohesion: 0.11
Nodes (12): poll_once(), Bot, bot(), telegram_conversation(), test_allowlisted_user_opens_a_telegram_conversation_and_others_are_ignored(), test_bot_token_never_reaches_logs(), test_hostile_file_metadata_is_refused_without_downloading(), test_only_private_human_chats_reduce_to_events() (+4 more)

### Community 214 - "Layer 3: Business features"
Cohesion: 0.29
Nodes (7): Changes on 2026-11-03, Extending safely, Features, Layer 3: Business features, Open gaps, Rules every feature follows, Tests and evidence

### Community 215 - "_stock_rows"
Cohesion: 0.33
Nodes (3): _stock_rows(), stock_status(), test_stock_status()

### Community 216 - "test_runtime_media_is_deleted_after_seven_days_but_text_and_thread_remain"
Cohesion: 0.33
Nodes (3): age(), one(), test_runtime_media_is_deleted_after_seven_days_but_text_and_thread_remain()

### Community 217 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, test, typecheck

### Community 218 - "User decisions register"
Cohesion: 0.40
Nodes (5): AI, evaluation and tracing, Integrations, Product and scope, User decisions register, Working method

### Community 219 - "Layer 4: Agent worker"
Cohesion: 0.40
Nodes (5): Layer 4: Agent worker, One tick, Open gaps, Spending and tracing, Tests and evidence

### Community 222 - "Showcase shot list (90-120 seconds)"
Cohesion: 0.67
Nodes (3): Not shown (do not demonstrate or claim), Reproducible evidence behind each claim, Showcase shot list (90-120 seconds)

## Knowledge Gaps
- **1 isolated node(s):** `lumaquote`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2226 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **70 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DomainError` connect `DomainError` to `psycopg`, `settings`, `test_semantic_catalog.py`, `decimal`, `bootstrap.py`, `claim_stock_export`, `process_next`, `validate`, `conversation`, `test_stock_acceptance.py`, `prepare`, `io`, `post`, `events`, `deliver_one`, `database`, `webhook.py`, `calculate`, `process_file`, `Voice and product-label media lifecycle`, `authorization.py`, `semantic.py`, `upload_audio`, `worker.py`, `Layer 4: Agent worker`, `media.py`, `staff`, `hashlib`, `test_embedding_contracts.py`, `google_sync/routes.py`, `email_dispatch.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 59 inferred relationships involving `DomainError` (e.g. with `embed_texts()` and `validate_embedding_provider()`) actually correct?**
  _`DomainError` has 59 INFERRED edges - model-reasoned connections that need verification._
- **What connects `lumaquote` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `psycopg` be split into smaller, more focused modules?**
  _Cohesion score 0.03222468588322247 - nodes in this community are weakly interconnected._
- **Why does `audit()` connect `DomainError` to `psycopg`, `test_semantic_catalog.py`, `test_job_trace_exports_graph_and_model_runs_masked`, `hashlib`, `AudioWaveform`, `deliver_one`, `bootstrap.py`, `claim_stock_export`, `process_next`, `conversation`, `AppShell.tsx`, `email_dispatch.py`, `database`, `Persistent data, privileges and migration lifecycle`, `outbound.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Should `ProviderError` be split into smaller, more focused modules?**
  _Cohesion score 0.06196078431372549 - nodes in this community are weakly interconnected._
- **Why does `conversation()` connect `conversation` to `prepare`, `post`, `inventory/api.ts`, `deliver_one`, `DomainError`, `bootstrap.py`, `validate`, `authorization.py`, `worker.py`, `email_dispatch.py`, `AppShell.tsx`, `test_stock_acceptance.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._