create schema if not exists luma;
revoke all on schema luma from public, anon, authenticated;
do $$ begin
  if not exists (select from pg_roles where rolname='luma_api') then create role luma_api login; end if;
  if not exists (select from pg_roles where rolname='luma_worker') then create role luma_worker login; end if;
end $$;
grant usage on schema luma, extensions to luma_api, luma_worker;
grant usage on schema auth to luma_api;
grant execute on function auth.uid() to luma_api;

create table luma.companies (
 id uuid primary key, name text not null, synthetic boolean not null default true
);
create table luma.memberships (
 user_id uuid references auth.users(id), company_id uuid references luma.companies(id),
 role text not null check(role in ('admin','salesperson')), active boolean not null default true,
 primary key(user_id,company_id)
);
create table luma.sources (
 id uuid primary key, company_id uuid not null references luma.companies(id),
 title text not null, version integer not null default 1, object_path text not null,
 created_at timestamptz not null default now(), unique(company_id,id)
);
create table luma.snapshots (
 id uuid primary key, company_id uuid not null references luma.companies(id),
 source text not null check(source in ('synthetic','google_sheets')),
 observed_at timestamptz not null, digest text not null, unique(company_id,id)
);
create table luma.products (
 id uuid primary key, company_id uuid not null references luma.companies(id),
 sku text not null, name text not null, family text not null, description text not null,
 watts integer not null check(watts>0), lumens integer not null check(lumens>0),
 cct integer not null, ip_rating text not null, price numeric(12,2) not null check(price>=0),
 available integer not null check(available>=0), pack_size integer not null default 1 check(pack_size>0),
 discontinued boolean not null default false, source_id uuid not null, page integer not null check(page>0),
 snapshot_id uuid not null, embedding extensions.vector(1536),
 unique(company_id,sku), unique(company_id,id),
 foreign key(company_id,source_id) references luma.sources(company_id,id),
 foreign key(company_id,snapshot_id) references luma.snapshots(company_id,id)
);
create table luma.conversations (
 id uuid primary key, company_id uuid not null references luma.companies(id),
 customer_name text not null, customer_company text not null default '',
 recipient text not null, channel text not null check(channel in ('local_test','whatsapp')),
 owner text not null default 'agent' check(owner in ('agent','staff')),
 status text not null default 'new', version integer not null default 1,
 last_customer_at timestamptz not null default now(), created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(), unique(company_id,id)
);
create table luma.messages (
 id uuid primary key, company_id uuid not null, conversation_id uuid not null,
 actor text not null check(actor in ('customer','assistant','staff','system')),
 kind text not null default 'text' check(kind in ('text','audio','image','document')),
 body text not null, object_path text, provider_id text unique,
 created_at timestamptz not null default now(),
 foreign key(company_id,conversation_id) references luma.conversations(company_id,id)
);
create table luma.quotes (
 id uuid primary key, company_id uuid not null, conversation_id uuid not null,
 number text not null, revision integer not null check(revision>0),
 status text not null default 'review' check(status in ('review','approved','rejected','superseded','expired')),
 recipient text not null, snapshot_id uuid not null, content jsonb not null,
 content_hash text not null, valid_until timestamptz not null,
 created_at timestamptz not null default now(), unique(company_id,id), unique(conversation_id,revision),
 foreign key(company_id,conversation_id) references luma.conversations(company_id,id),
 foreign key(company_id,snapshot_id) references luma.snapshots(company_id,id)
);
create table luma.approvals (
 id uuid primary key, company_id uuid not null, quote_id uuid not null unique,
 approver uuid not null references auth.users(id), content_hash text not null, recipient text not null,
 created_at timestamptz not null default now(),
 foreign key(company_id,quote_id) references luma.quotes(company_id,id)
);
create table luma.jobs (
 id uuid primary key, company_id uuid not null, conversation_id uuid not null,
 kind text not null check(kind in ('agent','drive_export')),
 payload jsonb not null default '{}', status text not null default 'queued'
 check(status in ('queued','running','done','failed','blocked')),
 attempts integer not null default 0, lease_until timestamptz, fence integer not null default 0,
 error_code text, created_at timestamptz not null default now(),
 foreign key(company_id,conversation_id) references luma.conversations(company_id,id)
);
create table luma.outbox (
 id uuid primary key, company_id uuid not null, conversation_id uuid not null,
 quote_id uuid, kind text not null check(kind in ('reply','quotation')),
 payload jsonb not null, status text not null default 'queued'
 check(status in ('queued','submitting','submitted','delivered','read','failed','unknown','blocked','local_delivered')),
 provider_id text unique, action_key text not null unique, error_code text,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 foreign key(company_id,conversation_id) references luma.conversations(company_id,id),
 foreign key(company_id,quote_id) references luma.quotes(company_id,id)
);
create table luma.inbox (
 provider_id text primary key, company_id uuid not null references luma.companies(id),
 payload jsonb not null, created_at timestamptz not null default now()
);
create table luma.operations (
 company_id uuid not null, user_id uuid not null, action text not null, key uuid not null,
 digest text not null, response jsonb not null,
 primary key(company_id,user_id,action,key)
);
create table luma.usage (
 id uuid primary key, company_id uuid not null references luma.companies(id), job_id uuid unique,
 reserved numeric(10,4) not null check(reserved>=0), estimated numeric(10,6),
 status text not null default 'reserved' check(status in ('reserved','settled','unknown','released')),
 created_at timestamptz not null default now()
);
create table luma.rate_windows (
 key text not null, bucket_window bigint not null, count integer not null check(count>0), primary key(key,bucket_window)
);
create table luma.audit (
 id bigint generated always as identity primary key, company_id uuid not null references luma.companies(id),
 actor text not null, action text not null, resource_id uuid, detail jsonb not null default '{}',
 created_at timestamptz not null default now()
);
create index on luma.messages(conversation_id,created_at);
create index on luma.jobs(status,created_at);
create index on luma.outbox(status,created_at);
create index on luma.products using gin(to_tsvector('english',sku||' '||name||' '||description));

-- Membership lookup is self-only; no caller-editable metadata establishes authority.
alter table luma.memberships enable row level security;
create policy membership_self on luma.memberships for select to luma_api
 using(user_id=auth.uid());
create policy membership_worker on luma.memberships for select to luma_worker using(true);
grant select on luma.memberships to luma_api,luma_worker;
grant select on luma.companies to luma_api,luma_worker;
alter table luma.companies enable row level security;
create policy company_member on luma.companies to luma_api using (
 exists(select 1 from luma.memberships m where m.company_id=id and m.user_id=auth.uid() and m.active));
create policy company_worker on luma.companies to luma_worker using(true);

do $$ declare t text; begin
 foreach t in array array['sources','snapshots','products','conversations','messages','quotes','approvals',
 'jobs','outbox','inbox','operations','usage','audit'] loop
  execute format('alter table luma.%I enable row level security',t);
  execute format('create policy staff_scope on luma.%I to luma_api using
   (exists(select 1 from luma.memberships m where m.company_id=%I.company_id and m.user_id=auth.uid() and m.active))
   with check(exists(select 1 from luma.memberships m where m.company_id=%I.company_id and m.user_id=auth.uid() and m.active))',t,t,t);
  execute format('create policy worker_scope on luma.%I to luma_worker using(true) with check(true)',t);
 end loop;
end $$;
grant select,insert,update on luma.conversations,luma.messages,luma.quotes,luma.jobs,luma.outbox,luma.usage to luma_api,luma_worker;
grant select,insert on luma.approvals,luma.audit,luma.operations to luma_api;
grant select,insert on luma.audit,luma.inbox to luma_worker;
grant select on luma.approvals to luma_worker;
grant select on luma.sources,luma.snapshots,luma.products to luma_api,luma_worker;
grant select,insert,update on luma.rate_windows to luma_api,luma_worker;
grant usage,select on all sequences in schema luma to luma_api,luma_worker;
-- Business tables are not exposed via Supabase REST. Browser writes use the
-- authenticated API; private files are streamed after current membership checks.
insert into storage.buckets(id,name,public,file_size_limit)
values('luma-private','luma-private',false,20971520) on conflict(id) do nothing;
