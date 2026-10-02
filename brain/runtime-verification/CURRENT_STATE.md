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
- VPS auth/API suite passes 28/28 tests.
- Full VPS synthetic unit suite passes 208/208 tests.
- Guarded Supabase Management Auth-config helper is implemented and its focused suite passes 4/4 tests. It preserves existing redirect allow-list entries and never persists/prints the management token.
- Hosted Supabase uses its default direct-confirmation email behavior. Dashboard inspection confirmed custom SMTP is required before editing template subject/body, so custom template application is now optional rather than a live-login blocker.
- VPS project environment has Supabase runtime/publishable configuration but no Supabase Management API token or CLI login. The new helper is therefore ready but cannot apply hosted Auth settings until an authorized scoped management token is supplied at runtime.
- Connected Drive access sees the private archive and synthetic original, but the existing VPS `phone_drive` rclone credential cannot enumerate the archive contents even with direct folder IDs. It is not suitable for registry runtime access.
- Gemini runtime remains unconfigured; no reusable live key was found in the inspected VPS runtime files.
- The prior Drive OAuth checkpoint confirms a dedicated Google OAuth client exists in a private vault, but Bitwarden CLI is unavailable both locally and on the VPS, so the client secret cannot be programmatically retrieved through the current tool path.

Pending: real short-lived owner-session HTTP/PostgREST test through the default hosted Magic Link flow, correct Drive OAuth/original streaming verification, Gemini synthetic verification, and synthetic-row cleanup when authorized tooling permits. Custom SMTP/template application is optional.

## OCR readiness correction

Observed on 2026-10-02:
- The user-local Tesseract and project-virtualenv OCRmyPDF executables are present and Hindi/English language data is available.
- Runtime readiness honors explicit `TESSERACT_CMD` and `OCRMYPDF_CMD` mappings instead of relying only on `PATH`.
- With the private environment loaded, Supabase runtime, auth callback, originals folder, Tesseract, OCRmyPDF, Hindi/English language checks, and synthetic-only safety are ready.
- Drive OAuth credentials and Gemini key remain unconfigured in the project runtime; no live Drive/Gemini synthetic operation has been completed yet.
