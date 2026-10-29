-- Originals remain available for authorized historical quotations, but retired
-- evidence cannot be used for new recommendations, approval, or dispatch.
alter table luma.sources add column retired_at timestamptz;
