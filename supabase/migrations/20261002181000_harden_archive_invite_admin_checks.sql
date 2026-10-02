-- Fail closed when the caller has no archive membership.
-- In PL/pgSQL, IF NULL does not enter the branch, so use IS DISTINCT FROM.

create or replace function public.dlr_invite_archive_member(
  target_archive_id uuid,
  target_email text,
  target_role text
)
returns table (
  invite_id uuid,
  email text,
  role text,
  status text,
  invite_code uuid,
  user_id uuid
)
language plpgsql
security definer
set search_path = ''
as $$
declare
  normalized_email text := lower(btrim(target_email));
  matched_user_id uuid;
  result_invite public.archive_member_invites%rowtype;
  existing_role text;
begin
  if (select private.archive_member_role(target_archive_id)) is distinct from 'admin' then
    raise exception 'archive admin required';
  end if;
  if length(normalized_email) not between 3 and 320
     or position('@' in normalized_email) <= 1 then
    raise exception 'valid email required';
  end if;
  if target_role not in ('admin','editor','viewer') then
    raise exception 'invalid archive role';
  end if;

  select u.id
    into matched_user_id
  from auth.users u
  where lower(u.email) = normalized_email
    and u.email_confirmed_at is not null
  order by u.created_at
  limit 1;

  if matched_user_id is not null then
    select m.role
      into existing_role
    from public.archive_members m
    where m.archive_id = target_archive_id
      and m.user_id = matched_user_id;

    if existing_role is null then
      insert into public.archive_members (
        archive_id, user_id, role, status
      )
      values (
        target_archive_id, matched_user_id, target_role, 'active'
      );
    end if;

    insert into public.archive_member_invites (
      archive_id,
      email,
      role,
      status,
      invited_by,
      accepted_user_id,
      accepted_at
    )
    values (
      target_archive_id,
      normalized_email,
      coalesce(existing_role, target_role),
      'accepted',
      (select auth.uid()),
      matched_user_id,
      now()
    )
    on conflict on constraint archive_member_invites_archive_id_email_key
    do update set
      role = excluded.role,
      status = 'accepted',
      invited_by = excluded.invited_by,
      accepted_user_id = excluded.accepted_user_id,
      accepted_at = excluded.accepted_at,
      updated_at = now()
    returning * into result_invite;
  else
    insert into public.archive_member_invites (
      archive_id,
      email,
      role,
      status,
      invite_code,
      invited_by,
      accepted_user_id,
      accepted_at
    )
    values (
      target_archive_id,
      normalized_email,
      target_role,
      'pending',
      extensions.gen_random_uuid(),
      (select auth.uid()),
      null,
      null
    )
    on conflict on constraint archive_member_invites_archive_id_email_key
    do update set
      role = excluded.role,
      status = 'pending',
      invite_code = excluded.invite_code,
      invited_by = excluded.invited_by,
      accepted_user_id = null,
      accepted_at = null,
      updated_at = now()
    returning * into result_invite;
  end if;

  return query
  select
    result_invite.id,
    result_invite.email,
    result_invite.role,
    result_invite.status,
    result_invite.invite_code,
    result_invite.accepted_user_id;
end
$$;

create or replace function public.dlr_list_archive_access(
  target_archive_id uuid
)
returns table (
  kind text,
  record_id uuid,
  user_id uuid,
  email text,
  role text,
  status text,
  invite_code uuid,
  created_at timestamptz
)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if (select private.archive_member_role(target_archive_id)) is distinct from 'admin' then
    raise exception 'archive admin required';
  end if;

  return query
  select
    'member'::text,
    m.user_id,
    m.user_id,
    lower(u.email),
    m.role,
    m.status,
    null::uuid,
    m.created_at
  from public.archive_members m
  join auth.users u on u.id = m.user_id
  where m.archive_id = target_archive_id

  union all

  select
    'invite'::text,
    i.id,
    i.accepted_user_id,
    i.email,
    i.role,
    i.status,
    case when i.status = 'pending' then i.invite_code else null::uuid end,
    i.created_at
  from public.archive_member_invites i
  where i.archive_id = target_archive_id
    and i.status <> 'accepted'

  order by created_at;
end
$$;

create or replace function public.dlr_update_archive_member(
  target_archive_id uuid,
  target_user_id uuid,
  target_role text,
  target_status text
)
returns table (
  user_id uuid,
  email text,
  role text,
  status text
)
language plpgsql
security definer
set search_path = ''
as $$
begin
  if (select private.archive_member_role(target_archive_id)) is distinct from 'admin' then
    raise exception 'archive admin required';
  end if;
  if target_role not in ('admin','editor','viewer') then
    raise exception 'invalid archive role';
  end if;
  if target_status not in ('active','disabled') then
    raise exception 'invalid member status';
  end if;

  update public.archive_members m
  set role = target_role,
      status = target_status,
      updated_at = now()
  where m.archive_id = target_archive_id
    and m.user_id = target_user_id;

  if not found then
    raise exception 'archive member not found';
  end if;

  return query
  select
    m.user_id,
    lower(u.email),
    m.role,
    m.status
  from public.archive_members m
  join auth.users u on u.id = m.user_id
  where m.archive_id = target_archive_id
    and m.user_id = target_user_id;
end
$$;

create or replace function public.dlr_revoke_archive_invite(
  target_archive_id uuid,
  target_invite_id uuid
)
returns table (revoked boolean)
language plpgsql
security definer
set search_path = ''
as $$
declare
  did_revoke boolean;
begin
  if (select private.archive_member_role(target_archive_id)) is distinct from 'admin' then
    raise exception 'archive admin required';
  end if;

  update public.archive_member_invites i
  set status = 'revoked',
      updated_at = now()
  where i.archive_id = target_archive_id
    and i.id = target_invite_id
    and i.status = 'pending';

  did_revoke := found;
  return query select did_revoke;
end
$$;
