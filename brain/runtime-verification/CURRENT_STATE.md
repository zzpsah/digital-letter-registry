# Runtime Verification — Current State

Observed on 2026-10-02:
- Owner-scoped RLS policies are present on public archive tables.
- Synthetic DB-level owner insert/read passed.
- Wrong-user read returned zero rows.
- Cross-owner synthetic insert was rejected by RLS.
- Verification used simulated database request JWT claims, not a real PostgREST/browser bearer session.
- One synthetic verification row remains in the letters table.
- No real archive-letter row exists.
- Repository auth/template implementation is ready: the checked-in magic-link template points to the server callback with `token_hash`, and the auth/session/API focused suite passes 35/35 tests on the VPS.
- Full VPS synthetic unit suite passes 201/201 tests.
- Hosted Supabase still uses its default direct-confirmation email behavior, so the checked-in template/Site URL configuration has not yet been applied to the live Auth project.
- VPS project environment has Supabase runtime/publishable configuration but no Supabase Management API token or CLI login, so hosted Auth settings cannot currently be changed from the VPS without an additional authorized management credential or dashboard/browser action.

Pending: apply hosted magic-link/Site URL configuration, real short-lived owner-session HTTP/PostgREST test, Drive OAuth/original streaming verification, Gemini synthetic verification, and synthetic-row cleanup when authorized tooling permits.

## OCR readiness correction

Observed on 2026-10-02:
- The user-local Tesseract and project-virtualenv OCRmyPDF executables are present and Hindi/English language data is available.
- Runtime readiness honors explicit `TESSERACT_CMD` and `OCRMYPDF_CMD` mappings instead of relying only on `PATH`.
- With the private environment loaded, Supabase runtime, auth callback, originals folder, Tesseract, OCRmyPDF, Hindi/English language checks, and synthetic-only safety are ready.
- Drive OAuth credentials and Gemini key remain unconfigured in the project runtime; no live Drive/Gemini synthetic operation has been completed yet.
