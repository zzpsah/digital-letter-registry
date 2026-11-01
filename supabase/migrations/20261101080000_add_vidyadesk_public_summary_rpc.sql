-- Aggregate-only DLR summary for VidyaDesk.
--
-- The RPC is callable only by authenticated archive members and independently
-- re-checks that the caller is a viewer of the requested archive. It returns
-- two aggregate values and never exposes letter rows or metadata.

create or replace function public.vidyadesk_public_archive_summary(
  target_archive_id uuid
)
returns table (
  public_document_count bigint,
  latest_public_document_at timestamptz
)
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  member_role text;
begin
  member_role := private.archive_member_role(target_archive_id);
  if member_role is distinct from 'viewer' then
    raise exception 'viewer archive membership required'
      using errcode = '42501';
  end if;

  if not exists (
    select 1
      from public.archives a
     where a.id = target_archive_id
       and a.status = 'active'
  ) then
    raise exception 'active archive required'
      using errcode = '42501';
  end if;

  return query
    select count(*)::bigint, max(l.uploaded_at)
      from public.letters l
     where l.archive_id = target_archive_id
       and l.visibility = 'public'
       and l.is_archived = false;
end;
$$;

revoke all on function public.vidyadesk_public_archive_summary(uuid) from public;
revoke all on function public.vidyadesk_public_archive_summary(uuid) from anon;
grant execute on function public.vidyadesk_public_archive_summary(uuid) to authenticated;
