-- Signed invalidations only. Importing authoritative snapshots is a separate operation.
create table luma.google_edit_receipts (
    company_id uuid not null references luma.companies(id) on delete cascade,
    nonce uuid not null,
    fingerprint text not null,
    received_at timestamptz not null default now(),
    primary key(company_id,nonce)
);
create index google_edit_receipts_received on luma.google_edit_receipts(received_at);
create table luma.google_refresh_signals (
    company_id uuid primary key references luma.companies(id) on delete cascade,
    spreadsheet_id text not null,
    requested_at timestamptz not null default now()
);
alter table luma.google_edit_receipts enable row level security;
alter table luma.google_refresh_signals enable row level security;
revoke all on luma.google_edit_receipts,luma.google_refresh_signals from public,anon,authenticated,luma_api;
grant select,insert,update,delete on luma.google_edit_receipts,luma.google_refresh_signals to luma_worker;
create policy google_receipts_worker on luma.google_edit_receipts to luma_worker using(true) with check(true);
create policy google_signals_worker on luma.google_refresh_signals to luma_worker using(true) with check(true);
