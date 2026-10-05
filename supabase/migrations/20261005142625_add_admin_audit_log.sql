create table if not exists public.admin_audit_log (
  id uuid primary key default gen_random_uuid(),
  archive_id uuid not null references public.archives(id) on delete cascade,
  actor_user_id uuid not null references auth.users(id) on delete restrict,
  action text not null check (length(action) between 1 and 120),
  target_type text not null check (length(target_type) between 1 and 80),
  target_id text,
  detail jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists admin_audit_log_archive_created_idx
  on public.admin_audit_log (archive_id, created_at desc);

alter table public.admin_audit_log enable row level security;
revoke all on table public.admin_audit_log from anon;
revoke all on table public.admin_audit_log from authenticated;
grant select, insert on table public.admin_audit_log to authenticated;

drop policy if exists "admins read audit log" on public.admin_audit_log;
create policy "admins read audit log"
on public.admin_audit_log for select to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "admins append audit log" on public.admin_audit_log;
create policy "admins append audit log"
on public.admin_audit_log for insert to authenticated
with check (
  (select private.archive_member_role(archive_id)) = 'admin'
  and actor_user_id = (select auth.uid())
);
