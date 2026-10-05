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
      set status = 'pending', approved_role = null, approval_token = null,
          requested_at = now(), notified_at = null, approved_at = null,
          approval_notified_at = null, rejected_at = null, updated_at = now()
      where id = existing.id
      returning id, status into existing.id, existing.status;
    elsif existing.status = 'pending' then
      if existing.requested_at <= now() - interval '15 minutes' then
        update public.account_access_requests
        set requested_at = now(), notified_at = null, updated_at = now()
        where id = existing.id
        returning id, status into existing.id, existing.status;
      end if;
    else
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
