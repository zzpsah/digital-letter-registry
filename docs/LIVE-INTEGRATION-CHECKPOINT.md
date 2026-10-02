# Live Integration Checkpoint

Last verified: 2026-10-02

## Completed

- Private archive Drive structure is reachable.
- A synthetic PDF was generated and uploaded successfully into the private `originals/` folder and verified private/not shared.
- The synthetic PDF uses the approved archive filename convention and has a computed SHA-256 fingerprint.
- Supabase archive-owner Auth identity exists and the owner email is confirmed.
- DB-level owner access and cross-user RLS isolation are verified. The latest synthetic claim-simulation test confirmed owner insert/read, wrong-user invisibility, and cross-owner insert denial. One synthetic verification row remains; no real archive-letter row exists.
- Server-side token-hash passwordless callback + Secure HttpOnly cookie session/refresh flow are implemented.
- Oracle ARM64 checkout is current, a Python 3.12 project virtualenv is installed, and the synthetic suite passes 188/188.
- Localhost-only FastAPI smoke test passed: health/PWA 200, unauthenticated session/search 401.
- Duplicate `processing_profiles` RLS policy residue was removed; advisor now reports only expected unused-index informational notices.

## Pending runtime verification

1. Configure a real short-lived authenticated archive-owner session in runtime secret storage.
2. Run the guarded synthetic Data API/PostgREST insert/read/duplicate-protection command using that real session; DB-level simulated-JWT verification is already complete.
3. Verify the synthetic HTTP intake → Drive → queue → worker → search/open-original vertical slice.
4. Verify refreshable Google Drive OAuth credentials with live original streaming.
5. Provide runtime-only Google Drive OAuth credentials and Gemini API key.
6. Complete the one-time authenticated owner-session verification; the auth email credential must be consumed manually/user-side rather than transferred between connected tools.
7. Keep `ENABLE_REAL_INTAKE=false` until the synthetic vertical slice is fully verified.

## Safety

No real archive letter has been ingested, renamed, or reprocessed. No production service has been deployed. Private Drive IDs/URLs, Supabase keys/tokens, Auth user IDs, OAuth secrets, SSH keys, and other credentials stay outside Git and public logs.


## Oracle OCR verification

- Tesseract 5.3.4 is installed user-locally on ARM64 without sudo.
- Language data verified: `eng`, `hin`, `osd`.
- OCRmyPDF 16.13.0 is installed in the project virtualenv.
- Direct synthetic PNG OCR passed.
- Synthetic image-only PDF → OCRmyPDF sidecar extraction passed.
- Full Oracle synthetic test suite passed 200/200 at this checkpoint.


## RLS verification note

The latest RLS check used simulated database request JWT claims, not a real bearer session. Therefore it strengthens DB-level evidence but does not close the authenticated HTTP/PostgREST vertical-slice task. A single synthetic verification row is currently retained; cleanup remains pending through an authorized destructive path.
