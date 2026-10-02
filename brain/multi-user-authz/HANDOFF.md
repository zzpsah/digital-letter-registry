# Multi-user authorization — Handoff

Multi-user account/role foundation is implemented and live.

Current model:
- any valid email provider may be used;
- email/password is native login;
- Magic Link is fallback/recovery;
- Google Sign-In is optional;
- registration is invite-only;
- active archive membership controls access;
- roles: admin/editor/viewer;
- bootstrap owner is currently the sole active admin;
- last-admin protection is live and verified;
- admin invite/member-management UI/API is implemented;
- invite links use `#invite=` and clear the secret after prefill;
- full suite passes 249/249.

Do not create a second admin with an invented email. Once the user chooses the actual dedicated admin email, invite it with role=admin and complete its registration/sign-in. Then verify a real editor/viewer session path as part of the pending HTTP/PostgREST vertical slice.

Security hardening still pending: enable Supabase leaked-password protection when Auth configuration access is available.
