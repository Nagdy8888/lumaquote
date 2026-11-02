-- One Drive copy per approved quotation revision, pulled and confirmed by Google Apps Script.
-- The row is created in the approval transaction but is independent of customer delivery:
-- a failed or stalled export never changes the quotation, its approval or the outbox.
-- Identity is the immutable quote id (a new revision is a new quote row), so a retry can
-- never export different content under the same row.
create table luma.drive_exports (
    id uuid primary key,
    company_id uuid not null,
    quote_id uuid not null,
    revision integer not null check (revision > 0),
    status text not null default 'queued' check (status in ('queued','claimed','done','blocked')),
    attempts integer not null default 0 check (attempts >= 0),
    claim_token uuid,
    lease_until timestamptz,
    pdf_sha256 text check (pdf_sha256 ~ '^[0-9a-f]{64}$'),
    pdf_size integer check (pdf_size > 0),
    drive_file_id text check (length(drive_file_id) between 1 and 128),
    error_code text check (length(error_code) <= 40),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    completed_at timestamptz,
    unique (company_id, quote_id),
    foreign key (company_id, quote_id) references luma.quotes(company_id, id),
    check (status <> 'done' or (drive_file_id is not null and pdf_sha256 is not null))
);
create index drive_exports_queue on luma.drive_exports(company_id, status, created_at);
alter table luma.drive_exports enable row level security;
revoke all on luma.drive_exports from public, anon, authenticated;
grant select, insert on luma.drive_exports to luma_api;
grant select, insert, update on luma.drive_exports to luma_worker;
create policy staff_scope on luma.drive_exports to luma_api
    using (exists(select 1 from luma.memberships m where m.company_id = drive_exports.company_id and m.user_id = auth.uid() and m.active))
    with check (exists(select 1 from luma.memberships m where m.company_id = drive_exports.company_id and m.user_id = auth.uid() and m.active));
create policy worker_scope on luma.drive_exports to luma_worker using (true) with check (true);
