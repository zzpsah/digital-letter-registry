# Drive OAuth Secret Manager — Project

## Purpose
Keep Google Drive OAuth refresh credentials out of repository files and application configuration while preserving direct Google Drive API access.

## Success criteria
- Refreshable OAuth works with process-start secret injection.
- File-based authorized-user credentials remain only an optional local/migration fallback.
- Runtime secret values are never printed or committed.
- Read/list/stream and write verification use synthetic data only.
- rclone is not a DLR storage-auth dependency.
