# Drive OAuth Secret Manager — Current State

Last updated: 2026-10-02.

Verified on the private Oracle runtime:
- OAuth client id/client secret/refresh token were migrated into the approved secret manager.
- The DLR process receives only the mapped OAuth variables through scoped injection.
- Secret-manager-only OAuth refresh, originals listing and synthetic original streaming passed.
- The persistent authorized-user credential file was retired after verification.
- The private API service remained healthy after cutover.

Pending:
- write-capable Google Drive re-consent completed;
- refresh token rotation in the secret manager completed;
- synthetic upload/write/stream/delete cleanup verification passed.
