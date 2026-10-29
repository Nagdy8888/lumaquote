-- Runtime identities may transition a quotation's lifecycle, but they must create
-- another revision rather than mutating an already reviewed commercial record.
revoke update on luma.quotes from luma_api,luma_worker;
grant update(status) on luma.quotes to luma_api,luma_worker;

alter table luma.outbox add constraint outbox_quote_identity_required
 check ((kind='quotation' and quote_id is not null) or (kind='reply' and quote_id is null));
alter table luma.outbox add constraint outbox_reply_text_bounded
 check (kind='quotation' or (payload ? 'text' and jsonb_typeof(payload->'text')='string'
        and length(payload->>'text') between 1 and 2000));
