-- Gmail channel through Apps Script (decision D47). An email conversation's recipient is the
-- sender's lowercase address. Inbound mails are stored in luma.inbox under `gm:<gmail message id>`.
-- Replies are pulled by Apps Script: the dispatcher authorizes and gates an outbox intent, marks it
-- `submitting` and adds one email_dispatch row; Apps Script claims the row, sends from Gmail and
-- reports the outcome. A claimed row whose lease expires without a receipt becomes `unknown` and is
-- never sent again, because the mail may already have left Gmail.
alter table luma.conversations drop constraint conversations_channel_check;
alter table luma.conversations
  add constraint conversations_channel_check check (channel in ('local_test', 'whatsapp', 'telegram', 'email'));

create table luma.email_dispatch (
    outbox_id uuid primary key references luma.outbox(id),
    company_id uuid not null,
    status text not null default 'waiting' check (status in ('waiting','claimed','sent','failed','unknown')),
    attempts integer not null default 0 check (attempts between 0 and 1),
    claim_token uuid,
    lease_until timestamptz,
    recipient text not null check (length(recipient) between 3 and 320),
    subject text not null check (length(subject) <= 300),
    body text not null check (length(body) between 1 and 20000),
    reply_message_id text check (reply_message_id ~ '^[0-9a-f]{10,32}$'),
    gmail_message_id text check (gmail_message_id ~ '^[0-9a-f]{10,32}$'),
    error_code text check (length(error_code) <= 40),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (status <> 'claimed' or (claim_token is not null and lease_until is not null))
);
create index email_dispatch_queue on luma.email_dispatch(company_id, status, created_at);
alter table luma.email_dispatch enable row level security;
revoke all on luma.email_dispatch from public, anon, authenticated;
grant select on luma.email_dispatch to luma_api;
grant select, insert, update on luma.email_dispatch to luma_worker;
create policy staff_scope on luma.email_dispatch for select to luma_api
    using (exists(select 1 from luma.memberships m where m.company_id = email_dispatch.company_id and m.user_id = auth.uid() and m.active));
create policy worker_scope on luma.email_dispatch to luma_worker using (true) with check (true);
