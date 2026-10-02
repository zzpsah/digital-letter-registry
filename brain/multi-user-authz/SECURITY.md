# Multi-user authorization — Security

- Authorization uses stable Supabase user id + active archive membership.
- Never authorize from email domain, Google/Gmail status, or `user_metadata`.
- Registration is invite-only.
- A Supabase Auth user without membership has no archive access.
- Admin/editor/viewer boundaries are enforced by database RLS and server authorization.
- The final active admin cannot be demoted, disabled, or removed.
- Supabase service-role is not a human login mechanism.
- Invite codes are high-entropy UUID secrets bound to the invited email and archive invite record.
- Invite codes are placed in URL fragments to avoid normal request/referrer logging and are cleared after prefill.
- Google Drive OAuth is independent of DLR user authentication.
- Real archive mutations remain subject to existing approval/safety gates.
- Supabase security advisor currently reports leaked-password protection disabled; enable it when Auth configuration access is available.
- Public SECURITY DEFINER RPCs used for invite/admin lifecycle must retain explicit fail-closed checks and fixed `search_path`; do not weaken them to silence a linter.
