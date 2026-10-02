# Runtime Verification — Current State

Observed on 2026-10-02:
- Owner-scoped RLS policies are present on public archive tables.
- Synthetic DB-level owner insert/read passed.
- Wrong-user read returned zero rows.
- Cross-owner synthetic insert was rejected by RLS.
- Verification used simulated database request JWT claims, not a real PostgREST/browser bearer session.
- One synthetic verification row remains in the letters table.
- No real archive-letter row exists.

Pending: real short-lived owner-session HTTP/PostgREST test, Drive OAuth/original streaming verification, Gemini synthetic verification, hosted magic-link configuration, and synthetic-row cleanup when authorized tooling permits.

## OCR readiness correction

Observed on 2026-10-02:
- The user-local Tesseract and project-virtualenv OCRmyPDF executables are present and Hindi/English language data is available.
- Runtime readiness now honors explicit `TESSERACT_CMD` and `OCRMYPDF_CMD` mappings instead of relying only on `PATH`.
- With the private environment loaded, Supabase runtime, auth callback, originals folder, Tesseract, OCRmyPDF, Hindi/English language checks, and synthetic-only safety are ready.
- Drive OAuth credentials and Gemini key remain unconfigured; no live Drive/Gemini synthetic operation was attempted.
