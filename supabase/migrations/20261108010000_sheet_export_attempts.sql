-- Stock Sheets export: count claim attempts so a silent or failing Apps Script stops after five tries
-- (decision D49, task T5). Same bounded-retry rule as luma.drive_exports.
alter table luma.sheet_exports add column attempts integer not null default 0 check (attempts >= 0);
