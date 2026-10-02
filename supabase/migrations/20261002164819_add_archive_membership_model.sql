create schema if not exists private;
revoke all on schema private from public;
revoke all on schema private from anon;
grant usage on schema private to authenticated;

create table if not exists public.archives (
  id uuid primary key default extensions.gen_random_uuid(),
  name text not null check (length(btrim(name)) > 0),
  status text not null default 'active'
    check (status in ('active','disabled')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.archive_members (
  archive_id uuid not null references public.archives(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('admin','editor','viewer')),
  status text not null default 'active'
    check (status in ('active','disabled')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (archive_id, user_id)
);

create index if not exists archive_members_user_status_idx
  on public.archive_members (user_id, status, archive_id);

alter table public.archives enable row level security;
alter table public.archive_members enable row level security;

revoke all on table public.archives from anon;
revoke all on table public.archive_members from anon;
revoke all on table public.archives from authenticated;
revoke all on table public.archive_members from authenticated;
grant select, update on table public.archives to authenticated;
grant select, insert, update, delete on table public.archive_members to authenticated;

create or replace function private.archive_member_role(target_archive_id uuid)
returns text
language sql
stable
security definer
set search_path = ''
as $$
  select m.role
  from public.archive_members m
  where m.archive_id = target_archive_id
    and m.user_id = (select auth.uid())
    and m.status = 'active'
  limit 1
$$;

revoke all on function private.archive_member_role(uuid) from public;
revoke all on function private.archive_member_role(uuid) from anon;
grant execute on function private.archive_member_role(uuid) to authenticated;

drop policy if exists "members read archives" on public.archives;
create policy "members read archives"
on public.archives
for select
to authenticated
using ((select private.archive_member_role(id)) is not null);

drop policy if exists "admins update archives" on public.archives;
create policy "admins update archives"
on public.archives
for update
to authenticated
using ((select private.archive_member_role(id)) = 'admin')
with check ((select private.archive_member_role(id)) = 'admin');

drop policy if exists "members read archive membership" on public.archive_members;
create policy "members read archive membership"
on public.archive_members
for select
to authenticated
using (
  user_id = (select auth.uid())
  or (select private.archive_member_role(archive_id)) = 'admin'
);

drop policy if exists "admins add archive members" on public.archive_members;
create policy "admins add archive members"
on public.archive_members
for insert
to authenticated
with check ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "admins update archive members" on public.archive_members;
create policy "admins update archive members"
on public.archive_members
for update
to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin')
with check ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "admins remove archive members" on public.archive_members;
create policy "admins remove archive members"
on public.archive_members
for delete
to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

create or replace function private.protect_last_archive_admin()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if old.role = 'admin'
     and old.status = 'active'
     and (
       tg_op = 'DELETE'
       or new.role <> 'admin'
       or new.status <> 'active'
     )
  then
    if not exists (
      select 1
      from public.archive_members m
      where m.archive_id = old.archive_id
        and m.user_id <> old.user_id
        and m.role = 'admin'
        and m.status = 'active'
    ) then
      raise exception 'archive must retain at least one active admin';
    end if;
  end if;

  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end
$$;

revoke all on function private.protect_last_archive_admin() from public;
revoke all on function private.protect_last_archive_admin() from anon;

drop trigger if exists archive_members_protect_last_admin on public.archive_members;
create trigger archive_members_protect_last_admin
before update or delete on public.archive_members
for each row execute function private.protect_last_archive_admin();

alter table public.letters
  add column if not exists archive_id uuid references public.archives(id) on delete restrict;
alter table public.letter_processing
  add column if not exists archive_id uuid references public.archives(id) on delete restrict;
alter table public.letter_relationships
  add column if not exists archive_id uuid references public.archives(id) on delete restrict;
alter table public.letter_chunks
  add column if not exists archive_id uuid references public.archives(id) on delete restrict;
alter table public.processing_jobs
  add column if not exists archive_id uuid references public.archives(id) on delete restrict;
alter table public.processing_profiles
  add column if not exists archive_id uuid references public.archives(id) on delete restrict;
alter table public.letter_sources
  add column if not exists archive_id uuid references public.archives(id) on delete restrict;

create index if not exists letters_archive_idx on public.letters (archive_id);
create index if not exists letter_processing_archive_idx on public.letter_processing (archive_id);
create index if not exists letter_relationships_archive_idx on public.letter_relationships (archive_id);
create index if not exists letter_chunks_archive_idx on public.letter_chunks (archive_id);
create index if not exists processing_jobs_archive_idx on public.processing_jobs (archive_id);
create index if not exists processing_profiles_archive_idx on public.processing_profiles (archive_id);
create index if not exists letter_sources_archive_idx on public.letter_sources (archive_id);
