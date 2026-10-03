# Runtime Verification — Current State

Observed on 2026-10-02:
- Owner-scoped RLS policies are present on public archive tables.
- Synthetic DB-level owner insert/read passed.
- Wrong-user read returned zero rows.
- Cross-owner synthetic insert was rejected by RLS.
- Verification used simulated database request JWT claims, not a real PostgREST/browser bearer session.
- The synthetic verification row was removed; the letters table now contains zero rows.
- No real archive-letter row exists.
- Repository auth implementation supports both paths: the checked-in custom template uses `token_hash`, and the default Supabase hosted email flow uses a hardened browser-fragment bridge that exchanges a validated owner session for HttpOnly cookies and clears the URL.
- VPS auth/API suite passes 29/29 tests.
- Full VPS synthetic unit suite passes 212/212 tests.
- Guarded Supabase Management Auth-config helper is implemented and its focused suite passes 4/4 tests. It preserves existing redirect allow-list entries and never persists/prints the management token.
- Hosted Supabase uses its default direct-confirmation email behavior. Dashboard inspection confirmed custom SMTP is required before editing template subject/body, so custom template application is now optional rather than a live-login blocker.
- VPS project environment has Supabase runtime/publishable configuration but no Supabase Management API token or CLI login. The new helper is therefore ready but cannot apply hosted Auth settings until an authorized scoped management token is supplied at runtime.
- Dedicated DLR Drive OAuth is configured through secret-manager-injected refresh credentials. The persistent authorized-user runtime file was retired after cutover, and the current grant is write-capable with disposable synthetic upload/stream/delete verification.
- Live refresh-token exchange passed. Originals listing returned one synthetic file, and the DLR GoogleDrivePrivateTransport streamed that synthetic original successfully (24,668 bytes).
- The existing VPS `phone_drive` rclone credential remains unsuitable and is not used by DLR.
- Gemini runtime remains unconfigured; no reusable live key was found in the inspected VPS runtime files.
- DLR runtime now uses a dedicated tailnet-only HTTPS origin, separate from other Oracle VPS applications. Supabase Site URL and redirect allow-list are aligned to that private origin. Exact private routing details remain runtime-only.
- Tailnet HTTPS health check passed from an authorized client. Devices must be on the authorized tailnet to open DLR magic-link callbacks; no public exposure is enabled.
- Supabase email-send throttling is currently preventing issuance of another fresh test link; the API now reports this safely as HTTP 429 instead of 500.
- The dedicated Google OAuth client is successfully in use through secret-manager-injected refresh credentials; legacy persistent authorized-user runtime files were retired after verified cutover.

Pending: real short-lived owner-session HTTP/PostgREST test through the dedicated tailnet-only default hosted Magic Link flow once email throttling permits a fresh link, and Gemini synthetic verification. Write-capable Drive authorization is complete and disposable synthetic upload/stream/delete cleanup passed. Custom SMTP/template application is optional.

## OCR readiness correction

Observed on 2026-10-02:
- The user-local Tesseract and project-virtualenv OCRmyPDF executables are present and Hindi/English language data is available.
- Runtime readiness honors explicit `TESSERACT_CMD` and `OCRMYPDF_CMD` mappings instead of relying only on `PATH`.
- With the private environment loaded, Supabase runtime, auth callback, originals folder, Tesseract, OCRmyPDF, Hindi/English language checks, and synthetic-only safety are ready.
- Drive OAuth is configured with the verified write-capable grant; live refresh/list/stream plus disposable synthetic upload/stream/delete cleanup passed. Gemini remains unconfigured; no live Gemini synthetic operation has been completed yet.


## 2026-10-03 — Dedicated worker identity checkpoint

- Oracle's `dlr-worker-run-with-bitwarden` wrapper successfully injects the configured worker email/password secrets.
- Initial login failed with `invalid_credentials`, confirming the wrapper path was live but the Auth identity was not yet provisioned.
- A dedicated Supabase Auth signup was created using the existing Bitwarden-backed credentials.
- The dedicated worker account is now email-confirmed.
- Live membership was promoted to the minimum processing role and verified as `editor / active`.
- Confirmation email delivery to the school Gmail alias is verified.
- Rechecked live on 2026-10-03: worker is `email_confirmed = true`, `editor / active`; archive letters and processing jobs remain untouched.
- The one-time confirmation token was not forwarded to the Oracle runtime.
- Next: run one-shot worker login/idle verification. Keep the timer disabled until that passes, then continue to the synthetic vertical slice.
