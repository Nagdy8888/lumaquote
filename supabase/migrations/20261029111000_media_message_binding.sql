-- A media record cannot relabel another conversation's message within a tenant.
alter table luma.messages add constraint messages_conversation_identity unique(company_id,conversation_id,id);
alter table luma.media add constraint media_message_conversation_fk
 foreign key(company_id,conversation_id,message_id) references luma.messages(company_id,conversation_id,id);
