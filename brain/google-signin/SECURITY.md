# Google Sign-In — Security

- Google Sign-In credentials are separate from Google Drive OAuth credentials.
- Use a Web application OAuth client for browser login.
- Do not commit client secrets or tokens.
- Keep canonical secret values in the approved secret manager.
- DLR validates the Supabase user id against the configured archive-owner id before accepting a fragment session.
- Database authorization remains auth.uid() = owner_id.
- HttpOnly, Secure, SameSite=Lax cookies hold DLR session tokens.
- Refresh cookies persist by default for 30 days but Supabase remains authoritative for session validity/revocation.
- Magic Link fallback does not weaken the owner-id check.
- Do not infer authorization from Google profile/user metadata.
