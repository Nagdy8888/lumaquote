alter table luma.messages add constraint messages_company_identity unique(company_id,id);
alter table luma.jobs drop constraint jobs_kind_check;
alter table luma.jobs add constraint jobs_kind_check check(kind in ('agent','drive_export','transcribe'));

create table luma.media (
 message_id uuid primary key, company_id uuid not null,
 conversation_id uuid not null, original_path text not null,
 normalized_path text, status text not null default 'queued'
 check(status in ('queued','processing','ready','needs_staff','rejected','unknown')),
 transcript text, metadata jsonb not null default '{}', error_code text,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 foreign key(company_id,message_id) references luma.messages(company_id,id),
 foreign key(company_id,conversation_id) references luma.conversations(company_id,id)
);
alter table luma.media enable row level security;
create policy staff_scope on luma.media to luma_api using
 (exists(select 1 from luma.memberships m where m.company_id=media.company_id and m.user_id=auth.uid() and m.active))
 with check(exists(select 1 from luma.memberships m where m.company_id=media.company_id and m.user_id=auth.uid() and m.active));
create policy worker_scope on luma.media to luma_worker using(true) with check(true);
grant select,insert,update on luma.media to luma_api,luma_worker;
