# Google Sign-In — Architecture

```text
Private DLR URL over Tailscale
  -> /api/v1/auth/providers
  -> if Google enabled: "Google se sign in"
  -> /auth/google
  -> Supabase Auth social authorize endpoint
  -> Google Web OAuth client
  -> Supabase Auth callback
  -> DLR /auth/confirm
  -> validate Supabase session + owner id
  -> HttpOnly access/refresh cookies
  -> Supabase RLS using auth.uid()
```

Magic Link remains a fallback authentication path to the same DLR session/RLS layer.

## Separation of concerns
- Tailscale: private network reachability.
- Google Sign-In / Magic Link: user identity.
- Supabase session: authenticated application session.
- Supabase RLS: database authorization.
- Google Drive OAuth: backend archive storage authorization.
- DLR approval gates: real ingestion/rename/delete/import authorization.
