# Google Apps Script integration

This folder is the single source managed by the root `.clasp.json` mapping.
Use `npm run google:status` and `npm run google:push` from the repository root.
After adding files, verify a remote pull; a skipped upload is not evidence of a
successful upload. No Google Cloud Console or backend Google OAuth setup is needed.

The [backend synchronization reference](../docs/reference/GOOGLE_SYNC.md) details
exact envelopes, signature/mapping/replay checks, whole-table validation,
transactional publication and freshness semantics. The [data model](../docs/reference/DATA_MODEL.md)
explains receipt/snapshot ownership and grants. This file remains the clasp/account
setup guide so operating instructions have one primary home.

## Source responsibilities

- `appsscript.json`: V8 runtime, Cairo timezone, Sheets, Drive, trigger and HTTP scopes.
  The Drive scope was added for `Exports.gs`; re-authorize the script after pushing it.
- `Scheduler.gs`: the one time-driven trigger `runLumaMinute` (D50), the lock helper used by the manual
  entry points, and the installer `installLumaMinute` (see "Trigger model" below).
- `Exports.gs`: polls the backend for approved quotation PDFs, files each in the private
  folder, reads the copy back and reports its SHA-256 (protocol in
  [Google synchronization](../docs/reference/GOOGLE_SYNC.md)).
- `Stock.gs`: stock export (D49). When a staff member presses Export to Google Sheets, the
  minute run (`runLumaMinute`, the export task) claims the export and writes only the `Stock`,
  `Customer Orders` and `Purchase Orders` tabs (plain-text format first, so nothing is evaluated as a
  formula), then posts a receipt with row counts. It never touches Products, Prices, Policies,
  Inventory or Quote Register. `installStockExport` installs the minute trigger without a Drive folder.
- `Configuration.gs`: required Script Properties, HTTPS callback destination,
  and SHA-256 HMAC signing of exact UTF-8 request bytes.
- `Workbook.gs`: non-destructive synthetic initializer and safe workbook/tab
  diagnostics through `inspectSupplierWorkbook`.
- `Notifications.gs`: owned manual-edit trigger, signed invalidation and editor
  test. The updated handler also attempts a full snapshot after notification.
- `Synchronization.gs`: bounded table capture, stable-read checks and signed full
  snapshots (the reconciliation task of the minute run).

The workbook is authoritative for commercial inputs. The ingested catalog remains
the evidence authority for supported product specifications. Backend validated
snapshots are synchronized observations, not independent editable price lists.
The Quote Register tab is initialized with headers; automatic register writes are
not implemented. Initializer completion preserves existing populated tabs and
does not by itself prove the intended workbook was filled.

## Trigger model (D50)

Exactly one time-driven trigger exists: `runLumaMinute`, every minute. It takes the script lock once with a
1 s `tryLock` and, if the previous run still holds it, skips that minute without an error. Otherwise it
runs these tasks in order, each in its own try/catch (one failure never skips the rest; the first error is
rethrown at the end so the run shows as Failed):

1. `pollLumaMail_` - push new Gmail messages (customer replies first).
2. `sendLumaMail_` - claim and send up to three queued replies.
3. `synchronizeSupplierWorkbook_` - push one signed Products/Prices/Policies snapshot.
4. `exportApprovedQuotations_` - Drive PDFs (only with `LUMA_DRIVE_FOLDER_ID`), then one stock export.

No new task starts after 4.5 minutes (`MINUTE_BUDGET_MS`) of Apps Script's 6-minute execution limit; skipped
task names are logged as a warning. The on-edit trigger `notifySupplierEdit` is separate and unchanged.

The public task names (`pollLumaMail`, `sendLumaMail`, `synchronizeSupplierWorkbook`,
`exportApprovedQuotations`) remain as **manual entry points** for running one task by hand in the editor: each
takes the script lock itself (waits up to 25 s) and calls the lock-free task above. Do not install them as
triggers. `installLumaMinute` deletes every project trigger whose handler is `runLumaMinute` or one of those
four names and creates the one `runLumaMinute` trigger; `installSupplierSynchronization`, `installDriveExport`,
`installStockExport` and `installLumaMail` call it, so no path recreates parallel triggers. After pushing
this change, run `installLumaMinute` once and check the Triggers page: one time-driven `runLumaMinute` plus
the on-edit `notifySupplierEdit`.

## Account setup

Script Properties: `LUMA_SPREADSHEET_ID`, `LUMA_COMPANY_ID`,
`LUMA_CALLBACK_URL`, `LUMA_CALLBACK_SECRET`. The ignored private setup file
contains this machine's callback values. Never put the secret in source or chat.

1. Run `initializeSyntheticWorkbook` for an empty dedicated synthetic workbook.
2. Run `installSupplierEditTrigger` and `verifySupplierCallback`.
3. Run `installSupplierSynchronization`. It sends an initial complete snapshot
   and installs the single one-minute trigger (`installLumaMinute`). The initial snapshot needs the script
   lock; if the minute run holds it for longer than 25 s, run it again.
4. Stock is owned by the web app (D49): the `Inventory` tab is no longer read or watched, and an
   edit to it changes nothing. Edit Prices instead to see a fresh sync observation.
5. For Drive copies: create a private Drive folder, set Script Property
   `LUMA_DRIVE_FOLDER_ID` to its id, run `installDriveExport` (it asks for the new Drive
   permission and installs the single minute trigger). Do not share the folder publicly.

The backend validates exact headers, unique/matching SKU sets, catalog-backed
specifications, USD decimal prices, effective dates, stock, pack size and approved
policies before atomically updating records. New SKUs/specification changes require
catalog evidence ingestion first. Unknown columns, formulas, missing rows and
conflicting policies are rejected. A 202 edit hint alone is not an imported snapshot.

Timer pushes cover API edits that do not fire manual edit triggers. Google schedules
timers approximately, so stale evidence must still block finalization. Failed pushes
are retried with a fresh full read by the next timer; they never refresh backend
freshness. The script lock coordinates this script (the minute run, manual runs and the
edit handler), not human/API writers. Double
reads detect changes during capture but cannot provide an atomic multi-tab Sheets
transaction; avoid simultaneous multi-tab administrative updates during import.

## Gmail channel (D47)

`Mail.gs` reads only mails under one Gmail label and sends the replies the backend queues. Setup:

1. In Gmail, create the label `LumaQuote` and a filter that applies it to customer requests, for
   example mails sent to `your.address+quotes@gmail.com`. A different label name goes in the Script
   Property `LUMA_GMAIL_LABEL`.
2. Push the project (the manifest now includes the `https://mail.google.com/` scope), run
   `installLumaMail` (or `installLumaMinute`) once and approve the new Gmail permission.
3. Test from a different address than the script's account: the script skips its own messages.
   With only one account, run `enableMailSelfTest` (accepts own mails sent to the `+quotes` alias)
   and `disableMailSelfTest` afterwards.

The manifest also needs `userinfo.email` so `Session.getEffectiveUser()` can return the account
address; approve both new permissions when the editor asks.

`pollLumaMail` finds threads by `label:<LumaQuote> newer_than:8d` and filters messages newer than its
cursor in code, because the filter labels only the first mail and a customer reply to the plain shop
address carries no label (see [how threads are found](../docs/reference/EMAIL.md#how-threads-are-found-fix-of-2026-11-11)).

The poll and send tasks run every minute inside `runLumaMinute`. Status codes only are kept in
`LUMA_LAST_MAIL_STATUS` and `LUMA_LAST_MAIL_SEND_STATUS`. See
[email channel](../docs/reference/EMAIL.md).

## Local receiver

`node scripts/python.cjs -m uvicorn luma.google_gateway:app --host 127.0.0.1 --port 8002 --no-access-log`

`ngrok http 8002 --inspect=false`

Only callback routes are exposed by this gateway. The tunnel must stay running;
update the callback property if its HTTPS address changes. GAS can access Sheets
using the authorizing Google account; it does not forward Google tokens to the backend.

## Backend contracts and persistence

Stock export (D49): `POST /callbacks/google/stock/claim` and `/callbacks/google/stock/receipt` use the
same signed envelope; see [Inventory](../docs/reference/INVENTORY.md). After pushing `Stock.gs`, run
`installLumaMinute` once (`installStockExport` and `installDriveExport` call it) and approve any new
permission. Push is a live step: `npm run google:push`.

Both snapshot routes require `X-Luma-Signature`: lowercase SHA-256 HMAC hex over the exact
request body with the shared secret. Version 1 envelopes carry company/workbook
mapping, timestamp, UUID nonce and event. Timestamp acceptance is five minutes;
snapshots additionally reject observations over five seconds in the future.

- `POST /callbacks/google`: `supplier_records_changed`, at most 4096 bytes.
  A 202 response means durable invalidation receipt, with `sync_status: pending`.
  At most 120 new receipts per company per minute are admitted.
- `POST /callbacks/google/snapshot`: `supplier_snapshot`, at most 512 KiB.
  Includes Products, Prices and Policies; an old `Inventory` list is accepted and ignored. A 202 response distinguishes
  `validated` from `duplicate`. At most 30 new snapshots per company per minute
  are admitted. Older/equal observations with new nonces are rejected.

Identical nonce/body retries have one effect; nonce reuse with different bytes is
a conflict. Authentication/mapping errors return 401/403, schema/domain rejection
422, conflicts 409, body limits 413, rate limits 429, and unavailable configuration
or database storage 503. Database transactions serialize imports per company and
acknowledge only after commit. Replay receipts are pruned after ten minutes on
accepted callback traffic. No background retention sweep is claimed.

The `google_sync` backend feature owns routes, signing checks, schemas, validation
and imports. `luma.google_gateway` composes only callback routes; it does not expose
staff APIs or documentation endpoints. The callback router is not mounted in the
normal staff application. Migrations `20261029120100_google_edit_receipts.sql` and
`20261029123000_gas_snapshots.sql` add worker-only receipt/signal/state tables with
RLS; browser and staff API roles have no direct table access.

`google_edit_receipts` and `google_refresh_signals` record invalidation;
`google_snapshot_receipts` deduplicates snapshot requests; `google_sync_state`
stores the latest validated observation and source tables. Unchanged normalized
data keeps its snapshot ID and refreshes observation time. Changed commercial data
gets a new snapshot ID while preserving product/catalog identities and stored
quotation revisions. Retained inventory locations/effective dates are in the
source tables; the current product projection stores available quantity and price.

## Troubleshooting and verification

If the editor file list is empty, verify the linked project and `clasp status`.
In this chat, a normal push reported `Skipping push` while a separate remote pull
contained only the hidden manifest. A deliberate `clasp push --force` restored the
four source files; an independent pull proved they arrived. This is clasp source
upload, not a Git force-push. Inspect the intended mapping and remote state before
overwriting source. After later additions, refresh the editor and select the
relevant file to see its functions. The current project has five uploaded files.

The execution API returned application-level `USER_ERROR / NOT_FOUND` even with
clasp exit code zero. `scripts/google.cjs` checks the JSON error and does not count
that as execution success. Editor runs and source uploads are separate capabilities;
GAS-only push integration does not require repairing execution-API access.

Run locally from the repository root:

```powershell
npm run check:architecture
node scripts/python.cjs -m ruff check app/backend/luma/features/google_sync app/backend/luma/google_gateway.py tests/integration/test_google_callback.py tests/integration/test_gas_snapshots.py
node scripts/python.cjs -m pytest tests/integration/test_google_callback.py tests/integration/test_gas_snapshots.py -q --tb=short
Get-Content gas/Configuration.gs,gas/Notifications.gs,gas/Synchronization.gs,gas/Workbook.gs,gas/Exports.gs,gas/Stock.gs,gas/Mail.gs,gas/Scheduler.gs | node --check
```

These checks cover Python structure/contracts, lint, HTTP/database behavior and GAS
syntax. They do not execute GAS services inside Google or prove timer installation.
See [progress evidence](../docs/evidence/google-gas-progress.json) and
[remaining account steps](../docs/MORNING_ACTIONS.md).

## Evidence limits

Edit-trigger delivery is live verified. Full snapshot import is locally verified;
its live editor/timer runs are pending. Drive export is implemented in `Exports.gs` and
the backend protocol is locally tested with a Python stand-in (digest identity, replay,
lease and retry), but the script has not run in Google and no Drive file was created. It
uses GAS authorization and a private configured folder, not backend OAuth or public sharing. No WhatsApp delivery or whole-phase completion is claimed.
