# Drive OAuth Secret Manager — Current State

Last updated: 2026-10-09.

Verified on the private Oracle runtime:
- OAuth client id/client secret/refresh token were migrated into the approved secret manager.
- The DLR process receives only the mapped OAuth variables through scoped injection.
- Secret-manager-only OAuth refresh, originals listing and synthetic original streaming passed.
- The persistent authorized-user credential file was retired after verification.
- The private API service remained healthy after cutover.

## 7-day expiry fixed by publishing the OAuth app — 2026-10-09

- The Drive refresh token expired 2026-10-09 14:29 UTC, exactly 7 days after issue, because the OAuth client
  was still in Testing mode. Testing mode gives external-user refresh tokens a 7-day lifetime.
- The OAuth app was published from Testing to In production, which removes that recurring expiry. In production
  the refresh token persists while it is used regularly; a long-unused token can still be invalidated.
- Re-consent for the archive owner `umvtetahali@gmail.com` completed through a loopback PKCE callback on
  `http://127.0.0.1:53682/callback`. Google accepts only loopback redirect URIs for this client, so no tailnet or
  remote callback URL works; the consent browser must run on the same host as the callback listener.
- The refreshed token was verified live (Drive scope, `originals` folder reachable) and rotated into Bitwarden
  Secrets Manager with `scripts/dlr-bitwarden-google-oauth.py --source <handoff> --apply --replace-existing`.
  A Bitwarden-only refresh then returned HTTP 200.
- Retired after the rotation: the OAuth handoff file, the temporary consent helper unit, and the copied Chrome
  profile used to drive the DevTools consent session.

Completed from the earlier pending list:
- write-capable Google Drive re-consent completed;
- refresh token rotation in the secret manager completed;
- synthetic upload/write/stream/delete cleanup verification passed.

