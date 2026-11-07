# Graph Report - Demo_Project_4  (2026-11-08)

## Corpus Check
- 392 files · ~336,832 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 51 file(s) not represented in the graph (top: .mmd 29, .css 9, .gs 6)

## Summary
- 3948 nodes · 9354 edges · 202 communities (134 shown, 68 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 735 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0adf0c9f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- psycopg
- ProviderError
- semantic.py
- October 29, 2026 - Offline embedding contract tests and engine recovery result
- Retry
- decimal
- frontend/package.json
- test_whatsapp.py
- evaluation_dataset.py
- test_catalog_retrieval.py
- make_draft
- evaluate_scenarios.py
- cn
- scan_secrets.py
- DocumentButton
- bootstrap.py
- Button
- media.py
- clarification_for
- validate
- Overview.tsx
- database
- re
- json
- scripts
- one
- workspace/schemas.py
- FixtureInspector.tsx
- skills.py
- test_stock_acceptance.py
- test_trace_masking.py
- Proposal: working rules, skill routing and documentation (draft for approval)
- prepare
- index.cjs
- submit
- types.ts
- Telegram channel (Bot API, long polling)
- steps
- retention.py
- Design System: LumaQuote
- Frontend ownership, server state and interaction contracts
- ref_node_path
- compilerOptions
- test_stock_ledger.py
- estimated-allowance
- quotation-approval
- Test layers
- Persistent data, privileges and migration lifecycle
- Reservation lifecycle (task T2)
- LumaQuote implementation tracker
- components.json
- Work log
- main
- AppShell.tsx
- whatsapp_client.py
- ledger.py
- check_frontend.cjs
- test_approved_quotation_is_claimed_with_the_exact_canonical_pdf
- package.json
- settings
- manual-workflow.cjs
- begin
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
- test_twilio.py
- backend-modules
- frontend-draft
- verification-scope
- ui-review.cjs
- create_request
- inventory/queries.py
- Local Supabase
- upload_audio
- telegram_ingress.py
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
- Layer 1: Presentation (React staff workspace)
- CLAUDE.md
- Verified OpenAI contracts
- IMPLEMENTATION_PLAN.md
- run
- scripts
- deliver_one
- Proposal: working rules, skill routing and documentation (draft for approval)
- health
- media_links.py
- Apps Script transport and validated commercial snapshots
- accept_customer_text
- calculate
- Email channel (Gmail through Apps Script)
- test_embedding_response_indices_bind_each_vector_to_its_requested_record
- lumaquote
- Tasks
- Development tooling, verification and evidence interpretation
- catalog.test.cjs
- test_surface_inventory.py
- pin
- test_agent_semantic_fallback_preserves_action_and_source_boundaries
- dependency_unavailable
- _assert_no_canaries
- User decisions register
- FakeSession
- Frontend work plan (for Sonnet execution)
- test_agent_on_development_scenario
- check_architecture.py
- Layer 6: Data (PostgreSQL and private Storage)
- test_phone_numbers_are_masked
- test_workspace_reports_only_complete_tenant_mapped_gas_configuration
- create_order
- hashlib
- State
- test_job_trace_exports_graph_and_model_runs_masked
- telegram_check.py
- Layer 5: Core infrastructure
- pull_request_template.md
- Layer 7: External integrations
- LumaQuote by layer
- Showcase shot list (90-120 seconds)
- brain
- Cross-cutting layer: verification and tooling
- Sales workspace direction
- authorize_outbound
- scripts
- conn
- token
- queue_drive_export
- UI_DIRECTION.md
- Backend contracts and business transactions

## God Nodes (most connected - your core abstractions)
1. `DomainError` - 147 edges
2. `October 29, 2026 - Offline embedding contract tests and engine recovery result` - 136 edges
3. `get_detail()` - 96 edges
4. `database()` - 90 edges
5. `settings()` - 88 edges
6. `create_request()` - 84 edges
7. `post()` - 82 edges
8. `make_draft()` - 59 edges
9. `deliver_one()` - 46 edges
10. `react` - 45 edges

## Surprising Connections (you probably didn't know these)
- `Agent fallback and publication recheck` --references--> `ask()`  [INFERRED]
  docs/reference/CATALOG.md → app/agents/luma_agent/nodes/workflow.py
- `Command ownership` --references--> `prepare()`  [INFERRED]
  docs/reference/TOOLING_AND_TESTS.md → app/agents/luma_agent/nodes/workflow.py
- `Two-step approval confirmation` --references--> `review()`  [INFERRED]
  docs/reference/FRONTEND.md → app/agents/luma_agent/nodes/workflow.py
- `Working method` --references--> `job_trace()`  [INFERRED]
  docs/DECISIONS.md → app/agents/luma_agent/observability.py
- `Extending safely` --references--> `rate_limit()`  [INFERRED]
  docs/layers/core.md → app/backend/luma/core/admission.py

## Import Cycles
- None detected.

## Communities (202 total, 68 thin omitted)

### Community 0 - "psycopg"
Cohesion: 0.03
Nodes (50): process_audio(), process_conversation(), claim_job(), finish_job(), process_media(), recover_expired(), tick(), test_free_wording_is_restated_then_yes_prepares_review() (+42 more)

### Community 1 - "ProviderError"
Cohesion: 0.08
Nodes (13): fetch_media(), account_base(), auth(), call(), create_message(), fetch_media(), make_client(), message_sid() (+5 more)

### Community 2 - "semantic.py"
Cohesion: 0.05
Nodes (34): validate_embedding_provider(), retrieve(), query_constraints(), SearchCriteria, candidate_question(), search_catalog(), search(), CatalogHit (+26 more)

### Community 3 - "October 29, 2026 - Offline embedding contract tests and engine recovery result"
Cohesion: 0.02
Nodes (108): 2026-10-29 - Agent fallback boundary tests added, 2026-10-29 - Agent fallback checks passed and evidence consolidated, 2026-10-29 - All Mermaid views rendered locally, 2026-10-29 - Configuration and verification reference coverage, 2026-10-29 — Current workflow documentation and screenshot reviewed, 2026-10-29 — Database gates passed; browser startup assertion failed, 2026-10-29 - Deep agent, media and retrieval references, 2026-10-29 - Deep backend and persistence documentation (+100 more)

### Community 6 - "frontend/package.json"
Cohesion: 0.05
Nodes (55): dependencies, class-variance-authority@^0.7.1, clsx@^2.1.1, cn@^0.4.0, @fontsource/ibm-plex-sans@^5.3.0, @fontsource-variable/space-grotesk@^5.3.0, lucide-react@^1.63.0, radix-ui@^1.8.1 (+47 more)

### Community 7 - "test_whatsapp.py"
Cohesion: 0.13
Nodes (20): conversation_for(), deliver_webhook(), drain(), envelope(), rows(), start(), test_concurrent_duplicate_webhooks_and_workers_process_each_event_once(), test_handshake_requires_the_exact_verify_token_and_full_configuration() (+12 more)

### Community 8 - "evaluation_dataset.py"
Cohesion: 0.04
Nodes (34): Unit and component coverage, 2026-11-02 - Holdout freeze guard (phase 6 preparation, offline), 2026-11-03 - Pre-freeze Recall@5 relabel: 7 to 14 retrieval cases (phase 6, local), catalog_model(), _check_outcome(), _check_retrieval(), _check_structure(), _check_turns() (+26 more)

### Community 9 - "test_catalog_retrieval.py"
Cohesion: 0.19
Nodes (6): search(), test_authoritative_family_is_searchable_when_name_uses_different_words(), test_changed_product_evidence_requires_another_review(), test_description_lookup_retains_original_page_version_and_explicit_specs(), test_exact_sku_precedes_descriptive_similarity(), test_retired_catalog_cannot_be_recommended_or_finalized()

### Community 10 - "make_draft"
Cohesion: 0.10
Nodes (20): Changes on 2026-11-03, Extending safely, Features, Layer 3: Business features, Open gaps, Rules every feature follows, Tests and evidence, 2026-11-02 - Concurrency tests, showcase shot list and screenshots; CI result (+12 more)

### Community 11 - "evaluate_scenarios.py"
Cohesion: 0.05
Nodes (22): 2026-11-02 - Synthetic voice/photo assets, paid development agent run and retrieval bug fix (phase 3), evaluate(), main(), decide(), evaluate(), load_catalog(), main(), run_scenario() (+14 more)

### Community 12 - "cn"
Cohesion: 0.11
Nodes (30): MediaUpload(), cn(), Badge(), badgeVariants, Empty(), EmptyContent(), EmptyDescription(), EmptyHeader() (+22 more)

### Community 13 - "scan_secrets.py"
Cohesion: 0.14
Nodes (9): load_secrets(), main(), run(), scan_files(), tracked_files(), make_repo(), test_clean_repo_reports_no_leaks(), test_only_secret_looking_long_nonpublic_values_are_loaded() (+1 more)

### Community 14 - "DocumentButton"
Cohesion: 0.22
Nodes (14): AudioWaveform(), decodeAudioData(), MediaPreview(), load(), computePeaks(), formatClock(), normalizePeaks(), documentUrl() (+6 more)

### Community 15 - "bootstrap.py"
Cohesion: 0.05
Nodes (23): PhotoReading, digest(), StrictModel, seed_opening(), quotation_pdf(), draft(), DraftInput, Selection (+15 more)

### Community 16 - "Button"
Cohesion: 0.15
Nodes (12): QuotationPanel(), ProductSelections(), QuoteSummary(), ReviewActions(), view(), Product, Button(), buttonVariants (+4 more)

### Community 17 - "media.py"
Cohesion: 0.08
Nodes (15): validate_media_provider(), reserve(), usage_totals(), assert_job(), assert_request_version(), index_company(), run_media(), reconcile_stock() (+7 more)

### Community 18 - "clarification_for"
Cohesion: 0.10
Nodes (14): clarification_for(), has_explicit_lines(), Integration coverage by responsibility, 2026-11-02 - Negative (mutation-style) checks for hostile-content tests, test_provider_failure_and_worker_logs_do_not_leak_canaries(), extracted(), test_duplicate_sku_requires_clarification(), test_empty_placeholder_lines_do_not_suppress_candidate_discovery() (+6 more)

### Community 19 - "validate"
Cohesion: 0.05
Nodes (31): catalog_context(), is_yes(), known_skus(), model_input(), restatement(), safe_reply(), transcript(), unknown_reply() (+23 more)

### Community 20 - "Overview.tsx"
Cohesion: 0.10
Nodes (34): App(), PendantField, SignIn(), CatalogPage(), FixtureCanvas, FixtureInspector, FixtureView, NewRequest() (+26 more)

### Community 21 - "database"
Cohesion: 0.03
Nodes (61): _deliver_local(), enqueue(), rate_limit(), audit(), database(), operation(), membership(), accept_quote_button() (+53 more)

### Community 22 - "re"
Cohesion: 0.10
Nodes (13): degrade(), draw_label(), font(), main(), make_photo(), make_voice(), mix(), noise() (+5 more)

### Community 23 - "json"
Cohesion: 0.04
Nodes (30): inspect_audio(), inspect_image(), inspect_pdf(), main(), bounded_output(), process_file(), `bash` (PreToolUse on Bash, R15), Claude Code hooks (+22 more)

### Community 24 - "scripts"
Cohesion: 0.06
Nodes (36): scripts, build, check:architecture, check:docs, check:frontend, check:rules, check:secrets, db:configure (+28 more)

### Community 25 - "one"
Cohesion: 0.08
Nodes (26): What is stored, Work identities are deliberately different, customer_messages(), jobs(), notices(), one(), quote_status(), refusal_setup() (+18 more)

### Community 26 - "workspace/schemas.py"
Cohesion: 0.08
Nodes (12): ActivityView, CompanyView, ConversationView, DeliveryView, JobView, MessageView, ProductView, QuoteContentView (+4 more)

### Community 27 - "FixtureInspector.tsx"
Cohesion: 0.06
Nodes (72): @react-three/drei@^10.7.9, @react-three/fiber@^9.8.2, three@^0.186.1, fadeTexture(), FixtureInspector(), InspectedProduct, InspectorModel(), nearestTemperature() (+64 more)

### Community 28 - "skills.py"
Cohesion: 0.12
Nodes (13): active_skills(), check_frontmatter(), check_links(), check_manifests(), check_mirror(), check_routing(), digest(), located() (+5 more)

### Community 29 - "test_stock_acceptance.py"
Cohesion: 0.06
Nodes (21): poll_once(), callback(), conn(), telegram_quote(), test_a_button_from_a_user_off_the_allowlist_is_ignored_but_still_answered(), test_callback_answer_failure_is_best_effort_and_logs_only_a_code(), test_callback_updates_reduce_only_when_well_formed(), test_decline_button_releases_the_hold() (+13 more)

### Community 30 - "test_trace_masking.py"
Cohesion: 0.10
Nodes (7): test_business_content_is_kept(), test_disabled_tracing_exports_nothing(), test_media_bytes_and_inline_data_are_omitted(), test_model_call_exports_tokens_and_estimated_cost(), test_production_client_masks_every_exported_field(), test_set_usage_is_a_noop_without_a_run(), test_tracing_is_forced_off_outside_a_job_trace()

### Community 31 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.24
Nodes (7): Code layout, Commands, Documentation (decisions D30, D33), LumaQuote working rules, Rules, Skill routing, Unattended work and accounts

### Community 32 - "prepare"
Cohesion: 0.06
Nodes (40): build_graph(), route(), ask(), clarify(), prepare(), review(), AgentState, Layer 4: Agent worker (+32 more)

### Community 33 - "index.cjs"
Cohesion: 0.15
Nodes (20): crypto, embeddedBlock(), existingFile(), fingerprint(), fs, hash(), path, readCatalog() (+12 more)

### Community 34 - "submit"
Cohesion: 0.33
Nodes (3): answer_buttons(), submit(), adapter()

### Community 35 - "types.ts"
Cohesion: 0.10
Nodes (25): ConversationCommand, EditableLine, draftSuite(), capturesLatestCleanVersion(), preservesConflict(), fixture(), useQuotationDraft(), beginEdit() (+17 more)

### Community 36 - "Telegram channel (Bot API, long polling)"
Cohesion: 0.09
Nodes (15): send_pdf(), send_text(), ProviderError, answer_callback(), call(), fetch_media(), get_updates(), make_client() (+7 more)

### Community 37 - "steps"
Cohesion: 0.09
Nodes (21): VITE_SUPABASE_ANON_KEY, VITE_SUPABASE_URL, jobs, local-contracts, runs-on, steps, timeout-minutes, name (+13 more)

### Community 38 - "retention.py"
Cohesion: 0.07
Nodes (19): delete_files(), Data model, 2026-11-02 - Retention tool and backup/restore drill (phase 5, local only), connect(), expired_media(), idle_conversations(), main(), purge_conversations() (+11 more)

### Community 39 - "Design System: LumaQuote"
Cohesion: 0.10
Nodes (21): Buttons, Cards / Containers, Chips, Colors, Components, Design System: LumaQuote, Do:, Do's and Don'ts (+13 more)

### Community 40 - "Frontend ownership, server state and interaction contracts"
Cohesion: 0.17
Nodes (12): SessionProvider(), Where it lives, Authored, generated and vendor-owned source, Frontend ownership, server state and interaction contracts, Live updates over an authenticated event stream, Mutations and canonical reconciliation, Private documents and temporary capabilities, Quotation editing and conflict preservation (+4 more)

### Community 41 - "ref_node_path"
Cohesion: 0.09
Nodes (16): fs, path, root, { spawnSync }, fs, path, root, { spawnSync } (+8 more)

### Community 42 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, baseUrl, esModuleInterop, jsx, lib, module, moduleResolution (+10 more)

### Community 43 - "test_stock_ledger.py"
Cohesion: 0.10
Nodes (14): main(), conn(), level(), make_quote(), test_invariants_hold_through_a_mixed_sequence(), test_movements_cannot_go_negative_or_below_reserved(), test_queries_report_stock_movements_alerts_and_low_stock(), test_reconcile_is_scoped_by_company_and_batches_levels() (+6 more)

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

### Community 48 - "Reservation lifecycle (task T2)"
Cohesion: 0.11
Nodes (19): held_quantities(), reconcile(), record(), release_hold(), check_snapshot(), 3.4 Freshness at approval and dispatch (task T2), 9. Task list (one Sonnet subagent each, sequential, one commit per task), Approval, freshness and dispatch (+11 more)

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
Cohesion: 0.11
Nodes (24): useConversation(), useWorkspace(), followStream(), reconnectDelay(), encoder, MockStream, renderLive(), signOut (+16 more)

### Community 55 - "whatsapp_client.py"
Cohesion: 0.10
Nodes (17): call(), download(), endpoint(), fetch_media(), GraphError, headers(), make_client(), media_host_allowed() (+9 more)

### Community 56 - "ledger.py"
Cohesion: 0.14
Nodes (11): apply_movement(), convert_quote(), ensure_level(), _held(), _ids(), _line_quantities(), lock_levels(), _move() (+3 more)

### Community 57 - "check_frontend.cjs"
Cohesion: 0.19
Nodes (12): Identity and evidence records, definitionName(), fs, inspect(), walk(), main(), visit(), path (+4 more)

### Community 58 - "test_approved_quotation_is_claimed_with_the_exact_canonical_pdf"
Cohesion: 0.17
Nodes (8): 2026-11-07 - Gmail quotation PDF live test (phase 4, live), conversation_for(), mail(), process(), test_approved_quotation_is_claimed_with_the_exact_canonical_pdf(), test_forged_or_unconfigured_push_is_refused(), test_signed_push_is_stored_once_and_opens_an_email_conversation(), test_unauthenticated_or_unlisted_sender_is_ignored()

### Community 59 - "package.json"
Cohesion: 0.16
Nodes (15): devDependencies, @google/clasp@3.4.1, mermaid@11.17.2, supabase@2.122.0, typescript@5.9.3, typescript, name, overrides (+7 more)

### Community 60 - "settings"
Cohesion: 0.03
Nodes (48): settings(), Settings, domain_error(), get_file(), put_file(), storage_headers(), source_pdf(), allowed() (+40 more)

### Community 61 - "manual-workflow.cjs"
Cohesion: 0.25
Nodes (10): beat(), { chromium, expect }, dispatchFixture(), fs, main(), path, PRIVATE, processMediaFixture() (+2 more)

### Community 62 - "begin"
Cohesion: 0.11
Nodes (16): begin(), block(), live_enabled(), ready(), Actors and authority, Configuration (names only), Database writes and transactions, External effects and secrets (+8 more)

### Community 63 - "ConversationThread.tsx"
Cohesion: 0.11
Nodes (27): AppShell(), navigation, useConversationAction(), ConversationComposer(), ConversationThread(), InboxPage(), JobState(), InboxSection (+19 more)

### Community 64 - "job-recovery"
Cohesion: 0.11
Nodes (18): app/agents/luma_agent/lease.py, app/agents/luma_agent/observability.py, app/agents/luma_agent/runtime/jobs.py, app/backend/luma/features/messaging/inbound.py, job-recovery, worker-tick, bindings, height (+10 more)

### Community 65 - "bindings"
Cohesion: 0.10
Nodes (21): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/agents/luma_agent/graph.py, app/agents/luma_agent/nodes/extraction.py (+13 more)

### Community 66 - "whatsapp-channel"
Cohesion: 0.10
Nodes (20): app/backend/luma/core/config.py, app/backend/luma/features/google_sync/routes.py, app/backend/luma/features/messaging/outbound.py, app/backend/luma/features/messaging/webhook.py, app/backend/luma/features/messaging/whatsapp_client.py, supabase/migrations/20261102010000_whatsapp_inbox.sql, integrations-map, whatsapp-channel (+12 more)

### Community 67 - "LumaQuote"
Cohesion: 0.17
Nodes (11): Accessibility & Inclusion, Brand Commitments, Capabilities and Constraints, Evidence on Hand, LumaQuote, Operating Context, Platform, Product Principles (+3 more)

### Community 68 - "start-local-supabase.cjs"
Cohesion: 0.18
Nodes (10): api(), databaseClients, { execFileSync, spawnSync }, fs, http, names, path, privateDir (+2 more)

### Community 69 - "ExportEnvelope"
Cohesion: 0.07
Nodes (10): ClaimRequest, ExportEnvelope, ReceiptRequest, MailClaim, MailReceipt, MailPush, base_receipt(), test_media_hosts_must_be_meta_owned_https() (+2 more)

### Community 70 - "catalog-retrieval"
Cohesion: 0.18
Nodes (11): app/agents/luma_agent/nodes/workflow.py, app/backend/luma/features/catalog/criteria.py, app/backend/luma/features/catalog/retrieval.py, app/backend/luma/features/catalog/semantic.py, bindings, height, renderer_sha256, source_sha256 (+3 more)

### Community 71 - "fetch_media"
Cohesion: 0.09
Nodes (14): MailItem, reduce_mail(), sender_address(), sender_authenticated(), Sender authentication, item(), test_anything_else_is_unauthenticated(), test_each_passing_mechanism_counts() (+6 more)

### Community 72 - "diagrams"
Cohesion: 0.12
Nodes (15): height, renderer_sha256, source_sha256, svg_sha256, width, diagrams, backend-modules, request-trace (+7 more)

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
Nodes (24): bindings, height, renderer_sha256, source_sha256, svg_sha256, width, app/backend/luma/core/admission.py, app/backend/luma/core/errors.py (+16 more)

### Community 77 - "test_twilio.py"
Cohesion: 0.08
Nodes (17): test_storage_outage_leaves_nothing_half_written_and_recovers(), count_inbox(), inbound(), post_form(), receipt(), sid(), sign(), start() (+9 more)

### Community 78 - "backend-modules"
Cohesion: 0.11
Nodes (21): bindings, app/agents/luma_agent/worker.py, app/backend/luma/features/media/sandbox.py, app/backend/luma/google_gateway.py, app/backend/luma/main.py, scripts/check_architecture.py, scripts/check_frontend.cjs, layer-map (+13 more)

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
Cohesion: 0.03
Nodes (67): Decision needed: failed requests are not rate limited, early_in_minute(), first_denial(), test_approval_limit_is_10_per_minute(), test_catalog_search_limit_is_30_per_minute(), test_customer_messages_are_limited_per_conversation(), test_failed_requests_also_consume_admission(), test_queue_capacity_refuses_work_at_100_with_a_recoverable_503() (+59 more)

### Community 83 - "inventory/queries.py"
Cohesion: 0.19
Nodes (6): low_stock_count(), low_stock_rows(), movements_page(), open_alerts(), stock_rows(), How the rest of the application reads stock

### Community 84 - "Local Supabase"
Cohesion: 0.22
Nodes (9): Conflicts, unavailable infrastructure and evidence, Credentials and application configuration, Local Supabase, Media and worker diagnosis, Native processes and optional provider work, Schema, Semantic index command under development, Services (+1 more)

### Community 86 - "telegram_ingress.py"
Cohesion: 0.19
Nodes (5): poll_telegram(), largest_photo(), reduce_callback(), reduce_update(), Modules and call flow

### Community 87 - "Morning actions"
Cohesion: 0.14
Nodes (14): Evidence limits, Gmail requests (D47), Google callback preparation, Google Workspace / clasp, LangSmith account limit, Latest verification, Local Docker / WSL availability, Morning actions (+6 more)

### Community 88 - "LumaQuote"
Cohesion: 0.25
Nodes (8): Documentation, LumaQuote, LumaQuote request-to-reviewed-offer workflow, Run locally, Status and next actions, Structure, Verification, Workflow at a glance

### Community 89 - "Configuration and native process operation"
Cohesion: 0.29
Nodes (7): Configuration and native process operation, Messaging and Google configuration, Paid AI policy, Private generated files and reproducibility, Safe routine operation, Supabase and database identities, Tracing policy

### Community 90 - "page-review.cjs"
Cohesion: 0.13
Nodes (16): @axe-core/playwright@^4.13.0, @playwright/test@^1.64.1, @axe-core/playwright, @playwright/test, { chromium }, fs, main(), ROUTES (+8 more)

### Community 91 - "telegram_ingress.py"
Cohesion: 0.20
Nodes (4): test_media_link_binds_outbox_id_and_expires(), test_media_link_refuses_without_a_token(), test_signature_matches_twilio_python_vector(), test_url_variants_add_or_remove_the_default_port()

### Community 92 - "LumaQuote architecture"
Cohesion: 0.40
Nodes (5): Agent participation and recovery limits, Code ownership, LumaQuote architecture, Processes and trust boundaries, Semantic retrieval work in progress

### Community 93 - "media.py"
Cohesion: 0.07
Nodes (24): embed_texts(), MediaReading, _read_label(), read_media(), configured_secrets(), finish(), flush(), job_trace() (+16 more)

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
Cohesion: 0.18
Nodes (4): test_accept_phrases(), test_decline_phrases(), test_everything_else_is_ordinary_text(), test_non_text_is_not_an_answer()

### Community 100 - "staff"
Cohesion: 0.17
Nodes (8): staff(), Binary attachment protocol, Command payloads and a review sequence, Errors and limits, Identity and mutation protocol, Regenerating contracts, Staff API reference, Staff identity, idempotency and optimistic mutation protocol

### Community 101 - "order-lifecycle"
Cohesion: 0.18
Nodes (11): app/backend/luma/features/inventory/ledger.py, app/backend/luma/features/orders/acceptance.py, app/backend/luma/features/orders/service.py, supabase/migrations/20261107030000_stock_ledger.sql, order-lifecycle, bindings, height, renderer_sha256 (+3 more)

### Community 102 - "Visual guide to LumaQuote"
Cohesion: 0.33
Nodes (5): Data and runtime, Layer views, Maintaining a view, Visual guide to LumaQuote, Workflow and architecture

### Community 103 - "Project documentation"
Cohesion: 0.50
Nodes (4): Current verification boundaries, Detailed implementation references, Documentation coverage and update ownership, Project documentation

### Community 104 - "DomainError"
Cohesion: 0.05
Nodes (28): DomainError, accept_hint(), EditHint, verify_hint(), verify_mapping(), verify_signature(), claim_export(), drive_filename() (+20 more)

### Community 105 - "rule-enforcement"
Cohesion: 0.17
Nodes (12): .claude/settings.json, scripts/check_docs.py, scripts/hooks/guard.py, scripts/skills.py, scripts/summarize_agent_run.py, rule-enforcement, bindings, height (+4 more)

### Community 106 - "Layer 1: Presentation (React staff workspace)"
Cohesion: 0.33
Nodes (6): Changes on 2026-11-03, Extending safely, Layer 1: Presentation (React staff workspace), Open gaps, Routes, Tests and evidence

### Community 108 - "Verified OpenAI contracts"
Cohesion: 0.67
Nodes (3): Embedding adapter under development, Photo label-reading contract, Verified OpenAI contracts

### Community 110 - "run"
Cohesion: 0.15
Nodes (11): 2026-11-07 - Stock ledger tables and single writer (phase 7, local), reply_texts(), run(), start(), test_model_reads_conversation_and_catalog_without_prices(), test_unknown_sku_is_not_restated_and_yes_then_asks_the_model(), test_unsafe_model_reply_is_replaced_by_the_fixed_question(), test_written_order_matching_the_model_prepares_directly() (+3 more)

### Community 111 - "scripts"
Cohesion: 0.19
Nodes (8): queued_notice(), rows(), script(), Script, test_expired_claim_becomes_unknown_and_is_never_offered_again(), test_failed_receipt_fails_the_outbox(), test_live_switch_off_blocks_before_any_dispatch(), test_reply_is_claimed_once_sent_in_thread_and_recorded()

### Community 114 - "deliver_one"
Cohesion: 0.09
Nodes (16): deliver_one(), test_approved_quotation_is_uploaded_as_the_exact_canonical_pdf(), test_gates_block_without_calling_telegram(), test_text_reply_is_sent_once_without_a_service_window(), test_uncertain_and_failed_sends_are_never_retried(), test_approved_quotation_is_offered_as_the_exact_pdf_behind_a_signed_link(), test_text_reply_is_submitted_once_as_a_twilio_message(), test_uncertain_and_failed_submissions_are_never_retried() (+8 more)

### Community 115 - "Proposal: working rules, skill routing and documentation (draft for approval)"
Cohesion: 0.18
Nodes (11): 1. What went wrong so far (evidence from the work log and this session), 2. Principles, 3. The rulebook (replaces most of AGENTS.md + CLAUDE.md prose), 4.1 Make skills discoverable, 4.2 Consolidate 37 -> about 20 skills, 4.3 One routing table, 4. Skill routing, 5. Documentation: one home per fact (+3 more)

### Community 116 - "health"
Cohesion: 0.18
Nodes (11): Evaluation scoring pin (R11), Failure and recovery, Knowledge graph (decision D33), npm checks, Overview, Rule-to-enforcement map, `scripts/check_docs.py` details, `scripts/skills.py` details (+3 more)

### Community 117 - "media_links.py"
Cohesion: 0.11
Nodes (9): docs_root(), test_r10_ticked_items_need_evidence_and_phase_4_needs_live(), test_r14_stop_requires_work_log_and_docs_for_code(), test_r15_bash_guard(), test_r6_edit_guard_warns_on_large_deletions(), test_r8_flags_mojibake_crlf_and_broken_links_but_not_quoted_code(), test_r9_requires_header_and_allowed_label_for_new_evidence(), test_skills_frontmatter_and_routing() (+1 more)

### Community 118 - "Apps Script transport and validated commercial snapshots"
Cohesion: 0.06
Nodes (28): drive_export_claim(), drive_export_receipt(), google_callback(), signed_body(), supplier_snapshot(), gmail_claim(), gmail_inbound(), gmail_receipt() (+20 more)

### Community 119 - "accept_customer_text"
Cohesion: 0.14
Nodes (15): accept_customer_text(), strip_quoted(), parse_answer(), answer_quote(), refusal_reason(), 4.1 Recognizing the answer, 4.2 Binding rules (code, not AI), 4. Customer acceptance (task T3) (+7 more)

### Community 123 - "calculate"
Cohesion: 0.22
Nodes (4): calculate(), Drafting an immutable offer, test_independently_calculated_discount_and_shipping(), test_integral_minor_unit_totals_remain_exact()

### Community 127 - "Email channel (Gmail through Apps Script)"
Cohesion: 0.11
Nodes (15): queue(), reply_subject(), sweep(), Actors and authority, Configuration (names only), Email channel (Gmail through Apps Script), External effects and secrets, Failures and recovery (+7 more)

### Community 128 - "test_embedding_response_indices_bind_each_vector_to_its_requested_record"
Cohesion: 0.29
Nodes (3): test_embedding_response_indices_bind_each_vector_to_its_requested_record(), create(), unit_vector()

### Community 144 - "Tasks"
Cohesion: 0.29
Nodes (7): F0 - Baseline, branch and worktree, F5 - Explicit approval confirmation (G5), F6 - Portrait inbox with a section switcher (G6), F7 - Capture-mode body masking (G7), F8 - Whole-app visual and accessibility review with evidence (G9), F9 - Close-out, Tasks

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
Cohesion: 0.21
Nodes (5): pin(), run_summarizer(), test_changed_or_missing_pin_is_refused_without_post_hoc(), test_matching_pin_is_scored_normally(), test_post_hoc_flag_labels_the_report()

### Community 150 - "dependency_unavailable"
Cohesion: 0.17
Nodes (11): dependency_unavailable(), response_boundaries(), Layer 2: Transport (staff API and signed gateway), Open gaps, Request pipeline, Status codes a caller should expect, Tests and evidence, The two processes (+3 more)

### Community 151 - "_assert_no_canaries"
Cohesion: 0.19
Nodes (7): _assert_no_canaries(), _job(), test_exception_text_and_error_field_are_masked(), test_metadata_tags_and_job_payload_are_masked(), test_nested_tool_and_subgraph_runs_are_masked(), inner(), lookup_tool()

### Community 152 - "User decisions register"
Cohesion: 0.40
Nodes (5): AI, evaluation and tracing, Integrations, Product and scope, User decisions register, Working method

### Community 154 - "Frontend work plan (for Sonnet execution)"
Cohesion: 0.22
Nodes (8): Acceptance for the whole plan, Branch, pull request and merge (decision D39), Execution protocol for Sonnet (read before every task), Frontend work plan (for Sonnet execution), How to start, Open questions for the user (not blocking any task; use the stated default), Run to completion (user instruction, 2026-11-03), Why this plan exists

### Community 157 - "Layer 6: Data (PostgreSQL and private Storage)"
Cohesion: 0.29
Nodes (7): Changes on 2026-11-03, Extending safely, Layer 6: Data (PostgreSQL and private Storage), Migrations, Open gaps, Retention and recovery, Who may reach what

### Community 161 - "hashlib"
Cohesion: 0.14
Nodes (8): docker(), main(), object_paths(), prepare_scratch(), run(), snapshot(), source_params(), test_every_media_turn_has_a_hashed_asset_and_stays_unconfirmed()

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

### Community 169 - "Showcase shot list (90-120 seconds)"
Cohesion: 0.67
Nodes (3): Not shown (do not demonstrate or claim), Reproducible evidence behind each claim, Showcase shot list (90-120 seconds)

### Community 171 - "Cross-cutting layer: verification and tooling"
Cohesion: 0.40
Nodes (5): Changes on 2026-11-03, Cross-cutting layer: verification and tooling, Open gaps, Test families by layer, The verify gate

### Community 173 - "authorize_outbound"
Cohesion: 0.15
Nodes (12): authorize_outbound(), Who calls what, Actors and authority, Configuration (names only), Data, Failure and recovery, Inbound media, Ingress (+4 more)

### Community 174 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, test, typecheck

### Community 191 - "Backend contracts and business transactions"
Cohesion: 0.29
Nodes (7): Admission and repeat submissions, Backend contracts and business transactions, Canonical quotation, exact approval and final dispatch checks, Composition and dependency direction, Failure boundaries and evidence, Identity, company selection and transactions, Surface inventory (reviewed 2026-11-03)

## Knowledge Gaps
- **1 isolated node(s):** `lumaquote`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1993 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **68 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DomainError` connect `DomainError` to `psycopg`, `test_embedding_response_indices_bind_each_vector_to_its_requested_record`, `semantic.py`, `decimal`, `bootstrap.py`, `media.py`, `validate`, `database`, `json`, `prepare`, `test_stock_ledger.py`, `authorize_outbound`, `Reservation lifecycle (task T2)`, `ledger.py`, `settings`, `create_request`, `telegram_ingress.py`, `media.py`, `staff`, `deliver_one`, `Apps Script transport and validated commercial snapshots`, `calculate`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 58 inferred relationships involving `DomainError` (e.g. with `embed_texts()` and `validate_embedding_provider()`) actually correct?**
  _`DomainError` has 58 INFERRED edges - model-reasoned connections that need verification._
- **What connects `lumaquote` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `psycopg` be split into smaller, more focused modules?**
  _Cohesion score 0.02750647797488539 - nodes in this community are weakly interconnected._
- **Why does `October 29, 2026 - Offline embedding contract tests and engine recovery result` connect `October 29, 2026 - Offline embedding contract tests and engine recovery result` to `semantic.py`, `evaluation_dataset.py`, `make_draft`, `evaluate_scenarios.py`, `DocumentButton`, `clarification_for`, `Overview.tsx`, `dependency_unavailable`, `FixtureInspector.tsx`, `prepare`, `Telegram channel (Bot API, long polling)`, `retention.py`, `Reservation lifecycle (task T2)`, `Work log`, `AppShell.tsx`, `test_approved_quotation_is_claimed_with_the_exact_canonical_pdf`, `queue_drive_export`, `ConversationThread.tsx`, `media.py`, `run`, `accept_customer_text`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Should `ProviderError` be split into smaller, more focused modules?**
  _Cohesion score 0.08258258258258258 - nodes in this community are weakly interconnected._
- **Why does `audit()` connect `database` to `psycopg`, `ProviderError`, `test_job_trace_exports_graph_and_model_runs_masked`, `DomainError`, `DocumentButton`, `bootstrap.py`, `Reservation lifecycle (task T2)`, `media.py`, `deliver_one`, `AppShell.tsx`, `accept_customer_text`, `ledger.py`, `one`, `begin`, `Email channel (Gmail through Apps Script)`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._