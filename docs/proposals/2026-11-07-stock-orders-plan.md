# Stock, customer orders and supplier purchasing: implementation plan

Date: 2026-11-07. Decision: [D49](../DECISIONS.md). Branch: `feat/stock-orders` (from `origin/main` 7db6163).
Author: Claude Opus (plan and orchestration). Implementers: Claude Sonnet subagents, one task each, in order.

## 1. Problem

The agent drafts and sends quotations, but the shop cannot see or control its stock:

- Stock is a number per SKU (`luma.products.available`) that the Google Sheet `Inventory` tab
  overwrites about once a minute (`google_sync/snapshots.py`).
- Nothing ever moves stock. Quotations do not reserve it (`stock_reserved: false`), there is no
  "customer accepted" step, no order record and no supplier purchase record.
- The `Quote Register` tab in the Sheet is created but never written.
- A shortage only escalates the conversation (`nodes/workflow.py` `prepare`) with a generic system line.

## 2. Actors and authority

| Actor | Can do | Cannot do |
|---|---|---|
| Customer (Telegram, Gmail, WhatsApp) | Accept or decline the latest sent, valid quotation of their own chat | Accept another chat's quote, an old revision, an expired quote; change price or quantity by accepting |
| Agent / worker | Detect accept/decline with code (no AI), create a pending order, hold and release reservations, raise shortage alerts | Confirm an order, change on-hand stock, create purchase orders |
| Salesperson | Confirm or cancel customer orders, acknowledge alerts, download Excel, request a Google Sheets export | Purchase orders, receipts, stock adjustments, reorder levels |
| Admin | Everything a salesperson can, plus purchase orders, receipts, adjustments (reason required), reorder levels | Make on-hand lower than reserved |
| Apps Script (GAS) | Pull signed stock export rows and write the Stock, Customer Orders and Purchase Orders tabs | Read anything else, change stock, approve or send |

Authorization is deterministic code at the route and service layer (R5). Roles come from
`luma.memberships.role` (`admin`, `salesperson`).

## 3. Stock model

### 3.1 Tables (one migration, task T1)

All tables: `company_id` scoping, composite FKs to `(company_id, id)` like existing tables, RLS
`staff_scope` / `worker_scope` exactly as in `20261029010000_quotation_domain.sql`, explicit grants.

- `luma.stock_levels(company_id, product_id pk-part, on_hand int >= 0, reserved int >= 0,
  reorder_level int >= 0 default 20, updated_at)`; `check (reserved <= on_hand)`; primary key
  `(company_id, product_id)`. Available = `on_hand - reserved` (never stored).
- `luma.stock_movements(id, company_id, product_id, delta int <> 0, kind in ('opening','adjustment',
  'receipt','order','order_cancel'), reference_id uuid null, reason text null (required for
  adjustment, 3-200 chars), actor text, created_at)`. Append-only: grant `select, insert` only.
  Invariant: `stock_levels.on_hand = sum(delta)` per product.
- `luma.stock_reservations(id, company_id, quote_id, product_id, quantity int > 0, status in
  ('held','released','converted'), release_reason text null, created_at, closed_at)`;
  `unique(quote_id, product_id)`. Invariant: `stock_levels.reserved = sum(quantity where held)`.
- `luma.orders(id, company_id, number text unique per company ('SO-0001'), conversation_id, quote_id
  unique, revision, status in ('pending','confirmed','cancelled'), accepted_via in
  ('telegram_button','reply','staff'), accepted_at, confirmed_by uuid null, confirmed_at,
  cancelled_by uuid null, cancelled_at, cancel_reason text null, currency, total numeric(12,2),
  customer_name, customer_company, created_at)`.
- `luma.order_lines(order_id, company_id, product_id, sku, name, quantity, unit_price, line_total)`
  copied from the accepted immutable quote content (prices never recomputed).
- `luma.purchase_orders(id, company_id, number ('PO-0001'), supplier text 1-120, status in
  ('ordered','partially_received','received','cancelled'), expected_on date null, notes text null
  (<= 500), created_by, created_at, updated_at)`.
- `luma.purchase_order_lines(id, company_id, purchase_order_id, product_id, quantity_ordered int > 0,
  quantity_received int >= 0 default 0, unit_cost numeric(12,2) >= 0)`;
  `check (quantity_received <= quantity_ordered)`; `unique(purchase_order_id, product_id)`.
- `luma.stock_alerts(id, company_id, kind in ('shortage','acceptance_refused'), product_id null,
  conversation_id null, quote_id null, requested int null, available int null, status in
  ('open','acknowledged'), acknowledged_by uuid null, created_at, acknowledged_at)`.
  Low-stock alerts are **not** stored; they are a live query (`available <= reorder_level`).
- `luma.sheet_exports(id, company_id, status in ('queued','claimed','done','failed'), requested_by,
  claim_token uuid null, lease_until, row_counts jsonb null, error_code text null, created_at,
  completed_at)`; at most one `queued`/`claimed` row per company (partial unique index).
- `luma.document_counters(company_id, kind in ('order','purchase_order'), next_value int)` for
  gap-tolerant, lock-serialized numbering.
- `luma.quotes.status` check gains `'accepted'` and `'declined'`.
- Backfill: one `stock_levels` row and one `opening` movement per product from the current
  `products.available`; then `alter table luma.products drop column available`. The local
  database is the only database (D06), so the destructive column drop is acceptable; the migration
  test must prove backfill equality before the drop.

### 3.2 Single writer

New feature package `app/backend/luma/features/inventory/`:

- `ledger.py` is the **only** code that writes `stock_levels`, `stock_movements` and
  `stock_reservations`. Functions (all take the caller's open transaction):
  - `lock_levels(conn, company, product_ids)` -> rows `for update`, always in sorted product-id
    order (deadlock rule), creating no rows.
  - `apply_movement(conn, company, product_id, delta, kind, actor, reference_id=None, reason=None)`;
    refuses a result where `on_hand < reserved` or `on_hand < 0` (`DomainError` 409).
  - `reserve_quote(conn, company, quote)` -> locks levels, checks `available >= quantity` for every
    line, inserts `held` reservations, raises reserved. All-or-nothing; idempotent on
    `(quote_id, product_id)`.
  - `release_quote(conn, company, quote_id, reason)` -> held -> released, lowers reserved. Idempotent.
  - `convert_quote(conn, company, quote_id, order_id, actor)` -> held -> converted, lowers reserved
    and writes `order` movements (negative delta) in one step.
  - `reconcile(conn, company=None)` -> releases held reservations whose quote is not
    `approved`/`accepted`, whose approved quote has expired (`valid_until <= now()`; also marks the
    quote `expired`), or whose quotation outbox row is `blocked` or `failed`. A reservation of an
    `accepted` quote with a `pending` order is kept until staff confirm or cancel. Never touches
    `unknown` deliveries (they may have reached the customer).
- `queries.py`: stock table rows (sku, name, family, on_hand, reserved, available, reorder_level,
  low flag), movements page, open alerts, low-stock count.

### 3.3 Readers that change (task T1)

Every reader of `products.available` switches to `stock_levels` (join on `company_id, product_id`):
`quotations/drafting.py`, `quotations/rules.py` (`line["available"]` now comes from the join),
`quotations/freshness.py`, `agents/luma_agent/nodes/workflow.py` (`prepare`),
`catalog/*` and `workspace/queries.py` + `workspace/schemas.py` (catalog payload keeps an
`available` field so the UI contract stays), `google_sync/snapshots.py` (stops writing stock).
Search the tree for `available` before finishing (`grep -rn "available" app/ tests/`).

### 3.4 Freshness at approval and dispatch (task T2)

- Approval (`quotations/approval.py` `decide`): after `check_snapshot`, call
  `ledger.reserve_quote` in the same transaction. Not enough stock -> `DomainError("Stock changed.
  Create a new revision.", 409)`, nothing written. Lock order: conversation -> quote -> stock levels.
- `check_snapshot` no longer compares `available >= quantity` for an already-approved quote
  (its own reservation lowered available). At dispatch it instead requires that every line has a
  `held` reservation for this quote. At approval time it checks `available >= quantity` as before
  (before the reservation exists).
- Release hooks call `ledger.release_quote` directly: customer revision supersede in
  `conversations/participation.py` `accept_customer_text`, `outbound.block`, failed outcome in
  `outbound.record`, the `dispatch_revalidation` / `live_adapter_not_enabled` branches in
  `runtime/delivery.py`, decline, order cancel. `ledger.reconcile` runs once per worker tick
  (`worker.py`) as the safety net for anything missed (takeover-blocked sends, expiry).

## 4. Customer acceptance (task T3)

### 4.1 Recognizing the answer

New module `app/backend/luma/features/orders/acceptance.py`:

- `parse_answer(text) -> 'accept' | 'decline' | None`. Normalize: lowercase, trim, collapse
  spaces, strip trailing `.`/`!`. Whole message must equal one phrase (max 40 characters):
  accept = `accept`, `i accept`, `accepted`, `yes i accept`, `yes, i accept`, `accept quotation`,
  `accept the quotation`, `i accept the quotation`; decline = `decline`, `i decline`, `declined`,
  `reject`, `no thanks`, `decline quotation`. Plain `yes` is **not** an acceptance (D46 uses YES to
  confirm an order restatement). Anything else is ordinary text and keeps today's behavior
  (supersede and re-quote). Unit-tested with a table of positive and negative cases.

### 4.2 Binding rules (code, not AI)

`orders/service.py` `answer_quote(conn, company, current, answer, via, quote_id=None, provider_id=None)`:

1. The target is the newest quote of this conversation with `status='approved'`, whose quotation
   outbox row is `submitted`, `delivered`, `read` or `local_delivered`, `valid_until > now()`, and
   `recipient == conversation.recipient`. If `quote_id` is given (Telegram button), it must equal
   that target; otherwise refuse.
2. Refused (no target, old button, expired): record the customer message, insert a
   `stock_alerts` row `kind='acceptance_refused'`, set conversation `needs_staff`, queue the fixed
   notice "This quotation can no longer be accepted. Our sales team will contact you." No agent job.
3. Accept: quote -> `accepted`; create `orders` (`pending`) + `order_lines` from quote content;
   keep the reservation held; conversation status `order_pending`; queue fixed notice
   "Thank you. Your acceptance of quotation {number}, revision {n}, is recorded. Our sales team
   will confirm your order." Audit `order.accepted`.
4. Decline: quote -> `declined`; `ledger.release_quote(..., 'declined')`; conversation `declined`;
   notice "Thank you. Quotation {number} is declined. Send a new request any time." Audit.
5. Notices are queued only while the agent owns the conversation (`inbound.queue_notice` rule);
   under staff takeover the answer is still recorded and staff see it.
6. Idempotent on `provider_id` (same message twice has one effect) and on the quote (a second
   accept of an already-accepted quote is a no-op returning the existing order).

Hook point: `accept_customer_text` calls `parse_answer` **before** the supersede update. When the
answer is accept/decline and a target exists, it delegates to `answer_quote` and returns without
superseding or enqueueing the agent. Shared by Telegram, WhatsApp, Gmail (`email_ingress.strip_quoted`
already removes the quoted history) and the local test channel.

### 4.3 Delivery wording and Telegram buttons

- `messaging/outbound.py` `begin` and `runtime/delivery.py` `_deliver_local`: quotation caption gains
  "Reply ACCEPT to accept or DECLINE to decline." Gmail dispatch (`email_dispatch.py`) body too.
- Telegram: `telegram_client.send_pdf` takes an optional `buttons` argument and sends
  `reply_markup={"inline_keyboard": [[{"text": "Accept", "callback_data": "acc:<quote_id>"},
  {"text": "Decline", "callback_data": "dec:<quote_id>"}]]}` (callback_data is 1-64 bytes; 40 used).
  Verify the field names against the Bot API page before coding (R3).
- `get_updates` `allowed_updates` becomes `["message", "callback_query"]`.
  `telegram_ingress.reduce_update` maps a `callback_query` from a private chat (sender id = chat id,
  not a bot) to an event `{type: "quote_answer", answer, quote_id, id: "tgcb:<callback id>"}`.
  Malformed data -> skipped. `inbound.handle_message` routes `quote_answer` through the allowlist
  then `answer_quote(..., via='telegram_button', quote_id=...)`. After storing, the worker calls
  `answerCallbackQuery` (best effort, no customer text in logs) so the button stops spinning.

## 5. Staff actions, purchasing and alerts (task T4)

Routes (FastAPI, `Staff` + `OperationKey` + `operation()` idempotency + `rate_limit(conn,
f"{user}:mutation", 30)`, audit every write, contracts per R4):

| Method and path | Role | Effect |
|---|---|---|
| `GET /api/inventory/stock` | staff | Stock table rows + low flag |
| `GET /api/inventory/movements?product_id=&limit=` | staff | Newest movements (keyset by created_at,id) |
| `POST /api/inventory/adjustments` `{product_id, delta, reason}` | admin | `apply_movement(kind='adjustment')` |
| `POST /api/inventory/reorder-levels` `{product_id, reorder_level 0..100000}` | admin | Update level |
| `GET /api/inventory/alerts` | staff | Open shortage/refused alerts + live low-stock list |
| `POST /api/inventory/alerts/{id}/acknowledge` | staff | open -> acknowledged |
| `GET /api/orders?status=` | staff | Orders with lines |
| `POST /api/orders/{id}/confirm` | staff | pending -> confirmed; `ledger.convert_quote`; conversation `ordered` |
| `POST /api/orders/{id}/cancel` `{reason}` | staff | pending -> cancelled (release) or confirmed -> cancelled (`order_cancel` movements, positive delta) |
| `GET /api/purchase-orders` | staff | List with lines |
| `POST /api/purchase-orders` `{supplier, expected_on?, notes?, lines:[{product_id, quantity, unit_cost}]}` | admin | Create `ordered` |
| `POST /api/purchase-orders/{id}/receive` `{lines:[{product_id, quantity}]}` | admin | Raise `quantity_received`, `receipt` movements, status partially_received/received |
| `POST /api/purchase-orders/{id}/cancel` | admin | Only when nothing received |
| `GET /api/inventory/export.xlsx` | staff | Excel download (task T5) |
| `POST /api/inventory/sheet-exports` / `GET /api/inventory/sheet-exports/latest` | staff | Queue / show Google Sheets export (task T5) |

Packages: `features/inventory` (ledger, stock, adjustments, alerts, exports), `features/orders`
(acceptance, orders), `features/purchasing` (purchase orders, receipts). `main.py` only includes the
routers. A salesperson calling an admin route gets 403 with a plain message.

Shortage alert: in `nodes/workflow.py` `prepare`, when `available < quantity` for a line, insert a
`stock_alerts` row (`kind='shortage'`, product, requested, available, conversation) besides the
existing system message and `needs_staff`. The customer is not told (D49). Discontinued or unknown
SKUs keep the current behavior without an alert.

## 6. Excel and Google Sheets export (task T5)

- Excel: add `openpyxl` to `pyproject.toml` and pin the current release in `requirements.lock.txt`
  (read its PyPI page and changelog first, R3). `inventory/exports.py` builds a workbook with sheets
  `Stock`, `Movements` (last 5000), `Customer Orders`, `Purchase Orders`; header row bold and frozen.
  Streamed as `lumaquote-stock-YYYYMMDD.xlsx`.
- Formula injection guard (security): any text cell starting with `=`, `+`, `-`, `@`, tab or CR is
  written as text with a leading `'` (Excel) and the same guard applies to Sheets rows. Customer
  names come from chat and are untrusted. Tested with `=HYPERLINK(...)` and `@SUM(...)` canaries.
- Google Sheets (D10, GAS only): same pull pattern as `google_sync/exports.py`. The web app button
  queues a `sheet_exports` row. Signed gateway endpoints in `google_sync` (registered in
  `google_gateway.py`): `POST /callbacks/google/stock/claim` returns the rows of the three tabs
  for the queued export (lease 5 minutes, HMAC envelope, nonce, workbook binding, `extra="forbid"`);
  `POST /callbacks/google/stock/receipt` stores `done` with row counts or `failed` with a code.
  New `gas/Stock.gs`: `exportStockTabs_()` called by the existing minute timer; clears and rewrites
  only the `Stock`, `Customer Orders` and `Purchase Orders` tabs (creates them if missing), writes
  values with plain-text number format for text columns, never touches Products, Prices, Policies
  or Inventory. `gas/README.md` documents the push step. Pushing GAS to the user's project is a
  live step: record it in `docs/MORNING_ACTIONS.md` (D37 lets Claude do it in the browser later).
- Sheet sync change: `google_sync/validation.py` makes the `Inventory` table optional and ignored
  (accepted for old GAS versions), the snapshot digest excludes it, and `gas/Synchronization.gs`
  stops sending it. Products and Prices keep syncing; freshness still needs a snapshot within 90 s
  for live channels.

## 7. Frontend (task T6)

Use `frontend-structure` (lead) and `frontend-design` + `shadcn` (supporting). New feature
`app/frontend/src/features/inventory/`:

- Route `/inventory` with tabs: **Stock** (table: SKU, name, family, on hand, reserved, available,
  reorder level, status chip OK / Low / Out; admin row actions Adjust and Reorder level in dialogs;
  movement history drawer), **Customer orders** (pending first; Confirm / Cancel with reason),
  **Purchase orders** (admin: New purchase order dialog with SKU picker, Receive dialog with
  partial quantities, Cancel), **Alerts** (shortage, refused acceptance, low stock; Acknowledge).
- Toolbar: **Download Excel** (fetch with auth, save blob) and **Export to Google Sheets** (queues,
  then shows queued / done with row counts / failed).
- Nav item "Inventory" in `AppShell` with a count badge of open alerts + low-stock SKUs.
- Overview: a stock card (low-stock count, pending orders, open alerts) that links to `/inventory`.
- Quotation panel: when the conversation has a pending order, a banner "Customer accepted
  Q-xxx r2" with Confirm order / Cancel; statuses `accepted`, `declined`, `order_pending`,
  `ordered` get labels. Catalog keeps showing available (now from the ledger).
- Hide admin-only controls for salespeople (server still enforces). Regenerate
  `src/shared/api/generated.ts` from the API's OpenAPI with the project's existing method
  (read `docs/reference/FRONTEND.md`). TanStack Query keys per feature; invalidate stock, orders
  and alerts after each mutation. Vitest tests for the stock table, confirm flow and role hiding.
- No 3D required here; keep the existing visual system (DESIGN.md, UI_DIRECTION.md). Respect
  reduced motion and keyboard access.

## 8. Tests and evidence (every task)

Pytest integration tests against local Supabase (`npm run db:start`), named `tests/integration/test_stock_*.py`:

- Ledger invariants after a mixed sequence: on_hand = sum(movements), reserved = sum(held).
- Two approvals race for the last units (two connections): exactly one succeeds, the other gets 409.
- Supersede, decline, expiry, blocked and failed delivery each release the reservation; `unknown`
  delivery does not.
- Acceptance: phrase table (unit), latest-revision binding, old revision, expired, other chat's
  quote id via a forged Telegram callback, duplicate provider id, staff takeover.
- Order confirm moves stock once (idempotency key replay), cancel pending releases, cancel
  confirmed returns stock.
- Purchase order partial and full receipt; cancel refused after a receipt; receiving more than
  ordered refused.
- Adjustment below reserved refused; salesperson 403 on admin routes.
- Shortage alert row written by `prepare`.
- Snapshot without Inventory accepted; snapshot with Inventory does not change stock.
- Excel opens with openpyxl, has four sheets, injection canaries are text.
- GAS stock export: bad signature, replayed nonce, wrong workbook refused; claim/receipt happy path.
- Migration test: backfill equality, column dropped, RLS on every new table.

Evidence files `docs/evidence/stock-*-2026-11-07.json` with the common header (R9), label `local`.
Plan checkboxes in `docs/IMPLEMENTATION_PLAN.md` are ticked only with an evidence link (R10).

## 9. Task list (one Sonnet subagent each, sequential, one commit per task)

| Task | Scope | Lead skill | Depends on |
|---|---|---|---|
| T1 | Migration, `inventory/ledger.py` + queries, readers switched off `products.available`, snapshot stops writing stock, migration + ledger tests | `build-quotations` (+ `fastapi`) | - |
| T2 | Reservation at approval, dispatch check, release hooks, worker `reconcile`, race and release tests | `build-quotations` | T1 |
| T3 | Accept/decline parser and service, `accept_customer_text` hook, delivery wording, Telegram buttons + callback ingress, Gmail reply path, tests | `integrate-whatsapp` (channels) + `implement-human-approval` | T2 |
| T4 | Orders confirm/cancel, purchase orders + receipts, adjustments, reorder levels, alerts, shortage alert in `prepare`, routes, role tests | `fastapi` + `secure-quotation-app` | T3 |
| T5 | Excel export (openpyxl pinned), Google Sheets pull export + `gas/Stock.gs`, Inventory tab ignored in sync, injection guard, tests | `automate-google-workspace` + `secure-quotation-app` | T4 |
| T6 | Frontend inventory feature, nav badge, overview card, quotation panel banner, generated API types, Vitest | `frontend-structure` + `frontend-design`, `shadcn` | T5 |
| T7 | Deep docs (`docs/reference/INVENTORY.md`, DATA_MODEL, GOOGLE_SYNC, TELEGRAM, EMAIL, AGENT_RULES, FRONTEND, BACKEND), diagrams (`stock-ledger.mmd`, order state machine), `graph:update`, `IMPLEMENTATION_PLAN.md` phase 7 status, full verify | `project-documentation` + `verify-and-review` | T6 |

Each task ends with: inline contracts (R4), its owning reference doc section, one work-log entry,
the narrowest checks (`lint:python`, `check:architecture`, the new test files, `check:frontend`
and `test:ui` for T6), `npm run check:rules`, and a commit on `feat/stock-orders` staging only its
files. The orchestrator reviews each diff before starting the next task. After T7: push, PR,
`npm run verify` on the final tree, merge (R16 billing-lock rule applies).

## 10. Out of scope (not decided, not built)

Shipping/fulfilment and delivery dates, multiple warehouses, supplier records beyond a name,
payments and invoices, automatic reordering, customer-visible stock numbers, AI-written
acceptance replies, deployment (D06).

## 11. Open gaps

- Live Telegram button test and GAS push need the user's running bot and Apps Script project
  (MORNING_ACTIONS); local tests use mocked transports and are labeled `local`.
- The existing `Quote Register` tab stays unused; the new `Customer Orders` tab replaces its purpose.
