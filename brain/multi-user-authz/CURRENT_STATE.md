# Multi-user authorization — Current State

Last updated: 2026-10-02.

## Hosted state
- Archive membership migrations are applied in Supabase.
- Current archive membership: one active admin; no editor/viewer/disabled members.
- Pending invites: zero.
- Real archive letter rows: zero.
- Last-active-admin protection was verified live by attempting to disable the sole admin; the database rejected it and membership state remained unchanged.

## Application state
- Email/password login is implemented and does not require Gmail.
- Registration is invite-only.
- Magic Link remains fallback/recovery.
- Google Sign-In is optional and currently disabled at the hosted provider level.
- Admin UI/API can invite users, assign admin/editor/viewer, change role/status, list access, and revoke pending invites.
- A Supabase Auth account without active archive membership receives no archive access.
- Invite links use URL fragments rather than query strings and the browser clears the fragment after prefill.
- Auth provider endpoint reports password=true, magic_link=true, registration_mode=invite_only.
- Full synthetic suite passes 249/249.

## Security observations
- Supabase security advisor reports leaked-password protection disabled; enabling it is pending external Auth configuration.
- SECURITY DEFINER advisor warnings exist for invitation/admin RPCs. These functions are intentionally privileged but contain explicit archive-admin or invite-secret checks and fixed search paths; retain review before changing them.
