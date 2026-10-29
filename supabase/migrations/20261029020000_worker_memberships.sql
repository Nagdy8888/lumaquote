-- Existing local installs need this policy as well as new installations.
drop policy if exists membership_worker on luma.memberships;
create policy membership_worker on luma.memberships for select to luma_worker using(true);
