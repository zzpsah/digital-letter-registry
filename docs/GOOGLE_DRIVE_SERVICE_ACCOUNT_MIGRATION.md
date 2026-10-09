# DLR Google Drive service-account migration

## Goal

Use a service-account identity to mint short-lived Drive access tokens at runtime.
Do not depend on a human user's refresh token. Access tokens are memory-only; the
service-account private key remains in a permission-restricted runtime file and
must never be committed or logged.

## Prerequisites (Google Cloud / Drive admin action)

1. In the Google Cloud project that owns the enabled Google Drive API, create a
   service account dedicated to DLR. Grant only the API/project permissions needed.
2. Prefer keyless Workload Identity Federation if the hosting identity provider can
   be configured. If a key file is required on this non-Google-Cloud VPS, create one
   deliberately, store the JSON only in the approved secret manager, and rotate it
   under a documented process.
3. **Confirm the archive destination before changing it.** Google service accounts
   have no Drive storage quota and cannot own files. The destination must be a
   Google Workspace Shared Drive with the service account added with the minimum
   required role (normally Contributor/Writer for new uploads and Editor-level
   capability if rename/replace/trash operations are required). A personal Gmail
   My Drive folder is not a valid destination for service-account-owned uploads.
4. Do not move, delete, or bulk-copy existing archive files as part of authentication
   setup. Preserve all existing Drive IDs and database references. If Shared Drive
   migration is needed, plan and test it separately.
5. Put the service-account JSON at
   `/home/prashant/.config/dlr/google-service-account.json`, owned by `prashant`,
   mode `0600`, with the parent directory mode `0700`. Do not put it in Git, `.env`,
   logs, or the WhatsApp queue.

## Runtime behavior

The DLR Drive auth provider selects `GOOGLE_SERVICE_ACCOUNT_FILE` before legacy OAuth
configuration. The WhatsApp wrapper sets that variable only when the protected key
file exists, allowing a controlled migration without interrupting intake. Once the
service-account path is proven, remove `DLR_GOOGLE_OAUTH_CLIENT_ID`,
`DLR_GOOGLE_OAUTH_CLIENT_SECRET`, and `DLR_GOOGLE_DRIVE_REFRESH_TOKEN` from the
Bitwarden scope and remove the legacy provider in a separate reviewed change.

## Acceptance checks before cutover

- `python -m unittest tests.test_google_drive_auth tests.test_runtime_readiness` passes.
- Service-account token minting succeeds without exposing token/key material.
- Service account can create a **synthetic test file** in the configured destination,
  read/download it, rename it, and trash/restore it if those operations are needed.
- The synthetic file is removed after testing; no real archive items are modified.
- A synthetic WhatsApp attachment passes intake through database persistence and
  private original retrieval. Existing pending items remain untouched until all checks
  pass, then the consumer is resumed and verified over multiple timer intervals.
- Confirm runtime readiness reports Drive configured without returning secrets.

## Rollback

Do not delete legacy credentials or change the destination until the service-account
path passes end-to-end tests. During the migration window, absence of the protected key
file leaves the existing provider selection unchanged. If service-account auth fails,
remove the key file from the runtime path and investigate; do not discard pending
WhatsApp attachments or reset the archive.
