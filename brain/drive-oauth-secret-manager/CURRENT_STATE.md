# Drive OAuth Secret Manager — Current State

Last updated: 2026-10-02.

Verified on the private Oracle runtime:
- OAuth client id/client secret/refresh token were migrated into the approved secret manager.
- The DLR process receives only the mapped OAuth variables through scoped injection.
- Secret-manager-only OAuth refresh, originals listing and synthetic original streaming passed.
- The persistent authorized-user credential file was retired after verification.
- The private API service remained healthy after cutover.

Pending:
- complete the approved write-capable Google Drive re-consent;
- rotate the refresh token in the secret manager;
- run synthetic upload/write/cleanup verification.
