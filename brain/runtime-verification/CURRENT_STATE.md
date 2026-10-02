# Runtime Verification — Current State

Observed on 2026-10-02:
- Owner-scoped RLS policies are present on public archive tables.
- Synthetic DB-level owner insert/read passed.
- Wrong-user read returned zero rows.
- Cross-owner synthetic insert was rejected by RLS.
- Verification used simulated database request JWT claims, not a real PostgREST/browser bearer session.
- One synthetic verification row remains in the letters table.
- No real archive-letter row exists.
- Repository auth/template implementation is ready: the checked-in magic-link template points to the server callback with `token_hash`.
- VPS focused auth/session/API suite passes 35/35 tests.
- Full VPS synthetic unit suite passes 205/205 tests.
- Guarded Supabase Management Auth-config helper is implemented and its focused suite passes 4/4 tests. It preserves existing redirect allow-list entries and never persists/prints the management token.
- Hosted Supabase still uses its default direct-confirmation email behavior, so the checked-in template/Site URL configuration has not yet been applied to the live Auth project.
- VPS project environment has Supabase runtime/publishable configuration but no Supabase Management API token or CLI login. The new helper is therefore ready but cannot apply hosted Auth settings until an authorized scoped management token is supplied at runtime.
- Connected Drive access sees the private archive and synthetic original, but the existing VPS `phone_drive` rclone credential cannot enumerate the archive contents even with direct folder IDs. It is not suitable for registry runtime access.
- Gemini runtime remains unconfigured; no reusable live key was found in the inspected VPS runtime files.
- The prior Drive OAuth checkpoint confirms a dedicated Google OAuth client exists in a private vault, but Bitwarden CLI is unavailable both locally and on the VPS, so the client secret cannot be programmatically retrieved through the current tool path.

Pending: apply hosted magic-link/Site URL configuration, real short-lived owner-session HTTP/PostgREST test, correct Drive OAuth/original streaming verification, Gemini synthetic verification, and synthetic-row cleanup when authorized tooling permits.

## OCR readiness correction

Observed on 2026-10-02:
- The user-local Tesseract and project-virtualenv OCRmyPDF executables are present and Hindi/English language data is available.
- Runtime readiness honors explicit `TESSERACT_CMD` and `OCRMYPDF_CMD` mappings instead of relying only on `PATH`.
- With the private environment loaded, Supabase runtime, auth callback, originals folder, Tesseract, OCRmyPDF, Hindi/English language checks, and synthetic-only safety are ready.
- Drive OAuth credentials and Gemini key remain unconfigured in the project runtime; no live Drive/Gemini synthetic operation has been completed yet.
