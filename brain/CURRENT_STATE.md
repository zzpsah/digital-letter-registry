# Project Brain — Current State

Last verified: 2026-10-02

## Working

- DevOS lifecycle is MANAGED and its local context-sync workflow is green.
- Public-safe repository scaffold and domain package exist.
- Private UMV Drive is selected for archive originals.
- Archive structure exists: `originals/`, `quarantine/`, `exports/`; only synthetic integration data has been used.
- Separate Supabase archive database exists with four core RLS-protected tables.
- Archive-owner Supabase Auth identity exists and is confirmed.
- Unicode-safe official naming and preview-only rename mapping are implemented.
- Persistence, Supabase runtime, private storage contracts, and guarded synthetic ingestion are implemented.
- Native PDF extraction, Hindi/English OCR fallback, structured AI context, embeddings, full-text/fuzzy/semantic/hybrid search are implemented.
- Live Supabase search migrations and pgvector HNSW index are applied.
- FastAPI + Hindi-first mobile PWA, filtered search, safe letter detail, and passwordless login-request endpoint are implemented.
- Original-file access stays server-side; private Drive object IDs are not returned to the browser.
- Google Drive server-side reader is implemented using runtime-only OAuth access token.
- Application tests and DevOS context-sync are green.

## Current gaps

- Live DB-level owner RLS read/insert and cross-user isolation are verified with rollback-only synthetic transactions. A final HTTP/PostgREST test using a short-lived real user bearer session is still pending.
- The current passwordless implicit-flow callback is implemented in the PWA: access token is kept in sessionStorage and URL fragments are scrubbed. Refresh/session renewal is intentionally not implemented yet.
- Google Drive access-token refresh/credential lifecycle is not yet implemented.
- Live original streaming through the API still needs runtime verification.
- OCRmyPDF/Tesseract Hindi+English packages still need runtime-environment verification.
- No real archive letters have been ingested.
- No rename executor is authorized.

## Next action

Implement the private upload/intake API and durable processing-queue boundary using synthetic fixtures, then run one complete authenticated synthetic vertical slice before any real-letter intake.

## Safety

Never commit real letters, Drive IDs/URLs, Supabase project references/keys, OAuth tokens, credentials, SSH keys, or server details. Do not rename existing Drive files without an approved preview mapping. No production deployment without explicit approval.


## Intake + processing worker

Synthetic-first private intake is implemented end-to-end in code: authenticated owner lookup, duplicate SHA preflight, immutable Drive upload, source/processing rows, durable queued job, atomic RLS-aware claim, private original download, extraction/OCR, structured context, smart filename metadata, embeddings, and durable completed/failed job transition. Real intake remains disabled by default and no production deployment has occurred.

PDF and image paths are both represented: PDF uses native text then OCRmyPDF/Tesseract fallback; JPG/JPEG/PNG uses direct Tesseract Hindi+English OCR. The remaining milestone is live synthetic runtime verification with short-lived user/Drive credentials and locally available OCR binaries.


## 2026-10-02 — Schema sync and auth shell

- Applied the pending relationship-review migration to the empty archive database.
- Live schema now includes processing jobs, search/semantic RPCs, summary/reference metadata, and reviewable relationship lifecycle.
- Verified RLS owner access and cross-user isolation without retaining test rows.
- PWA now captures implicit magic-link sessions safely on the client and can open streamed original bytes.
- No real letter ingestion, rename execution, or production deployment occurred.
