-- Durable WhatsApp ingress. The webhook only persists a verified event and acknowledges;
-- the worker processes it later. provider_id (the primary key already on luma.inbox) is
-- the deduplication identity: the WhatsApp message id for a message, and
-- "status:<message id>:<status>" for a delivery receipt, so an earlier receipt never
-- suppresses a later delivered/read update.
alter table luma.inbox
    add column kind text not null default 'message' check (kind in ('message','status')),
    add column status text not null default 'queued' check (status in ('queued','processing','done','failed','ignored')),
    add column attempts integer not null default 0 check (attempts >= 0),
    add column error_code text check (length(error_code) <= 40),
    add column lease_until timestamptz,
    add column updated_at timestamptz not null default now();
create index inbox_queue on luma.inbox(status, created_at);
grant update on luma.inbox to luma_worker;
