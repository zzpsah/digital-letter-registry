# Runtime Verification — Security

- Synthetic data only.
- Never store project refs, owner UUIDs, access/refresh tokens, OAuth credentials, API keys, Drive IDs, SSH/server details, or private URLs in Git.
- RLS remains the authorization boundary for ordinary database access.
- Browser auth tokens remain server-side/HttpOnly.
- No real data, deployment, import, connector activation, or rename is authorized by this enhancement.
