create index if not exists admin_audit_log_actor_user_idx
  on public.admin_audit_log (actor_user_id);
