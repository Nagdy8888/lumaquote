# Graph Report - Demo_Project_4  (2026-11-08)

## Corpus Check
- 404 files · ~348,503 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 52 file(s) not represented in the graph (top: .mmd 30, .css 9, .gs 6)

## Summary
- 4180 nodes · 10021 edges · 216 communities (143 shown, 73 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 759 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `71475415`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- psycopg
- settings
- semantic.py
- October 29, 2026 - Offline embedding contract tests and engine recovery result
- test_stock_staff_routes.py
- decimal
- frontend/package.json
- test_whatsapp.py
- evaluation_dataset.py
- StrictModel
- make_draft
- evaluate_scenarios.py
- cn
- scan_secrets.py
- DocumentButton
- bootstrap.py
- Button
- core/errors.py
- test_provider_failure_and_worker_logs_do_not_leak_canaries
- validate
- Overview.tsx
- audit
- re
- pathlib
- scripts
- re
- workspace/schemas.py
- glowTexture
- skills.py
- test_stock_acceptance.py
- test_trace_masking.py
- Proposal: working rules, skill routing and documentation (draft for approval)
- prepare
- index.cjs
- time
- generated.ts
- io
- steps
- retention.py
- Design System: LumaQuote
- useQuotationDraft
- ref_node_path
- compilerOptions
- test_stock_ledger.py
- estimated-allowance
- quotation-approval
- Test layers
- Persistent data, privileges and migration lifecycle
- ledger.py
- LumaQuote implementation tracker
- components.json
- Work log
- main
- AppShell.tsx
- whatsapp_client.py
- media/routes.py
- check_frontend.cjs
- stored_quotation_pdf
- package.json
- twilio_webhook.py
- manual-workflow.cjs
- Telegram channel (Bot API, long polling)
- ConversationThread.tsx
- job-recovery
- bindings
- whatsapp-channel
- LumaQuote
- start-local-supabase.cjs
- ExportEnvelope
- catalog-retrieval
- fetch_media
- diagrams
- google-snapshot
- drive-export
- workflow-data
- bindings
- test_storage_outage_leaves_nothing_half_written_and_recovers
- backend-modules
- frontend-draft
- verification-scope
- ui-review.cjs
- test_stock_reservations.py
- inventory/service.py
- Local Supabase
- upload_audio
- worker.py
- Morning actions
- LumaQuote
- Configuration and native process operation
- page-review.cjs
- telegram_ingress.py
- LumaQuote architecture
- media.py
- appsscript.json
- InputRecord
- frontend-live-updates
- Sales and agent workflows
- test_acceptance_phrases.py
- test_every_response_is_private_nosniff_and_unframed
- staff
- order-lifecycle
- Visual guide to LumaQuote
- Project documentation
- DomainError
- rule-enforcement
- rate_limit
- CLAUDE.md
- Verified OpenAI contracts
- IMPLEMENTATION_PLAN.md
- run
- scripts
- Proposal: working rules, skill routing and documentation (draft for approval)
- health
- subprocess
- Apps Script transport and validated commercial snapshots
- inbound.py
- test_brain.py
- email_dispatch.py
- media_links.py
- lumaquote
- Tasks
- Development tooling, verification and evidence interpretation
- catalog.test.cjs
- test_surface_inventory.py
- pin
- test_agent_semantic_fallback_preserves_action_and_source_boundaries
- dependency_unavailable
- _assert_no_canaries
- test_migrations.py
- FakeSession
- Frontend work plan (for Sonnet execution)
- test_agent_on_development_scenario
- check_architecture.py
- Layer 6: Data (PostgreSQL and private Storage)
- test_phone_numbers_are_masked
- test_workspace_reports_only_complete_tenant_mapped_gas_configuration
- purchasing/service.py
- hashlib
- State
- test_job_trace_exports_graph_and_model_runs_masked
- receive
- database
- pull_request_template.md
- Layer 7: External integrations
- LumaQuote by layer
- sceneKit.ts
- brain
- Cross-cutting layer: verification and tooling
- get
- authorize_outbound
- fixtureModels.tsx
- conn
- token
- cancel
- UI_DIRECTION.md
- Backend contracts and business transactions
- accept_media
- PendantField.tsx
- FixtureInspector.tsx
- LightingScene.tsx
- Google Apps Script integration
- useScenePlayback
- AdjustmentInput
- TestEnvironment
- test_hostile_media_text_only_receives_fixed_clarification
- test_every_route_passes_axe_fits_both_viewports_and_masks_capture
- test_unresolved_prior_day_call_still_consumes_daily_allowance
- test_holdout_is_refused_unless_frozen_unspent_and_confirmed

## God Nodes (most connected - your core abstractions)
1. `DomainError` - 163 edges
2. `October 29, 2026 - Offline embedding contract tests and engine recovery result` - 137 edges
3. `database()` - 106 edges
4. `post()` - 102 edges
5. `get_detail()` - 101 edges
6. `settings()` - 88 edges
7. `create_request()` - 86 edges
8. `make_draft()` - 61 edges
9. `audit()` - 53 edges
10. `rate_limit()` - 47 edges

## Surprising Connections (you probably didn't know these)
- `Agent fallback and publication recheck` --references--> `ask()`  [INFERRED]
  docs/reference/CATALOG.md → app/agents/luma_agent/nodes/workflow.py
- `3.3 Readers that change (task T1)` --references--> `prepare()`  [INFERRED]
  docs/proposals/2026-11-07-stock-orders-plan.md → app/agents/luma_agent/nodes/workflow.py
- `Open gaps` --references--> `prepare()`  [INFERRED]
  docs/reference/INVENTORY.md → app/agents/luma_agent/nodes/workflow.py
- `Command ownership` --references--> `prepare()`  [INFERRED]
  docs/reference/TOOLING_AND_TESTS.md → app/agents/luma_agent/nodes/workflow.py
- `Two-step approval confirmation` --references--> `review()`  [INFERRED]
  docs/reference/FRONTEND.md → app/agents/luma_agent/nodes/workflow.py

## Import Cycles
- None detected.

## Communities (216 total, 73 thin omitted)

### Community 0 - "psycopg"
Cohesion: 0.02
Nodes (83): early_in_minute(), first_denial(), test_approval_limit_is_10_per_minute(), test_catalog_search_limit_is_30_per_minute(), test_customer_messages_are_limited_per_conversation(), test_failed_requests_also_consume_admission(), test_queue_capacity_refuses_work_at_100_with_a_recoverable_503(), test_read_limit_is_120_per_minute() (+75 more)

### Community 1 - "settings"
Cohesion: 0.05
Nodes (34): settings(), Settings, delete_files(), put_file(), storage_headers(), ProviderError, adapter(), live_enabled() (+26 more)

### Community 2 - "semantic.py"
Cohesion: 0.05
Nodes (34): query_constraints(), SearchCriteria, candidate_question(), search_catalog(), CatalogHit, CatalogSearch, embedding_inputs(), has_current_embeddings() (+26 more)

### Community 3 - "October 29, 2026 - Offline embedding contract tests and engine recovery result"
Cohesion: 0.02
Nodes (111): 2026-10-29 - Agent fallback boundary tests added, 2026-10-29 - Agent fallback checks passed and evidence consolidated, 2026-10-29 - All Mermaid views rendered locally, 2026-10-29 - Configuration and verification reference coverage, 2026-10-29 — Current workflow documentation and screenshot reviewed, 2026-10-29 — Database gates passed; browser startup assertion failed, 2026-10-29 - Deep agent, media and retrieval references, 2026-10-29 - Deep backend and persistence documentation (+103 more)

### Community 4 - "test_stock_staff_routes.py"
Cohesion: 0.06
Nodes (28): as_salesperson(), conn(), level(), movements(), pending_order(), po_body(), receive_body(), rows() (+20 more)

### Community 6 - "frontend/package.json"
Cohesion: 0.04
Nodes (57): dependencies, class-variance-authority@^0.7.1, clsx@^2.1.1, cn@^0.4.0, @fontsource/ibm-plex-sans@^5.3.0, @fontsource-variable/space-grotesk@^5.3.0, lucide-react@^1.63.0, radix-ui@^1.8.1 (+49 more)

### Community 7 - "test_whatsapp.py"
Cohesion: 0.05
Nodes (47): deliver_one(), Work identities are deliberately different, test_gates_block_without_calling_telegram(), count_inbox(), inbound(), post_form(), receipt(), sid() (+39 more)

### Community 8 - "evaluation_dataset.py"
Cohesion: 0.04
Nodes (35): Unit and component coverage, 2026-11-02 - Holdout freeze guard (phase 6 preparation, offline), 2026-11-03 - Pre-freeze Recall@5 relabel: 7 to 14 retrieval cases (phase 6, local), catalog_model(), _check_outcome(), _check_retrieval(), _check_structure(), _check_turns() (+27 more)

### Community 9 - "StrictModel"
Cohesion: 0.06
Nodes (20): ResponseModel, StrictModel, AlertAck, AlertCounts, AlertRow, AlertsView, LevelView, MovementRow (+12 more)

### Community 10 - "make_draft"
Cohesion: 0.13
Nodes (14): Features, 2026-11-02 - Concurrency tests, showcase shot list and screenshots; CI result, approve(), approved_quote(), exports(), poller(), Poller, test_changed_pdf_blocks_the_export_instead_of_shipping_different_bytes() (+6 more)

### Community 11 - "evaluate_scenarios.py"
Cohesion: 0.06
Nodes (20): evaluate(), main(), evaluate(), load_catalog(), main(), run_scenario(), summarize(), denominators() (+12 more)

### Community 12 - "cn"
Cohesion: 0.12
Nodes (31): NewRequest(), cn(), Badge(), badgeVariants, Empty(), EmptyContent(), EmptyDescription(), EmptyHeader() (+23 more)

### Community 13 - "scan_secrets.py"
Cohesion: 0.14
Nodes (9): load_secrets(), main(), run(), scan_files(), tracked_files(), make_repo(), test_clean_repo_reports_no_leaks(), test_only_secret_looking_long_nonpublic_values_are_loaded() (+1 more)

### Community 14 - "DocumentButton"
Cohesion: 0.10
Nodes (25): PhotoReading, AudioWaveform(), decodeAudioData(), MediaPreview(), load(), computePeaks(), formatClock(), normalizePeaks() (+17 more)

### Community 15 - "bootstrap.py"
Cohesion: 0.12
Nodes (12): digest(), seed_opening(), draft(), latest_quote(), DraftInput, Selection, main(), stable() (+4 more)

### Community 16 - "Button"
Cohesion: 0.10
Nodes (24): PendantField, SignIn(), ConversationCommand, useConversationAction(), QuotationPanel(), ProductSelections(), QuoteSummary(), ReviewActions() (+16 more)

### Community 17 - "core/errors.py"
Cohesion: 0.08
Nodes (17): embed_texts(), validate_embedding_provider(), validate_media_provider(), reserve(), usage_totals(), assert_job(), assert_request_version(), retrieve() (+9 more)

### Community 19 - "validate"
Cohesion: 0.05
Nodes (36): catalog_context(), is_yes(), known_skus(), model_input(), restatement(), safe_reply(), transcript(), unknown_reply() (+28 more)

### Community 20 - "Overview.tsx"
Cohesion: 0.12
Nodes (29): App(), CatalogPage(), FixtureCanvas, FixtureInspector, FixtureView, ConnectionHub, connections, ConnectionsPage() (+21 more)

### Community 21 - "audit"
Cohesion: 0.06
Nodes (27): recover_expired(), enqueue(), audit(), change_ownership(), queue_staff_reply(), record_customer_reply(), record_note(), conversation() (+19 more)

### Community 22 - "re"
Cohesion: 0.10
Nodes (13): degrade(), draw_label(), font(), main(), make_photo(), make_voice(), mix(), noise() (+5 more)

### Community 23 - "pathlib"
Cohesion: 0.08
Nodes (9): F8 - Whole-app visual and accessibility review with evidence (G9), 2026-11-07 - 3D fixture inspector, overview light rail, page transitions (phase 5, local-substitute), main(), run_review(), available_port(), test_complete_native_browser_workflow(), wait_for_server(), test_every_page_passes_axe_and_fits_both_viewports() (+1 more)

### Community 24 - "scripts"
Cohesion: 0.06
Nodes (36): scripts, build, check:architecture, check:docs, check:frontend, check:rules, check:secrets, db:configure (+28 more)

### Community 25 - "re"
Cohesion: 0.08
Nodes (15): configured(), extract_events(), handshake(), message_event(), receive(), status_event(), valid_signature(), base_receipt() (+7 more)

### Community 26 - "workspace/schemas.py"
Cohesion: 0.09
Nodes (14): ActivityView, CompanyView, ConversationDetail, ConversationView, DeliveryView, JobView, MessageView, ProductView (+6 more)

### Community 27 - "glowTexture"
Cohesion: 0.26
Nodes (15): ConnectionHub(), Constellation(), Floor(), Hub(), HubNode, labels, labelTexture(), Satellite() (+7 more)

### Community 28 - "skills.py"
Cohesion: 0.12
Nodes (13): active_skills(), check_frontmatter(), check_links(), check_manifests(), check_mirror(), check_routing(), digest(), located() (+5 more)

### Community 29 - "test_stock_acceptance.py"
Cohesion: 0.04
Nodes (50): poll_once(), External effects and secrets, callback(), conn(), customer_messages(), jobs(), notices(), one() (+42 more)

### Community 30 - "test_trace_masking.py"
Cohesion: 0.10
Nodes (7): test_business_content_is_kept(), test_disabled_tracing_exports_nothing(), test_media_bytes_and_inline_data_are_omitted(), test_model_call_exports_tokens_and_estimated_cost(), test_production_client_masks_every_exported_field(), test_set_usage_is_a_noop_without_a_run(), test_tracing_is_forced_off_outside_a_job_trace()

### Community 31 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.14
Nodes (12): Code layout, Commands, Documentation (decisions D30, D33), LumaQuote working rules, Rules, Skill routing, Unattended work and accounts, AI, evaluation and tracing (+4 more)

### Community 32 - "prepare"
Cohesion: 0.05
Nodes (39): build_graph(), route(), clarify(), prepare(), raise_shortage_alert(), review(), AgentState, Layer 4: Agent worker (+31 more)

### Community 33 - "index.cjs"
Cohesion: 0.15
Nodes (20): crypto, embeddedBlock(), existingFile(), fingerprint(), fs, hash(), path, readCatalog() (+12 more)

### Community 34 - "time"
Cohesion: 0.07
Nodes (10): test_auth_outage_is_a_safe_503_not_an_open_door(), test_cors_allows_only_the_exact_local_origins(), test_declared_oversize_and_malformed_length_are_rejected_before_routing(), test_gateway_never_exposes_staff_routes_or_documentation(), test_mutation_rate_limit_rejects_the_thirty_first_request_with_retry_guidance(), test_private_pdf_is_never_cacheable(), test_complete_snapshot_import_and_rejections(), test_signed_callback_receipts() (+2 more)

### Community 35 - "generated.ts"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 36 - "io"
Cohesion: 0.11
Nodes (10): inspect_audio(), inspect_image(), inspect_pdf(), main(), process_file(), Fixed sandbox boundary, test_corrupt_files_are_rejected(), test_image_is_normalized_without_metadata() (+2 more)

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
Cohesion: 0.09
Nodes (27): draftSuite(), capturesLatestCleanVersion(), preservesConflict(), fixture(), useQuotationDraft(), beginEdit(), updateDiscount(), updateLines() (+19 more)

### Community 41 - "ref_node_path"
Cohesion: 0.09
Nodes (16): fs, path, root, { spawnSync }, fs, path, root, { spawnSync } (+8 more)

### Community 42 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, baseUrl, esModuleInterop, jsx, lib, module, moduleResolution (+10 more)

### Community 43 - "test_stock_ledger.py"
Cohesion: 0.09
Nodes (21): 3.1 Tables (one migration, task T1), 3.2 Single writer, 3.3 Readers that change (task T1), 3. Stock model, Reconcile rules, assert_invariants(), conn(), held() (+13 more)

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
Cohesion: 0.20
Nodes (10): Catalog, commercial snapshot and current embedding relationships, Checkpoints, retention and preservation, Conversation and quotation records, Conversation, offer, approval, media and work relationships, Exact conversation and attachment binding, Google synchronization records, Migration sequence and local application, Persistent data, privileges and migration lifecycle (+2 more)

### Community 48 - "ledger.py"
Cohesion: 0.06
Nodes (32): reconcile_stock(), apply_movement(), convert_quote(), ensure_level(), _held(), held_quantities(), _ids(), _line_quantities() (+24 more)

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
Cohesion: 0.19
Nodes (8): check_encoding(), check_evidence(), check_links(), check_plan(), documentation_files(), evidence_header(), main(), relative()

### Community 54 - "AppShell.tsx"
Cohesion: 0.11
Nodes (26): @tanstack/react-query@^5.105.0, useConversation(), useWorkspace(), followStream(), reconnectDelay(), encoder, MockStream, renderLive() (+18 more)

### Community 55 - "whatsapp_client.py"
Cohesion: 0.10
Nodes (17): call(), download(), endpoint(), fetch_media(), GraphError, headers(), make_client(), media_host_allowed() (+9 more)

### Community 57 - "check_frontend.cjs"
Cohesion: 0.17
Nodes (13): What is stored, Identity and evidence records, definitionName(), fs, inspect(), walk(), main(), visit() (+5 more)

### Community 58 - "stored_quotation_pdf"
Cohesion: 0.10
Nodes (7): quotation_pdf(), stored_quotation_pdf(), decision(), draft(), pdf(), Decision, run()

### Community 59 - "package.json"
Cohesion: 0.16
Nodes (15): devDependencies, @google/clasp@3.4.1, mermaid@11.17.2, supabase@2.122.0, typescript@5.9.3, typescript, name, overrides (+7 more)

### Community 60 - "twilio_webhook.py"
Cohesion: 0.11
Nodes (13): addressed_to_us(), configured(), expected_signature(), first(), message_event(), receive_message(), receive_status(), status_event() (+5 more)

### Community 61 - "manual-workflow.cjs"
Cohesion: 0.25
Nodes (10): beat(), { chromium, expect }, dispatchFixture(), fs, main(), path, PRIVATE, processMediaFixture() (+2 more)

### Community 62 - "Telegram channel (Bot API, long polling)"
Cohesion: 0.11
Nodes (16): _deliver_local(), largest_photo(), reduce_callback(), reduce_update(), 4.1 Recognizing the answer, 4.3 Delivery wording and Telegram buttons, 4. Customer acceptance (task T3), Configuration (names only) (+8 more)

### Community 63 - "ConversationThread.tsx"
Cohesion: 0.10
Nodes (28): AppShell(), navigation, ConversationComposer(), ConversationThread(), InboxPage(), JobState(), MediaUpload(), InboxSection (+20 more)

### Community 64 - "job-recovery"
Cohesion: 0.22
Nodes (9): app/agents/luma_agent/lease.py, app/agents/luma_agent/runtime/jobs.py, job-recovery, bindings, height, renderer_sha256, source_sha256, svg_sha256 (+1 more)

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

### Community 69 - "ExportEnvelope"
Cohesion: 0.11
Nodes (6): ClaimRequest, ExportEnvelope, ReceiptRequest, MailClaim, MailReceipt, MailPush

### Community 70 - "catalog-retrieval"
Cohesion: 0.18
Nodes (11): app/agents/luma_agent/nodes/workflow.py, app/backend/luma/features/catalog/criteria.py, app/backend/luma/features/catalog/retrieval.py, app/backend/luma/features/catalog/semantic.py, bindings, height, renderer_sha256, source_sha256 (+3 more)

### Community 71 - "fetch_media"
Cohesion: 0.07
Nodes (22): sender_authenticated(), Actors and authority, Configuration (names only), Email channel (Gmail through Apps Script), External effects and secrets, Failures and recovery, Idempotency, Limits and cost (+14 more)

### Community 72 - "diagrams"
Cohesion: 0.12
Nodes (15): diagrams, request-trace, worker-tick, mermaid_version, height, renderer_sha256, source_sha256, svg_sha256 (+7 more)

### Community 73 - "google-snapshot"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/google_sync/callbacks.py, app/backend/luma/features/google_sync/snapshots.py, app/backend/luma/features/google_sync/validation.py, gas/Synchronization.gs, google-snapshot, bindings, height, renderer_sha256 (+3 more)

### Community 74 - "drive-export"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/google_sync/exports.py, app/backend/luma/features/quotations/documents.py, gas/Exports.gs, supabase/migrations/20261102000000_drive_exports.sql, drive-export, bindings, height, renderer_sha256 (+3 more)

### Community 75 - "workflow-data"
Cohesion: 0.08
Nodes (26): supabase/migrations/20261029010000_quotation_domain.sql, supabase/migrations/20261029100000_immutable_quotation_content.sql, supabase/migrations/20261029110000_voice_intake.sql, supabase/migrations/20261029111000_media_message_binding.sql, supabase/migrations/20261029131000_versioned_embeddings.sql, bindings, height, renderer_sha256 (+18 more)

### Community 76 - "bindings"
Cohesion: 0.09
Nodes (23): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/backend/luma/core/admission.py, app/backend/luma/core/errors.py (+15 more)

### Community 78 - "backend-modules"
Cohesion: 0.09
Nodes (27): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/agents/luma_agent/worker.py, app/backend/luma/features/media/sandbox.py (+19 more)

### Community 79 - "frontend-draft"
Cohesion: 0.10
Nodes (21): app/frontend/src/app/App.tsx, app/frontend/src/features/conversations/api.ts, app/frontend/src/features/quotations/QuotationPanel.tsx, app/frontend/src/features/quotations/useQuotationDraft.ts, app/frontend/src/main.tsx, app/frontend/src/shared/api/client.ts, app/frontend/vite.config.ts, frontend-draft (+13 more)

### Community 80 - "verification-scope"
Cohesion: 0.11
Nodes (19): .github/workflows/ci.yml, package.json, scripts/verify.cjs, tests/integration/test_browser_workflow.py, tests/integration/test_ui_review.py, verification-scope, verify-gate, bindings (+11 more)

### Community 81 - "ui-review.cjs"
Cohesion: 0.26
Nodes (12): { chromium }, fs, keyboardPass(), livePass(), main(), measure(), PRIVATE, reviewView() (+4 more)

### Community 82 - "test_stock_reservations.py"
Cohesion: 0.08
Nodes (20): 2026-11-07 - Gmail quotation PDF live test (phase 4, live), approved(), assert_nothing_written(), outbox_of(), stock(), submitting_quote(), test_a_ledger_refusal_after_the_snapshot_check_rolls_the_whole_approval_back(), test_approval_reserves_stock_and_dispatch_proves_the_hold() (+12 more)

### Community 83 - "inventory/service.py"
Cohesion: 0.05
Nodes (21): low_stock_count(), low_stock_rows(), movements_page(), open_alerts(), stock_rows(), acknowledge(), alerts(), movements() (+13 more)

### Community 84 - "Local Supabase"
Cohesion: 0.22
Nodes (9): Conflicts, unavailable infrastructure and evidence, Credentials and application configuration, Local Supabase, Media and worker diagnosis, Native processes and optional provider work, Schema, Semantic index command under development, Services (+1 more)

### Community 85 - "upload_audio"
Cohesion: 0.16
Nodes (6): get_file(), audio_playback(), image_preview(), receive_upload(), upload_audio(), upload_image()

### Community 86 - "worker.py"
Cohesion: 0.09
Nodes (14): finish(), process_audio(), process_conversation(), claim_job(), finish_job(), process_media(), main(), poll_telegram() (+6 more)

### Community 87 - "Morning actions"
Cohesion: 0.13
Nodes (15): Decision needed: failed requests are not rate limited, Evidence limits, Gmail requests (D47), Google callback preparation, Google Workspace / clasp, LangSmith account limit, Latest verification, Local Docker / WSL availability (+7 more)

### Community 88 - "LumaQuote"
Cohesion: 0.25
Nodes (8): Documentation, LumaQuote, LumaQuote request-to-reviewed-offer workflow, Run locally, Status and next actions, Structure, Verification, Workflow at a glance

### Community 89 - "Configuration and native process operation"
Cohesion: 0.15
Nodes (9): Configuration and native process operation, Messaging and Google configuration, Paid AI policy, Private generated files and reproducibility, Safe routine operation, Supabase and database identities, Tracing policy, Twilio (+1 more)

### Community 90 - "page-review.cjs"
Cohesion: 0.14
Nodes (16): @axe-core/playwright@^4.13.0, @playwright/test@^1.64.1, @axe-core/playwright, @playwright/test, { chromium }, fs, main(), ROUTES (+8 more)

### Community 91 - "telegram_ingress.py"
Cohesion: 0.25
Nodes (3): test_media_link_binds_outbox_id_and_expires(), test_media_link_refuses_without_a_token(), test_signature_matches_twilio_python_vector()

### Community 92 - "LumaQuote architecture"
Cohesion: 0.40
Nodes (5): Agent participation and recovery limits, Code ownership, LumaQuote architecture, Processes and trust boundaries, Semantic retrieval work in progress

### Community 93 - "media.py"
Cohesion: 0.08
Nodes (20): MediaReading, _read_label(), read_media(), configured_secrets(), flush(), job_trace(), mask(), mask_text() (+12 more)

### Community 94 - "appsscript.json"
Cohesion: 0.33
Nodes (5): dependencies, exceptionLogging, oauthScopes, runtimeVersion, timeZone

### Community 95 - "InputRecord"
Cohesion: 0.15
Nodes (6): InputRecord, InventoryInput, PolicyInput, PriceInput, ProductInput, SupplierTables

### Community 96 - "frontend-live-updates"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/workspace/routes.py, app/frontend/src/features/workspace/api.ts, app/frontend/src/features/workspace/useLiveUpdates.ts, app/frontend/src/shared/api/events.ts, frontend-live-updates, bindings, height, renderer_sha256 (+3 more)

### Community 97 - "Sales and agent workflows"
Cohesion: 0.40
Nodes (5): Agent requests and evidence, Manual quotation, Notes, human replies and takeover, Sales and agent workflows, Voice and product-label photos

### Community 98 - "test_acceptance_phrases.py"
Cohesion: 0.15
Nodes (5): test_accept_phrases(), test_an_email_reply_with_quoted_history_reduces_to_the_phrase(), test_decline_phrases(), test_everything_else_is_ordinary_text(), test_non_text_is_not_an_answer()

### Community 100 - "staff"
Cohesion: 0.12
Nodes (11): auth_client(), staff(), Binary attachment protocol, Command payloads and a review sequence, Errors and limits, Identity and mutation protocol, Regenerating contracts, Staff API reference (+3 more)

### Community 101 - "order-lifecycle"
Cohesion: 0.10
Nodes (21): app/backend/luma/features/inventory/ledger.py, app/backend/luma/features/orders/acceptance.py, app/backend/luma/features/orders/management.py, app/backend/luma/features/orders/service.py, app/backend/luma/features/purchasing/routes.py, app/backend/luma/features/purchasing/service.py, supabase/migrations/20261107030000_stock_ledger.sql, order-lifecycle (+13 more)

### Community 102 - "Visual guide to LumaQuote"
Cohesion: 0.40
Nodes (5): Data and runtime, Layer views, Maintaining a view, Visual guide to LumaQuote, Workflow and architecture

### Community 103 - "Project documentation"
Cohesion: 0.50
Nodes (4): Current verification boundaries, Detailed implementation references, Documentation coverage and update ownership, Project documentation

### Community 104 - "DomainError"
Cohesion: 0.08
Nodes (19): DomainError, accept_hint(), EditHint, verify_hint(), verify_mapping(), verify_signature(), claim_export(), drive_filename() (+11 more)

### Community 105 - "rule-enforcement"
Cohesion: 0.17
Nodes (12): .claude/settings.json, scripts/check_docs.py, scripts/hooks/guard.py, scripts/skills.py, scripts/summarize_agent_run.py, rule-enforcement, bindings, height (+4 more)

### Community 106 - "rate_limit"
Cohesion: 0.16
Nodes (10): rate_limit(), membership(), acknowledge(), adjustments(), alerts(), movements(), reorder_levels(), stock() (+2 more)

### Community 108 - "Verified OpenAI contracts"
Cohesion: 0.67
Nodes (3): Embedding adapter under development, Photo label-reading contract, Verified OpenAI contracts

### Community 109 - "IMPLEMENTATION_PLAN.md"
Cohesion: 0.21
Nodes (4): Not shown (do not demonstrate or claim), Reproducible evidence behind each claim, Showcase shot list (90-120 seconds), Synthetic development confirmation cases

### Community 110 - "run"
Cohesion: 0.14
Nodes (12): 2026-11-07 - Stock ledger tables and single writer (phase 7, local), reply_texts(), run(), start(), test_free_wording_is_restated_then_yes_prepares_review(), test_model_reads_conversation_and_catalog_without_prices(), test_unknown_sku_is_not_restated_and_yes_then_asks_the_model(), test_unsafe_model_reply_is_replaced_by_the_fixed_question() (+4 more)

### Community 111 - "scripts"
Cohesion: 0.11
Nodes (15): conversation_for(), mail(), process(), queued_notice(), rows(), Script, test_approved_quotation_is_claimed_with_the_exact_canonical_pdf(), test_expired_claim_becomes_unknown_and_is_never_offered_again() (+7 more)

### Community 115 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.17
Nodes (12): 1. What went wrong so far (evidence from the work log and this session), 2. Principles, 3. The rulebook (replaces most of AGENTS.md + CLAUDE.md prose), 4.1 Make skills discoverable, 4.2 Consolidate 37 -> about 20 skills, 4.3 One routing table, 4. Skill routing, 5. Documentation: one home per fact (+4 more)

### Community 116 - "health"
Cohesion: 0.18
Nodes (11): Evaluation scoring pin (R11), Failure and recovery, Knowledge graph (decision D33), npm checks, Overview, Rule-to-enforcement map, `scripts/check_docs.py` details, `scripts/skills.py` details (+3 more)

### Community 117 - "subprocess"
Cohesion: 0.06
Nodes (21): `bash` (PreToolUse on Bash, R15), Claude Code hooks, `edit` (PostToolUse on Edit and Write, R6), `stop` (Stop, R14 and R8-R10), bash(), block(), changed_paths(), edit() (+13 more)

### Community 118 - "Apps Script transport and validated commercial snapshots"
Cohesion: 0.18
Nodes (11): Apps Script transport and validated commercial snapshots, Atomic publication and offer freshness, Authority and process boundary, Diagnosis without leaking integration data, Drive export of approved quotations, Envelope authentication and replay, GAS source responsibilities, Invalidation hint versus full snapshot (+3 more)

### Community 119 - "inbound.py"
Cohesion: 0.06
Nodes (29): accept_customer_text(), accept_quote_button(), add_message(), store_media(), allowed(), allowed_email_senders(), allowed_senders(), allowed_telegram_users() (+21 more)

### Community 123 - "test_brain.py"
Cohesion: 0.13
Nodes (8): make(), test_anything_more_than_agreement_is_not_yes(), test_plain_agreement_is_yes(), test_plain_reply_passes_trimmed(), test_restatement_is_built_from_pairs_only(), test_unsafe_or_empty_replies_are_dropped(), test_unusable_model_orders_are_rejected(), test_valid_lines_normalize_case()

### Community 127 - "email_dispatch.py"
Cohesion: 0.07
Nodes (20): record_nonce(), verify_envelope(), claim_mail(), queue(), ready(), record_mail_receipt(), reply_subject(), send_pdf() (+12 more)

### Community 128 - "media_links.py"
Cohesion: 0.15
Nodes (6): domain_error(), key(), load_pdf(), quotation_pdf(), quotation_url(), signature()

### Community 144 - "Tasks"
Cohesion: 0.33
Nodes (6): F0 - Baseline, branch and worktree, F5 - Explicit approval confirmation (G5), F6 - Portrait inbox with a section switcher (G6), F7 - Capture-mode body masking (G7), F9 - Close-out, Tasks

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

### Community 150 - "dependency_unavailable"
Cohesion: 0.17
Nodes (11): dependency_unavailable(), response_boundaries(), Layer 2: Transport (staff API and signed gateway), Open gaps, Request pipeline, Status codes a caller should expect, Tests and evidence, The two processes (+3 more)

### Community 151 - "_assert_no_canaries"
Cohesion: 0.19
Nodes (7): _assert_no_canaries(), _job(), test_exception_text_and_error_field_are_masked(), test_metadata_tags_and_job_payload_are_masked(), test_nested_tool_and_subgraph_runs_are_masked(), inner(), lookup_tool()

### Community 152 - "test_migrations.py"
Cohesion: 0.15
Nodes (8): Data model, apply(), scratch(), shape(), test_all_migrations_apply_cleanly_and_match_the_live_schema(), test_stock_ledger_backfills_every_product_then_drops_available(), test_stock_tables_are_protected_and_the_ledger_is_append_only(), test_upgrade_keeps_pending_work()

### Community 154 - "Frontend work plan (for Sonnet execution)"
Cohesion: 0.25
Nodes (8): Acceptance for the whole plan, Branch, pull request and merge (decision D39), Execution protocol for Sonnet (read before every task), Frontend work plan (for Sonnet execution), How to start, Open questions for the user (not blocking any task; use the stated default), Run to completion (user instruction, 2026-11-03), Why this plan exists

### Community 157 - "Layer 6: Data (PostgreSQL and private Storage)"
Cohesion: 0.29
Nodes (7): Changes on 2026-11-03, Extending safely, Layer 6: Data (PostgreSQL and private Storage), Migrations, Open gaps, Retention and recovery, Who may reach what

### Community 160 - "purchasing/service.py"
Cohesion: 0.10
Nodes (11): require_admin(), next_number(), adjust(), level_view(), set_reorder_level(), create_order(), cancel(), create() (+3 more)

### Community 161 - "hashlib"
Cohesion: 0.16
Nodes (7): docker(), main(), object_paths(), prepare_scratch(), run(), snapshot(), source_params()

### Community 164 - "receive"
Cohesion: 0.17
Nodes (6): cancel(), create(), purchase_orders(), receive(), PurchaseOrderInput, ReceiveInput

### Community 165 - "database"
Cohesion: 0.15
Nodes (15): database(), operation(), customer_reply(), detail(), intake(), message(), execute(), ownership() (+7 more)

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
Cohesion: 0.22
Nodes (13): three@^0.186.1, familyOf(), FixtureCanvas(), FixtureStage(), FixtureView(), LostPendant(), Pendant(), sputter() (+5 more)

### Community 171 - "Cross-cutting layer: verification and tooling"
Cohesion: 0.40
Nodes (5): Changes on 2026-11-03, Cross-cutting layer: verification and tooling, Open gaps, Test families by layer, The verify gate

### Community 172 - "get"
Cohesion: 0.11
Nodes (8): search(), source_pdf(), events(), stream(), inspect(), workspace(), health(), get()

### Community 173 - "authorize_outbound"
Cohesion: 0.09
Nodes (22): authorize_outbound(), begin(), ready(), Changes on 2026-11-03, Extending safely, Layer 3: Business features, Open gaps, Rules every feature follows (+14 more)

### Community 174 - "fixtureModels.tsx"
Cohesion: 0.29
Nodes (14): BELL, Brass(), Downlight(), Emergency(), FAMILIES, Family, FamilySpec, HighBay() (+6 more)

### Community 189 - "cancel"
Cohesion: 0.19
Nodes (5): cancel(), confirm(), orders(), CancelInput, Stock, order and purchasing records

### Community 191 - "Backend contracts and business transactions"
Cohesion: 0.33
Nodes (6): Admission and repeat submissions, Backend contracts and business transactions, Canonical quotation, exact approval and final dispatch checks, Composition and dependency direction, Failure boundaries and evidence, Surface inventory (reviewed 2026-11-08)

### Community 193 - "accept_media"
Cohesion: 0.20
Nodes (5): accept_audio(), accept_media(), authorize_upload(), admit_upload(), persist_upload()

### Community 194 - "PendantField.tsx"
Cohesion: 0.28
Nodes (8): @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2, layout(), PendantField(), Pendants(), PendantSpec, @react-three/drei, @react-three/fiber

### Community 204 - "FixtureInspector.tsx"
Cohesion: 0.33
Nodes (8): fadeTexture(), FixtureInspector(), InspectedProduct, InspectorModel(), nearestTemperature(), Part, TEMPERATURES, kelvinColour()

### Community 205 - "LightingScene.tsx"
Cohesion: 0.36
Nodes (8): beamFade(), beamGeometry(), CameraDrift(), FlutedWall(), HeadParts, HEADS, LightingScene(), TrackHeads()

### Community 206 - "Google Apps Script integration"
Cohesion: 0.25
Nodes (8): Account setup, Backend contracts and persistence, Evidence limits, Gmail channel (D47), Google Apps Script integration, Local receiver, Source responsibilities, Troubleshooting and verification

### Community 207 - "useScenePlayback"
Cohesion: 0.48
Nodes (5): paperTexture(), RevisionStack(), settle(), Stack(), useScenePlayback()

## Knowledge Gaps
- **1 isolated node(s):** `lumaquote`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2096 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **73 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DomainError` connect `DomainError` to `media_links.py`, `psycopg`, `semantic.py`, `decimal`, `test_whatsapp.py`, `DocumentButton`, `bootstrap.py`, `core/errors.py`, `validate`, `audit`, `re`, `test_stock_acceptance.py`, `prepare`, `purchasing/service.py`, `io`, `database`, `test_stock_ledger.py`, `get`, `authorize_outbound`, `ledger.py`, `media/routes.py`, `stored_quotation_pdf`, `twilio_webhook.py`, `accept_media`, `test_stock_reservations.py`, `inventory/service.py`, `upload_audio`, `worker.py`, `telegram_ingress.py`, `media.py`, `staff`, `rate_limit`, `inbound.py`, `email_dispatch.py`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Are the 59 inferred relationships involving `DomainError` (e.g. with `embed_texts()` and `validate_embedding_provider()`) actually correct?**
  _`DomainError` has 59 INFERRED edges - model-reasoned connections that need verification._
- **What connects `lumaquote` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `psycopg` be split into smaller, more focused modules?**
  _Cohesion score 0.02355378486055777 - nodes in this community are weakly interconnected._
- **Why does `What is stored` connect `check_frontend.cjs` to `audit`, `test_stock_acceptance.py`, `Layer 6: Data (PostgreSQL and private Storage)`, `test_whatsapp.py`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Should `settings` be split into smaller, more focused modules?**
  _Cohesion score 0.0461357625624449 - nodes in this community are weakly interconnected._
- **Should `semantic.py` be split into smaller, more focused modules?**
  _Cohesion score 0.04695304695304695 - nodes in this community are weakly interconnected._