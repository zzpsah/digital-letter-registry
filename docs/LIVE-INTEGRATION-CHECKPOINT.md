# Live Integration Checkpoint

Last verified: 2026-10-02

## Completed

- Private archive Drive structure is reachable.
- A synthetic PDF was generated and uploaded successfully into the private `originals/` folder and verified private/not shared.
- The synthetic PDF uses the approved archive filename convention and has a computed SHA-256 fingerprint.
- Supabase archive-owner Auth identity exists and the owner email is confirmed.
- DB-level owner access and cross-user RLS isolation have been verified with rollback-only synthetic transactions.
- Server-side token-hash passwordless callback + Secure HttpOnly cookie session/refresh flow are implemented.
- Oracle ARM64 checkout is current, a Python 3.12 project virtualenv is installed, and the synthetic suite passes 188/188.
- Localhost-only FastAPI smoke test passed: health/PWA 200, unauthenticated session/search 401.
- Duplicate `processing_profiles` RLS policy residue was removed; advisor now reports only expected unused-index informational notices.

## Pending runtime verification

1. Configure a short-lived authenticated archive-owner session in runtime secret storage.
2. Run the guarded synthetic Data API insert/read/duplicate-protection command.
3. Verify the synthetic HTTP intake → Drive → queue → worker → search/open-original vertical slice.
4. Verify refreshable Google Drive OAuth credentials with live original streaming.
5. Install and verify Oracle OCR runtime packages: Tesseract + `hin` + `eng` + OCRmyPDF. ARM64 packages are available, but installation currently requires interactive sudo authorization.
6. Keep `ENABLE_REAL_INTAKE=false` until the synthetic vertical slice is fully verified.

## Safety

No real archive letter has been ingested, renamed, or reprocessed. No production service has been deployed. Private Drive IDs/URLs, Supabase keys/tokens, Auth user IDs, OAuth secrets, SSH keys, and other credentials stay outside Git and public logs.
