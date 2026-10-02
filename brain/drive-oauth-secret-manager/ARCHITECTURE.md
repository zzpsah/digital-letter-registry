# Drive OAuth Secret Manager — Architecture

```text
private service launcher
  -> approved read-only secret-manager identity
  -> explicit OAuth key allowlist
  -> GOOGLE_OAUTH_CLIENT_ID / CLIENT_SECRET / REFRESH_TOKEN
  -> GoogleRefreshTokenProvider
  -> in-memory access token cache
  -> Google Drive API reader/catalog/writer/renamer
```

The application does not need the secret-manager machine credential itself. File-based authorized-user credentials remain supported only as a fallback for local/migration use.
