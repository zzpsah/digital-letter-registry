# Google Sign-In — Handoff

Read project rules, root TASKS, .ai state, brain/HANDOFF.md and this folder before continuing.

## Current resume point
Code is complete and synthetic tests pass. Supabase currently reports the Google provider disabled because a separate Google Web OAuth client has not yet been configured.

Do not reuse DLR Drive OAuth credentials; that client is for backend Drive access.

Next:
1. Create Google Web application OAuth client.
2. Register the exact private DLR origin as an authorized JavaScript origin.
3. Register the hosted Supabase Auth callback URI as an authorized redirect URI.
4. Store client id/secret in the approved secret store.
5. Enable Supabase Google provider.
6. Confirm /api/v1/auth/providers reports google=true.
7. Sign in with the existing archive-owner Google account.
8. Verify auth.identities now contains both email and google for the same Supabase user id.
9. Execute the real authenticated synthetic owner/RLS vertical slice.
