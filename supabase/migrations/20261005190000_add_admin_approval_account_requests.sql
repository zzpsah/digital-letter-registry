create table if not exists public.account_access_requests (
  id uuid primary key default extensions.gen_random_uuid(),
  archive_id uuid not null references public.archives(id) on delete cascade,
  email text not null,
  status text not null default 'pending'
    check (status in ('pending','approved','rejected','completed')),
  approved_role text
    check (approved_role is null or approved_role in ('viewer','editor','admin')),
  approval_token uuid,
  requested_at timestamptz not null default now(),
  notified_at timestamptz,
  approved_at timestamptz,
  approval_notified_at timestamptz,
  completed_at timestamptz,
  rejected_at timestamptz,
  updated_at timestamptz not null default now(),
  unique (archive_id, email)
);

create index if not exists account_access_requests_archive_status_idx
  on public.account_access_requests (archive_id, status, requested_at desc);

alter table public.account_access_requests enable row level security;
revoke all on table public.account_access_requests from anon;
revoke all on table public.account_access_requests from authenticated;
grant select, update on table public.account_access_requests to authenticated;

drop policy if exists "admins read access requests" on public.account_access_requests;
create policy "admins read access requests"
on public.account_access_requests for select to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "admins update access requests" on public.account_access_requests;
create policy "admins update access requests"
on public.account_access_requests for update to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin')
with check ((select private.archive_member_role(archive_id)) = 'admin');

create or replace function public.dlr_request_archive_access(
  target_archive_id uuid,
  target_email text
)
returns table(request_id uuid, request_status text)
language plpgsql
security definer
set search_path = ''
as $$
declare
  normalized_email text := lower(btrim(target_email));
  existing public.account_access_requests%rowtype;
begin
  if normalized_email is null
     or length(normalized_email) < 3
     or length(normalized_email) > 320
     or position('@' in normalized_email) <= 1 then
    raise exception 'invalid email';
  end if;

  if not exists (
    select 1 from public.archives
    where id = target_archive_id and status = 'active'
  ) then
    raise exception 'archive unavailable';
  end if;

  select * into existing
  from public.account_access_requests
  where archive_id = target_archive_id
    and email = normalized_email
  limit 1;

  if found then
    if existing.status = 'completed' then
      return query select existing.id, existing.status;
      return;
    end if;

    if existing.status = 'rejected' then
      update public.account_access_requests
      set status = 'pending',
          approved_role = null,
          approval_token = null,
          requested_at = now(),
          notified_at = null,
          approved_at = null,
          approval_notified_at = null,
          rejected_at = null,
          updated_at = now()
      where id = existing.id
      returning id, status into existing.id, existing.status;
    elsif existing.status = 'pending' then
      -- Prevent repeated anonymous submissions from spamming the admin inbox.
      if existing.requested_at <= now() - interval '15 minutes' then
        update public.account_access_requests
        set requested_at = now(),
            notified_at = null,
            updated_at = now()
        where id = existing.id
        returning id, status into existing.id, existing.status;
      end if;
    else
      -- Approved requests remain approved until completed/rejected by admin.
      update public.account_access_requests
      set updated_at = now()
      where id = existing.id
      returning id, status into existing.id, existing.status;
    end if;

    return query select existing.id, existing.status;
    return;
  end if;

  insert into public.account_access_requests (archive_id, email)
  values (target_archive_id, normalized_email)
  returning id, status into existing.id, existing.status;

  return query select existing.id, existing.status;
end;
$$;

revoke all on function public.dlr_request_archive_access(uuid,text) from public;
grant execute on function public.dlr_request_archive_access(uuid,text) to anon, authenticated;

create or replace function public.dlr_claim_account_notifications(
  target_archive_id uuid,
  notification_kind text,
  result_limit integer default 20
)
returns table(
  request_id uuid,
  email text,
  approved_role text,
  approval_token uuid
)
language plpgsql
security definer
set search_path = ''
as $$
begin
  if (select private.archive_member_role(target_archive_id)) not in ('admin','editor') then
    raise exception 'forbidden';
  end if;

  if notification_kind = 'request' then
    return query
      select r.id, r.email, r.approved_role, r.approval_token
      from public.account_access_requests r
      where r.archive_id = target_archive_id
        and r.status = 'pending'
        and r.notified_at is null
      order by r.requested_at
      limit greatest(1, least(coalesce(result_limit,20),100));
  elsif notification_kind = 'approved' then
    return query
      select r.id, r.email, r.approved_role, r.approval_token
      from public.account_access_requests r
      where r.archive_id = target_archive_id
        and r.status = 'approved'
        and r.approval_notified_at is null
        and r.approval_token is not null
      order by r.approved_at
      limit greatest(1, least(coalesce(result_limit,20),100));
  else
    raise exception 'invalid notification kind';
  end if;
end;
$$;

revoke all on function public.dlr_claim_account_notifications(uuid,text,integer) from public;
grant execute on function public.dlr_claim_account_notifications(uuid,text,integer) to authenticated;

create or replace function public.dlr_mark_account_notification_sent(
  target_archive_id uuid,
  target_request_id uuid,
  notification_kind text
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
begin
  if (select private.archive_member_role(target_archive_id)) not in ('admin','editor') then
    raise exception 'forbidden';
  end if;

  if notification_kind = 'request' then
    update public.account_access_requests
    set notified_at = now(), updated_at = now()
    where archive_id = target_archive_id and id = target_request_id;
  elsif notification_kind = 'approved' then
    update public.account_access_requests
    set approval_notified_at = now(), updated_at = now()
    where archive_id = target_archive_id and id = target_request_id;
  else
    raise exception 'invalid notification kind';
  end if;
  return found;
end;
$$;

revoke all on function public.dlr_mark_account_notification_sent(uuid,uuid,text) from public;
grant execute on function public.dlr_mark_account_notification_sent(uuid,uuid,text) to authenticated;
