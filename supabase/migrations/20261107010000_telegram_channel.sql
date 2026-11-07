-- Telegram bot channel (decision D44). A Telegram conversation's recipient is the private chat id,
-- which equals the Telegram user id. Inbox, outbox and messages are reused unchanged: Telegram
-- events are stored under provider ids `tg:<chat id>:<message id>`.
alter table luma.conversations drop constraint conversations_channel_check;
alter table luma.conversations
  add constraint conversations_channel_check check (channel in ('local_test', 'whatsapp', 'telegram'));
