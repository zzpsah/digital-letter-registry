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

- Final authenticated live Supabase insert/read + anonymous/RLS denial test with a real user session is still pending.
- Passwordless auth callback/session exchange is a runtime/deployment integration and is not implemented as raw token-handling code in this public repo.
- Google Drive access-token refresh/credential lifecycle is not yet implemented.
- Live original streaming through the API still needs runtime verification.
- OCRmyPDF/Tesseract Hindi+English packages still need runtime-environment verification.
- No real archive letters have been ingested.
- No rename executor is authorized.

## Next action

Implement the private upload/intake API and durable processing-queue boundary using synthetic fixtures, then run one complete authenticated synthetic vertical slice before any real-letter intake.

## Safety

Never commit real letters, Drive IDs/URLs, Supabase project references/keys, OAuth tokens, credentials, SSH keys, or server details. Do not rename existing Drive files without an approved preview mapping. No production deployment without explicit approval.
