alter table luma.media add column kind text not null default 'audio' check(kind in ('audio','image'));
alter table luma.jobs drop constraint jobs_kind_check;
alter table luma.jobs add constraint jobs_kind_check check(kind in ('agent','drive_export','transcribe','read_photo'));
