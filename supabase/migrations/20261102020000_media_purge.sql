-- Runtime media (original and normalized bytes) is kept seven days. After the operator retention
-- tool deletes the private objects it stamps purged_at; the transcript/reading text stays because it
-- is business data governed by the 90-day policy. Preview routes treat a purged row as missing.
alter table luma.media add column purged_at timestamptz;
