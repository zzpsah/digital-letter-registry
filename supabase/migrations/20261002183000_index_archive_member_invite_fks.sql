create index if not exists archive_member_invites_invited_by_idx
  on public.archive_member_invites (invited_by);

create index if not exists archive_member_invites_accepted_user_idx
  on public.archive_member_invites (accepted_user_id)
  where accepted_user_id is not null;
