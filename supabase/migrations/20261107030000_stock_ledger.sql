-- Stock ledger, customer orders and supplier purchasing (decision D49, plan task T1).
-- The web app becomes the stock master. Stock is a ledger: luma.stock_movements is append-only,
-- luma.stock_levels caches on_hand (= sum of movements) and reserved (= sum of held reservations),
-- and available is always derived as on_hand - reserved, never stored. Only
-- app/backend/luma/features/inventory/ledger.py writes stock_levels, stock_movements and
-- stock_reservations. Google Sheets no longer supplies stock, so products.available is dropped
-- after its values are copied into the ledger (the local database is the only database, D06).

-- A customer can now accept or decline a sent quotation (written by the orders feature in task T3).
alter table luma.quotes drop constraint quotes_status_check;
alter table luma.quotes
    add constraint quotes_status_check
    check (status in ('review','approved','rejected','superseded','expired','accepted','declined'));

create table luma.stock_levels (
    company_id uuid not null,
    product_id uuid not null,
    on_hand integer not null default 0 check (on_hand >= 0),
    reserved integer not null default 0 check (reserved >= 0),
    reorder_level integer not null default 20 check (reorder_level between 0 and 100000),
    updated_at timestamptz not null default now(),
    primary key (company_id, product_id),
    foreign key (company_id, product_id) references luma.products(company_id, id),
    check (reserved <= on_hand)
);

-- Append-only: the application roles receive select and insert only (grants below).
create table luma.stock_movements (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null,
    product_id uuid not null,
    delta integer not null check (delta <> 0),
    kind text not null check (kind in ('opening','adjustment','receipt','order','order_cancel')),
    reference_id uuid,
    reason text check (reason is null or length(reason) <= 200),
    actor text not null check (length(actor) between 1 and 80),
    created_at timestamptz not null default now(),
    foreign key (company_id, product_id) references luma.products(company_id, id),
    check (kind <> 'adjustment' or length(btrim(coalesce(reason, ''))) between 3 and 200),
    check (
        (kind in ('opening','receipt','order_cancel') and delta > 0)
        or kind = 'adjustment'
        or (kind = 'order' and delta < 0)
    )
);
create index stock_movements_product on luma.stock_movements(company_id, product_id, created_at desc, id desc);
create index stock_movements_page on luma.stock_movements(company_id, created_at desc, id desc);

create table luma.stock_reservations (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null,
    quote_id uuid not null,
    product_id uuid not null,
    quantity integer not null check (quantity > 0),
    status text not null default 'held' check (status in ('held','released','converted')),
    release_reason text check (release_reason is null or length(release_reason) <= 60),
    created_at timestamptz not null default now(),
    closed_at timestamptz,
    unique (quote_id, product_id),
    foreign key (company_id, quote_id) references luma.quotes(company_id, id),
    foreign key (company_id, product_id) references luma.products(company_id, id),
    check ((status = 'held') = (closed_at is null))
);
create index stock_reservations_held on luma.stock_reservations(company_id, status, quote_id);
create index stock_reservations_product on luma.stock_reservations(company_id, product_id) where status = 'held';

create table luma.orders (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null,
    number text not null check (length(number) between 3 and 20),
    conversation_id uuid not null,
    quote_id uuid not null unique,
    revision integer not null check (revision > 0),
    status text not null default 'pending' check (status in ('pending','confirmed','cancelled')),
    accepted_via text not null check (accepted_via in ('telegram_button','reply','staff')),
    accepted_at timestamptz not null default now(),
    confirmed_by uuid references auth.users(id),
    confirmed_at timestamptz,
    cancelled_by uuid references auth.users(id),
    cancelled_at timestamptz,
    cancel_reason text check (cancel_reason is null or length(cancel_reason) <= 200),
    currency text not null check (length(currency) = 3),
    total numeric(12,2) not null check (total >= 0),
    customer_name text not null,
    customer_company text not null default '',
    created_at timestamptz not null default now(),
    unique (company_id, number),
    unique (company_id, id),
    foreign key (company_id, conversation_id) references luma.conversations(company_id, id),
    foreign key (company_id, quote_id) references luma.quotes(company_id, id),
    check (status <> 'confirmed' or (confirmed_by is not null and confirmed_at is not null)),
    check (status <> 'cancelled' or cancelled_at is not null)
);
create index orders_company_status on luma.orders(company_id, status, created_at desc);

-- Copied from the accepted immutable quotation content; prices are never recomputed.
create table luma.order_lines (
    order_id uuid not null,
    company_id uuid not null,
    product_id uuid not null,
    sku text not null,
    name text not null,
    quantity integer not null check (quantity > 0),
    unit_price numeric(12,2) not null check (unit_price >= 0),
    line_total numeric(12,2) not null check (line_total >= 0),
    primary key (order_id, product_id),
    foreign key (company_id, order_id) references luma.orders(company_id, id),
    foreign key (company_id, product_id) references luma.products(company_id, id)
);

create table luma.purchase_orders (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null,
    number text not null check (length(number) between 3 and 20),
    supplier text not null check (length(btrim(supplier)) between 1 and 120),
    status text not null default 'ordered'
        check (status in ('ordered','partially_received','received','cancelled')),
    expected_on date,
    notes text check (notes is null or length(notes) <= 500),
    created_by uuid not null references auth.users(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (company_id, number),
    unique (company_id, id)
);
create index purchase_orders_company on luma.purchase_orders(company_id, created_at desc);

create table luma.purchase_order_lines (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null,
    purchase_order_id uuid not null,
    product_id uuid not null,
    quantity_ordered integer not null check (quantity_ordered > 0),
    quantity_received integer not null default 0 check (quantity_received >= 0),
    unit_cost numeric(12,2) not null check (unit_cost >= 0),
    unique (purchase_order_id, product_id),
    foreign key (company_id, purchase_order_id) references luma.purchase_orders(company_id, id),
    foreign key (company_id, product_id) references luma.products(company_id, id),
    check (quantity_received <= quantity_ordered)
);

-- Shortage and refused-acceptance alerts are stored. Low-stock alerts are not: they are a live
-- query (available <= reorder_level) so they cannot go stale.
create table luma.stock_alerts (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null,
    kind text not null check (kind in ('shortage','acceptance_refused')),
    product_id uuid,
    conversation_id uuid,
    quote_id uuid,
    requested integer check (requested is null or requested >= 0),
    available integer check (available is null or available >= 0),
    status text not null default 'open' check (status in ('open','acknowledged')),
    acknowledged_by uuid references auth.users(id),
    created_at timestamptz not null default now(),
    acknowledged_at timestamptz,
    foreign key (company_id, product_id) references luma.products(company_id, id),
    foreign key (company_id, conversation_id) references luma.conversations(company_id, id),
    foreign key (company_id, quote_id) references luma.quotes(company_id, id),
    check (status <> 'acknowledged' or (acknowledged_by is not null and acknowledged_at is not null))
);
create index stock_alerts_open on luma.stock_alerts(company_id, status, created_at desc);

-- Staff-requested Google Sheets stock export, pulled and confirmed by Apps Script (task T5).
-- At most one queued or claimed export per company at a time.
create table luma.sheet_exports (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null references luma.companies(id),
    status text not null default 'queued' check (status in ('queued','claimed','done','failed')),
    requested_by uuid not null references auth.users(id),
    claim_token uuid,
    lease_until timestamptz,
    row_counts jsonb,
    error_code text check (error_code is null or length(error_code) <= 40),
    created_at timestamptz not null default now(),
    completed_at timestamptz,
    check (status <> 'claimed' or (claim_token is not null and lease_until is not null))
);
create unique index sheet_exports_one_open on luma.sheet_exports(company_id) where status in ('queued','claimed');
create index sheet_exports_company on luma.sheet_exports(company_id, created_at desc);

-- Gap-tolerant, lock-serialized document numbering (SO-0001, PO-0001).
create table luma.document_counters (
    company_id uuid not null references luma.companies(id),
    kind text not null check (kind in ('order','purchase_order')),
    next_value integer not null default 1 check (next_value >= 1),
    primary key (company_id, kind)
);

-- Backfill before the destructive drop: one level per product, and one opening movement for each
-- product that has stock (a movement needs a non-zero delta, so zero-stock products have none).
insert into luma.stock_levels(company_id, product_id, on_hand)
    select company_id, id, available from luma.products;
insert into luma.stock_movements(company_id, product_id, delta, kind, actor)
    select company_id, id, available, 'opening', 'migration' from luma.products where available > 0;
alter table luma.products drop column available;

-- Row-level security and grants follow the pattern of the quotation domain migration.
do $$ declare t text; begin
 foreach t in array array['stock_levels','stock_movements','stock_reservations','orders','order_lines',
 'purchase_orders','purchase_order_lines','stock_alerts','sheet_exports','document_counters'] loop
  execute format('alter table luma.%I enable row level security',t);
  execute format('revoke all on luma.%I from public, anon, authenticated',t);
  execute format('create policy staff_scope on luma.%I to luma_api using
   (exists(select 1 from luma.memberships m where m.company_id=%I.company_id and m.user_id=auth.uid() and m.active))
   with check(exists(select 1 from luma.memberships m where m.company_id=%I.company_id and m.user_id=auth.uid() and m.active))',t,t,t);
  execute format('create policy worker_scope on luma.%I to luma_worker using(true) with check(true)',t);
 end loop;
end $$;

-- Levels and reservations: the ledger writes them from the API (approval, adjustments, receipts,
-- order confirm/cancel) and from the worker (release, reconcile, dispatch checks).
grant select, insert, update on luma.stock_levels, luma.stock_reservations to luma_api, luma_worker;
-- Movements are append-only. Only the API ledger path (adjustments, receipts, order confirm and
-- cancel) writes them; the worker only releases reservations and so never inserts one.
grant select, insert on luma.stock_movements to luma_api;
grant select on luma.stock_movements to luma_worker;
-- Orders are created pending by the acceptance path (API webhook or worker) and confirmed or
-- cancelled by staff through the API. Lines are immutable once copied from the quotation.
grant select, insert, update on luma.orders to luma_api, luma_worker;
grant select, insert on luma.order_lines to luma_api, luma_worker;
-- Purchasing is admin-only through the API; the worker reads it for the Sheets export gateway.
grant select, insert, update on luma.purchase_orders, luma.purchase_order_lines to luma_api;
grant select on luma.purchase_orders, luma.purchase_order_lines to luma_worker;
-- Alerts: inserted by the agent worker and acceptance path, acknowledged by staff.
grant select, insert, update on luma.stock_alerts to luma_api, luma_worker;
-- Sheet exports: staff queue them; the signed gateway (worker connection) claims and completes them.
grant select, insert on luma.sheet_exports to luma_api;
grant select, insert, update on luma.sheet_exports to luma_worker;
-- Numbering is advanced inside the transaction that creates the numbered document.
grant select, insert, update on luma.document_counters to luma_api, luma_worker;
