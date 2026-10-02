# Google Sign-In — Decisions

1. Google Sign-In is the preferred user experience; Magic Link remains fallback/recovery.
2. Do not reuse the Google Drive desktop OAuth client for user Sign-In.
3. Google Sign-In requires its own Google Web application OAuth client.
4. Existing Supabase email identity should be preserved; same-email verified Google identity should link to the existing user rather than create a new archive owner.
5. DLR still validates the returned Supabase user id against the configured archive-owner id before setting application cookies.
6. Refresh cookies persist for 30 days by default to avoid repeated sign-in after browser restarts.
7. Supabase may still invalidate/revoke/expire a session earlier; DLR then clears cookies and requires authentication again.
8. Authentication never grants Google Drive permissions or consequential archive mutation permissions.
