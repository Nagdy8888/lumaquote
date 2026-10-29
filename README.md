# LumaQuote

A commercial-lighting supplier's sales workspace: customer requests, catalog
evidence, accurate quotations, and a salesperson's decision before delivery.

English interface and fictional supplier records. Business impact is a pilot
hypothesis, not a claim about an existing client.

## Run locally

Requires Node 20.20+ (CI uses Node 22), Python 3.12, and Docker Desktop for local
Supabase and the isolated file processor. UI, API, worker, and tests run natively.

```powershell
npm ci
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.lock.txt
npm run db:start
npm run db:configure
npm run setup
npm run media:build
```

Open separate terminals for the native processes:

```powershell
npm run dev:api
npm run dev:ui
npm run dev:worker
```

Visit http://127.0.0.1:5173. Local setup puts the generated staff credentials in
ignored `.local/staff-access.json`. The root `.env` holds provider credentials;
`.env.local` overrides local connection settings. Never commit either.
Restart the API after backend edits; automatic reload is deliberately not enabled
in the Windows command wrapper. Stop Supabase with `npm run db:stop`; data remains.

## Structure

- `app/backend/luma/core`: shared infrastructure and request boundaries.
- `app/backend/luma/features`: conversations, catalog, quotations, media, and workspace.
- `app/frontend/src/app`: application composition; features own their UI and queries.
- `app/frontend/src/shared`: documented UI primitives, Auth, and generated API contracts.
- `app/agents/luma_agent`: graph state, individual nodes, budget/lease controls, and native worker.
- `app/backend/integrations/apps-script`: versioned Google Apps Script source, managed with clasp.
- `supabase/migrations`, `tests`, and `docs`: schema, verification, and project evidence.

Every authored function/class has an inline contract. Checks enforce documentation
and import direction; feature organization avoids a global business-logic file.

## Verification

```powershell
npm run lint:python
npm run check:architecture
npm run check:frontend
npm run typecheck
npm run test:unit
npm run test:ui
npm run test:python
npm run build
```

`test:python` includes real local Auth/PostgreSQL/Storage and media-container tests.
It creates isolated synthetic tenants and does not reset the developer database.
The GitHub workflow runs unit/component/static/build checks; it does not claim
those external or Docker-backed integration checks passed remotely.

OpenAI calls are disabled by default until intentionally enabled. Local exact-SKU
preparation is a labeled offline baseline, not evidence of live model behavior.
Usage amounts are estimates/reservations, never provider invoices.

## Status and next actions

Read the [implementation tracker](docs/IMPLEMENTATION_PLAN.md),
[testing plan](docs/TESTING_PLAN.md), [morning actions](docs/MORNING_ACTIONS.md),
[local database details](LOCAL_DEVELOPMENT.md), and [visual system](DESIGN.md).
Configuration, local tests, live provider calls, and client validation are reported
separately. This project is not yet a production release.

The private source repository is https://github.com/Nagdy8888/lumaquote.
Completed phases are committed and pushed after their checks and review.
