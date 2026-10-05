-- Retire failed processing jobs without deleting the letter.
alter type public.processing_job_status add value if not exists 'retired';

-- Approval notification is sent after account activation, so completed requests
-- with no approval notification are eligible for the approval email.
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
        and r.status in ('approved','completed')
        and r.approval_notified_at is null
      order by r.approved_at
      limit greatest(1, least(coalesce(result_limit,20),100));
  else
    raise exception 'invalid notification kind';
  end if;
end;
$$;

revoke all on function public.dlr_claim_account_notifications(uuid,text,integer) from public;
grant execute on function public.dlr_claim_account_notifications(uuid,text,integer) to authenticated;
