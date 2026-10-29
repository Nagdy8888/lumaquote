# Local Supabase

This project uses an independent Supabase CLI stack named `quotation-local-dev`.
It does not connect to the hosted project or share the existing Smart RAG stack.
Docker must be running. The CLI is pinned in package.json and package-lock.json.

## Services

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
