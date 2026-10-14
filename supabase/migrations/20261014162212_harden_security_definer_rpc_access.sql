-- Harden privileged RPC access and make archive membership checks NULL-safe.
-- Anonymous access remains enabled only for the deliberate guest flows:
-- dlr_request_archive_access() and dlr_validate_archive_invite().

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
  if coalesce((select private.archive_member_role(target_archive_id)), '') not in ('admin','editor') then
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
        and r.status in ('approved','completed')
        and r.approval_notified_at is null
      order by r.approved_at
      limit greatest(1, least(coalesce(result_limit,20),100));
  else
    raise exception 'invalid notification kind';
  end if;
end;
$$;

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
  if coalesce((select private.archive_member_role(target_archive_id)), '') not in ('admin','editor') then
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

-- These functions are invoked by triggers, not directly through the Data API.
revoke all on function public.backfill_authority_alias() from public, anon, authenticated, service_role;
revoke all on function public.set_letter_canonical_authority() from public, anon, authenticated, service_role;

-- These endpoints require an authenticated caller; each function still performs
-- its own auth.uid()/membership authorization check.
revoke execute on function public.dlr_claim_account_notifications(uuid,text,integer) from public, anon;
revoke execute on function public.dlr_mark_account_notification_sent(uuid,uuid,text) from public, anon;
revoke execute on function public.osint_admin_list_requests() from public, anon;
revoke execute on function public.osint_admin_review_request(uuid,text,text) from public, anon;
revoke execute on function public.osint_request_access(text,text) from public, anon;

grant execute on function public.dlr_claim_account_notifications(uuid,text,integer) to authenticated, service_role;
grant execute on function public.dlr_mark_account_notification_sent(uuid,uuid,text) to authenticated, service_role;
grant execute on function public.osint_admin_list_requests() to authenticated, service_role;
grant execute on function public.osint_admin_review_request(uuid,text,text) to authenticated, service_role;
grant execute on function public.osint_request_access(text,text) to authenticated, service_role;
