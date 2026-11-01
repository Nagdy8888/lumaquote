# Local Supabase

This project uses an independent Supabase CLI stack named `quotation-local-dev`.
It does not connect to the hosted project or share the existing Smart RAG stack.
Docker must be running. The CLI is pinned in package.json and package-lock.json.

For the full variable/default/precedence inventory and native process boundaries,
read [configuration and operation](docs/reference/CONFIGURATION.md). For stateful
failure diagnosis, read [agent recovery](docs/reference/AGENT_RUNTIME.md) and
[media processing](docs/reference/MEDIA.md); those guides explain why a retry may
be unsafe rather than only listing startup commands.

## Services

Documentation diagrams use the pinned development-only Mermaid dependency and
the existing Playwright Chromium (`npx playwright install chromium` if missing).
See [the diagram maintenance guide](docs/diagrams/README.md) for render/check
commands. No additional Docker service or paid provider is required.

- API, Auth, and Storage gateway: http://127.0.0.1:55321
- PostgreSQL: 127.0.0.1:55322
- Supabase Studio: http://127.0.0.1:55323
- Local test-email inbox: http://127.0.0.1:55324

Realtime, Analytics, the connection pooler, and Edge Runtime are disabled for now.
API, UI, and worker run natively with `npm run dev:api`, `npm run dev:ui`, and
`npm run dev:worker`; Docker is limited to Supabase and constrained media decoding.

## Start and stop

Run `npm ci` to install the pinned CLI on a fresh checkout.
Start the local stack:

```powershell
npm run db:start
```

Use `npm run db:stop` to stop this project's stack while preserving local data.
Do not use reset, destroy, volume deletion, or stop --no-backup as routine shutdown.
Existing project volumes are distinct from Smart RAG's volumes.

The start helper creates the dedicated loopback network if needed and checks
published ports. On Docker Desktop versions that ignore the network's binding
default, it recreates only this project's four published containers with explicit
127.0.0.1 bindings, preserving their named volumes and configuration. It waits for
healthy services. Private restore configurations and CLI output stay under ignored
supabase/.temp/. No other project's containers are changed.

## Credentials and application configuration

Provider keys remain in the user's existing ignored `.env`.
Local Supabase settings are stored in ignored `.env.local`; backend development
configuration must load `.env` followed by `.env.local`. Vite loads the local
override and exposes only variables prefixed with `VITE_`.
Never prefix database URLs, provider keys, or service-role credentials with VITE_.
`npm run db:status` displays local keys, so do not paste its full output into chat.

Studio's optional OpenAI integration is disabled. Installing/starting Supabase
does not call OpenAI or LangSmith and does not establish either API connection.

## Schema

Versioned migrations live in `supabase/migrations/`. The initial migration enables
pgvector under the extensions schema. Business tables, staff membership/RLS,
private Storage, immutable quotation content, and linked voice-media records are
implemented by subsequent versioned migrations. Run `npm run setup` to apply them
and provision this local project idempotently.
No hosted migration, production deployment, or application readiness is implied.

## Native processes and optional provider work

Follow the root [README setup commands](README.md#run-locally) for the virtual
environment, locked dependencies, generated local configuration and media image.
Start API, UI and worker in separate terminals. The API is on loopback port 8001;
Vite is on 5173 and proxies `/api` to it. Restart a native process after changing
its environment or backend code. The Windows wrapper deliberately omits reload.

`ENABLE_PAID_AI` defaults to false. With it disabled, exact-SKU preparation is an
offline baseline and normalized media stays available for manual staff review.
When intentionally enabled, fixed configured OpenAI models may consume reserved
estimated allowance. The worker must be running to process uploads or dispatch
local intents. `ENABLE_LIVE_WHATSAPP` alone does not establish an adapter or
authorized Meta connection.

The initial allowance policy is estimated USD 25 total, USD 5/day and USD 0.25
reservation/run. Unresolved reservations continue to count across UTC midnight;
unknown provider outcomes do not free allowance automatically. These are internal
estimates, not invoice totals or a provider-enforced billing guarantee.

## Media and worker diagnosis

- **Upload remains queued:** check the native worker and Docker engine. Processing
  uses `lumaquote-media:local`; rebuild it with `npm run media:build` after changing
  the sandbox processor or image dependencies. Do not turn parsing into unrestricted
  host execution to bypass a Docker failure.
- **Paid AI disabled:** staff can listen/view a successfully normalized attachment
  and continue with text. This state is expected, not a failed live integration.
- **Rejected attachment:** actual type/content/duration/resource validation failed.
  Ask for a supported smaller recording/photo or text. Changing an extension is
  not a repair.
- **Unknown provider outcome:** retain the reservation and review the durable
  media/job state. The current app has no general reconciliation/retry UI. Do not
  reset database rows or submit a fresh paid job blindly; staff can ask for text.
- **Interrupted active job:** a later claim reconciles at most 100 expired leases,
  fences/fails them, retains reserved usage as unknown and exposes pending media
  interruption to staff. Locked transactions are skipped. Work is not replayed;
  inspect the internal recovery message/audit and continue manually. Heartbeats
  and a general retry/reconciliation UI remain unfinished. Paused LangGraph
  restart/resume has separate tests and does not prove an active provider was cancelled.
- **LangSmith unavailable:** optional trace failure does not stop quotation work.
  The observed monthly account quota rejection is recorded in morning actions;
  no successful export or quota increase is claimed.

Runtime media states are `queued`, `processing`, `ready`, `needs_staff`, `rejected`
and `unknown`. Ready means a reading is available, not that its fields or a quote
are approved. The API returns normalized WAV/JPEG only after current authorization.
An interrupted private upload before database commit may leave an orphan object;
retention/orphan cleanup is still a planned safeguard, not an implemented promise.

## Conflicts, unavailable infrastructure and evidence

A 409 mutation keeps the local draft visible. Refresh/review the canonical state
and explicitly discard/rebuild edits where appropriate; never bypass the expected
version or approve an old revision. Database/admission failures must fail closed.
Do not replace unavailable shared enforcement with a browser-only cooldown.

If Auth fails immediately after a cold Docker start, use the project's start
helper and inspect readiness. It rebinds only this project's published containers
and reconnects its dependent services when the database container changes.
Preserve volumes; routine diagnosis does not authorize reset or deletion.

`npm run verify:full` writes private command logs and a summary under
`.local/checks`. Read the failing log before changing code. The paid provider
canaries in `tests/integration/test_live_*.py` are skipped unless their explicit
opt-in variable is set; routine tests do not enable paid calls. Browser tests own
temporary native servers and isolated synthetic tenants. No test should reset
the developer's supplier or another project's data.

Use synthetic data for public capture. Current capture controls do not establish
complete message/PDF redaction or production privacy readiness. Retention,
backup/restore, public deployment and the full engineering ledger remain later
verification gates. See [architecture](docs/ARCHITECTURE.md),
[sales workflows](docs/WORKFLOWS.md) and [API reference](docs/api/README.md).

## Semantic index command under development

The working-tree `scripts/index_catalog.py` command requires `--company <UUID>`,
`--run-id <stable-UUID>` and `--execute`, through `node scripts/python.cjs`.
It is an explicit paid operation, restricted to an explicitly synthetic supplier
on this project's local database. It is not called by setup or ordinary tests.
The embedding migration and targeted SQL tests have passed. Live indexing remains
an explicit paid operation; routine verification uses deterministic vectors.

A prior reserved/unknown index operation blocks another batch until reconciliation.
Preserve its run ID; do not generate a new identity to bypass that state. Publication
checks source/version/page/content again after the provider call and aborts if the
catalog changed. Raw catalog text excludes prices, inventory and customer data.
The provider estimate is recorded separately from actual billing, which has not
been retrieved. A three-record synthetic live index/query canary passed; this
does not establish recall quality. It is skipped by default and can be explicitly
enabled with `LUMA_RUN_LIVE_EMBEDDINGS=1` for
`node scripts/python.cjs -m pytest tests/integration/test_live_embeddings.py -q`.
