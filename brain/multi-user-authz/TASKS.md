# Multi-user authorization — Tasks

- [x] Inspect current schema/RLS/API assumptions.
- [x] Add archive + membership role schema/migrations.
- [x] Bootstrap existing owner as admin.
- [x] Replace owner-only session authorization with membership authorization.
- [x] Define admin/editor/viewer permissions.
- [x] Add invite-only user/account lifecycle foundation.
- [x] Add email/password login independent of Gmail.
- [x] Add admin access-management API/UI.
- [x] Add last-admin database protection.
- [x] Apply membership/role/invite migrations to hosted Supabase.
- [x] Verify hosted membership state.
- [x] Verify last-admin protection live.
- [x] Harden invite links to URL fragments.
- [x] Full synthetic suite passes 249/249.
- [ ] Enable Supabase leaked-password protection.
- [ ] Invite/create an additional dedicated admin when the intended email is chosen.
- [ ] Complete real authenticated multi-role HTTP/PostgREST vertical slice.


- [x] Verify hosted admin/editor/viewer/non-member RLS matrix with synthetic JWT claims.
- [x] Verify zero synthetic residue after hosted role tests.
- [x] Add one-click registration email action for pending invites.
- [ ] Complete real owner bearer-session/PostgREST vertical slice through normal browser completion.
