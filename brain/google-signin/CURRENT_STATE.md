# Google Sign-In — Current State

Last updated: 2026-10-02.

## Implemented
- Public provider-status endpoint reports whether Supabase Google Auth is enabled.
- Google login route redirects to the Supabase social OAuth authorize endpoint only when the provider is enabled.
- Hindi-first UI treats Google Sign-In as primary when available.
- Email Magic Link is retained in a collapsed fallback section.
- Existing fragment-to-HttpOnly-session bridge is reused for OAuth return sessions.
- Non-owner Supabase sessions remain rejected before DLR cookies are set.
- Refresh-session cookie now persists for 30 days by default and continues to rotate through Supabase refresh responses.
- Refresh-cookie lifetime is configurable from 1 to 90 days.
- Full synthetic suite: 220/220 passed.

## Live external state
- Supabase Google provider currently reports disabled.
- No separate DLR Google Web OAuth client credentials are currently present in the approved secret store.
- Existing DLR Google Drive OAuth credentials are separate and must not be reused for Sign-In.

## Pending one-time external configuration
1. Create a Google OAuth client of type Web application.
2. Register the DLR application origin and the Supabase Auth callback URI.
3. Store the Sign-In client id/secret in the approved secret manager.
4. Configure the Supabase Google Auth provider with that Web client.
5. Verify Google login with the existing archive-owner account.
6. Confirm the Google identity links to the existing Supabase user id.
7. Run the authenticated synthetic owner/RLS vertical slice.
