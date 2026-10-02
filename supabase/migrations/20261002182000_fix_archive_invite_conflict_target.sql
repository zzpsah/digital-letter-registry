-- Avoid PL/pgSQL output-column ambiguity in the invite upsert conflict target.

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
