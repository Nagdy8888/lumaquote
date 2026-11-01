-- GAS is the only Google data adapter; no backend Google OAuth grant is required.
create table luma.google_sync_state (
 company_id uuid primary key references luma.companies(id) on delete cascade,
 snapshot_id uuid not null references luma.snapshots(id) on delete cascade,
 observed_at timestamptz not null, digest text not null, source_tables jsonb not null
);
create table luma.google_snapshot_receipts (
 company_id uuid not null references luma.companies(id) on delete cascade,
 nonce uuid not null, fingerprint text not null, received_at timestamptz not null default now(),
 primary key(company_id,nonce)
);
create index google_snapshot_receipts_received on luma.google_snapshot_receipts(received_at);
alter table luma.google_sync_state enable row level security;
alter table luma.google_snapshot_receipts enable row level security;
revoke all on luma.google_sync_state,luma.google_snapshot_receipts from public,anon,authenticated,luma_api;
grant select,insert,update,delete on luma.google_sync_state,luma.google_snapshot_receipts to luma_worker;
create policy gas_state_worker on luma.google_sync_state to luma_worker using(true) with check(true);
create policy gas_receipts_worker on luma.google_snapshot_receipts to luma_worker using(true) with check(true);
grant insert,update on luma.snapshots to luma_worker;
grant update on luma.products to luma_worker;
