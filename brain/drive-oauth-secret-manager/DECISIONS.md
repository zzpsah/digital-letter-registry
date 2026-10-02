# Drive OAuth Secret Manager — Decisions

1. Runtime-injected refresh credentials take precedence over the authorized-user file fallback.
2. Direct Google OAuth/Drive API is the DLR storage path; unrelated rclone credentials are not reused.
3. Secret-manager injection must be scoped to the DLR OAuth keys rather than exposing an entire secret inventory to the child process.
4. Access tokens remain in memory only.
5. Write-capable OAuth permission does not authorize real archive mutation; synthetic/approval gates remain independent.
