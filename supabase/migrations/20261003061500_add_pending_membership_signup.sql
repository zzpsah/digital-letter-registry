-- Reconcile the hosted self-service account bootstrap behavior.
-- This migration records live verified state: a password signup without an
-- invite starts as viewer/disabled and requires admin activation.

create or replace function private.initialize_pending_archive_membership()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  target_archive_id uuid;
begin
  if new.email is null then
    return new;
  end if;

  if coalesce(new.raw_user_meta_data ->> 'dlr_invite_code', '') <> '' then
    return new;
  end if;

  select a.id
    into target_archive_id
  from public.archives a
  where a.status = 'active'
  order by a.created_at
  limit 1;

  if target_archive_id is null then
    return new;
  end if;

  insert into public.archive_members (
    archive_id,
    user_id,
    role,
    status
  )
  values (
    target_archive_id,
    new.id,
    'viewer',
    'disabled'
  )
  on conflict (archive_id, user_id) do nothing;

  return new;
end
$$;

revoke all on function private.initialize_pending_archive_membership()
  from public;
revoke all on function private.initialize_pending_archive_membership()
  from anon;
revoke all on function private.initialize_pending_archive_membership()
  from authenticated;

drop trigger if exists dlr_pending_membership_on_auth_user
  on auth.users;
create trigger dlr_pending_membership_on_auth_user
after insert on auth.users
for each row execute function private.initialize_pending_archive_membership();
