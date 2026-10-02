create table if not exists public.archive_member_invites (
  id uuid primary key default extensions.gen_random_uuid(),
  archive_id uuid not null references public.archives(id) on delete cascade,
  email text not null check (
    email = lower(btrim(email))
    and length(email) between 3 and 320
    and position('@' in email) > 1
  ),
  role text not null check (role in ('admin','editor','viewer')),
  status text not null default 'pending'
    check (status in ('pending','accepted','revoked')),
  invite_code uuid not null default extensions.gen_random_uuid(),
  invited_by uuid not null references auth.users(id) on delete restrict,
  accepted_user_id uuid references auth.users(id) on delete set null,
  accepted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (archive_id, email),
  unique (invite_code)
);

create index if not exists archive_member_invites_archive_status_idx
  on public.archive_member_invites (archive_id, status, created_at desc);

alter table public.archive_member_invites enable row level security;

revoke all on table public.archive_member_invites from anon;
revoke all on table public.archive_member_invites from authenticated;
grant select, insert, update, delete on table public.archive_member_invites
  to authenticated;

drop policy if exists "admins read archive invites"
  on public.archive_member_invites;
create policy "admins read archive invites"
on public.archive_member_invites
for select
to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "admins add archive invites"
  on public.archive_member_invites;
create policy "admins add archive invites"
on public.archive_member_invites
for insert
to authenticated
with check ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "admins update archive invites"
  on public.archive_member_invites;
create policy "admins update archive invites"
on public.archive_member_invites
for update
to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin')
with check ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "admins delete archive invites"
  on public.archive_member_invites;
create policy "admins delete archive invites"
on public.archive_member_invites
for delete
to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

create or replace function public.dlr_validate_archive_invite(
  target_email text,
  target_invite_code uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.archive_member_invites i
    join public.archives a on a.id = i.archive_id
    where i.email = lower(btrim(target_email))
      and i.invite_code = target_invite_code
      and i.status = 'pending'
      and a.status = 'active'
  )
$$;

revoke all on function public.dlr_validate_archive_invite(text, uuid)
  from public;
grant execute on function public.dlr_validate_archive_invite(text, uuid)
  to anon, authenticated;

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
  if (select private.archive_member_role(target_archive_id)) <> 'admin' then
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
    on conflict (archive_id, email)
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
    on conflict (archive_id, email)
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

revoke all on function public.dlr_invite_archive_member(uuid, text, text)
  from public;
revoke all on function public.dlr_invite_archive_member(uuid, text, text)
  from anon;
grant execute on function public.dlr_invite_archive_member(uuid, text, text)
  to authenticated;

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
  if (select private.archive_member_role(target_archive_id)) <> 'admin' then
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

revoke all on function public.dlr_list_archive_access(uuid) from public;
revoke all on function public.dlr_list_archive_access(uuid) from anon;
grant execute on function public.dlr_list_archive_access(uuid)
  to authenticated;

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
  if (select private.archive_member_role(target_archive_id)) <> 'admin' then
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

revoke all on function public.dlr_update_archive_member(uuid, uuid, text, text)
  from public;
revoke all on function public.dlr_update_archive_member(uuid, uuid, text, text)
  from anon;
grant execute on function public.dlr_update_archive_member(uuid, uuid, text, text)
  to authenticated;

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
  if (select private.archive_member_role(target_archive_id)) <> 'admin' then
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

revoke all on function public.dlr_revoke_archive_invite(uuid, uuid)
  from public;
revoke all on function public.dlr_revoke_archive_invite(uuid, uuid)
  from anon;
grant execute on function public.dlr_revoke_archive_invite(uuid, uuid)
  to authenticated;

create or replace function private.claim_archive_invite_for_auth_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  candidate public.archive_member_invites%rowtype;
  supplied_code uuid;
begin
  if new.email is null or new.email_confirmed_at is null then
    return new;
  end if;

  begin
    supplied_code := nullif(
      new.raw_user_meta_data ->> 'dlr_invite_code',
      ''
    )::uuid;
  exception when invalid_text_representation then
    supplied_code := null;
  end;

  if supplied_code is null then
    return new;
  end if;

  for candidate in
    select i.*
    from public.archive_member_invites i
    where i.email = lower(btrim(new.email))
      and i.invite_code = supplied_code
      and i.status = 'pending'
    order by i.created_at
  loop
    insert into public.archive_members (
      archive_id, user_id, role, status
    )
    values (
      candidate.archive_id, new.id, candidate.role, 'active'
    )
    on conflict (archive_id, user_id)
    do update set
      role = excluded.role,
      status = 'active',
      updated_at = now();

    update public.archive_member_invites
    set status = 'accepted',
        accepted_user_id = new.id,
        accepted_at = now(),
        updated_at = now()
    where id = candidate.id
      and status = 'pending';
  end loop;

  return new;
end
$$;

revoke all on function private.claim_archive_invite_for_auth_user()
  from public;
revoke all on function private.claim_archive_invite_for_auth_user()
  from anon;

drop trigger if exists dlr_claim_archive_invite_on_auth_user
  on auth.users;
create trigger dlr_claim_archive_invite_on_auth_user
after insert or update of email_confirmed_at on auth.users
for each row execute function private.claim_archive_invite_for_auth_user();
