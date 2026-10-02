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


## Latest verification

- Hosted admin/editor/viewer/non-member RLS matrix verified with synthetic JWT-claim simulation.
- All expected role boundaries passed.
- Cleanup verified with no synthetic residue.
- Admin UI now supports one-click registration email for pending invites using the existing invite-validated registration Magic Link path.
- Copy-invite links and email onboarding use fragment-based invite secrets.
- Full synthetic suite: 251/251 passed.
- Fresh owner Magic Link delivery is working again. Automated redemption of the one-time email credential was not forwarded into remote execution; the real short-lived owner bearer-session/PostgREST vertical slice therefore remains pending.


## Password setup

- Authenticated archive members can set/change password through DLR.
- The update is performed against the authenticated Supabase user and does not alter archive membership/role.
- Signed-in Account UI includes new-password + confirmation fields.
- Unauthenticated change attempt returns 401.
- Full suite now passes 255/255.
- Bootstrap admin first password setup is pending one normal browser/email session.


## Magic Link callback fix — 2026-10-03

A real bootstrap-admin Magic Link was successfully redeemed by Supabase, but the DLR fragment bridge returned HTTP 422 before session cookies were created. Supabase user identity and active admin membership matched correctly.

The DLR fragment request model no longer assumes fixed provider token lengths or a minimum 60-second expiry. Token format is now treated as provider-owned; DLR still validates the access token against Supabase and confirms active archive membership before issuing HttpOnly cookies.

Verification:
- focused API tests pass;
- full suite passes 256/256;
- private service restarted healthy.

A fresh email send was rate-limited, so browser retry is pending using an earlier unconsumed Magic Link if still valid.


## Second admin onboarding

A second administrator invitation is pending through the normal invite-only onboarding flow. The registration email was sent successfully. Supabase created the unconfirmed Auth user with the invite metadata, while archive membership remains absent until email ownership is confirmed.

The existing database trigger `dlr_claim_archive_invite_on_auth_user` runs after user insert or email confirmation update. Once the invited email is confirmed, it will atomically create/update the active archive admin membership and mark the invite accepted.

No raw Auth-user insertion or confirmation bypass was used.
