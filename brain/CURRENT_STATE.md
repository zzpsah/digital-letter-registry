# Project Brain — Current State

Last verified: 2026-10-02

## Working

- DevOS lifecycle is MANAGED.
- Public-safe repository scaffold and domain package exist.
- Private UMV Drive is selected for archive originals.
- Archive folder structure exists and is empty: `originals/`, `quarantine/`, `exports/`.
- Separate Supabase archive database exists with four core RLS-protected tables.
- Security advisor is clean.
- Unicode-safe official naming and preview-only rename mapping are implemented.
- Persistence ports, Supabase row mapping, injected-transport repository adapter, synthetic ingestion preparation, storage ports, and a Drive adapter contract are implemented.
- GitHub CI is configured for synthetic unit tests.

## Current gaps

- Supabase archive-owner Auth identity exists and its email is confirmed.
- No live Google Drive transport or authenticated Supabase transport is wired yet.
- No OCR, AI context extraction, embeddings pipeline, search UI, or live ingestion exists.
- No rename executor is authorized.

## Next action

Create/establish the archive owner authentication identity, then wire the private Drive upload adapter and authenticated Supabase transport with synthetic fixtures only.

## Safety

Do not commit real letters, Drive IDs/URLs, Supabase keys, credentials, SSH keys, or server details to this public repository. Existing Drive files must not be renamed without an approved preview mapping.


## 2026-10-02 — Live integration checkpoint

A synthetic PDF upload to the private Drive `originals/` folder is verified. Supabase archive-owner email confirmation is complete. Runtime authenticated PostgREST transport and a guarded synthetic integration command are now implemented. The remaining live step is to execute the command with a short-lived authenticated user session and verify RLS denial for an unauthenticated caller.


## Phase 2 progress

Native PDF text/OCR provider contracts are implemented with Hindi-English fallback semantics. Government/education vocabulary and deterministic context hints are implemented before AI analysis. A concrete OCR backend and structured AI provider remain pending.


## Concrete extraction backends

Native PDF text now has a pypdf implementation. OCR fallback now has an OCRmyPDF/Tesseract implementation using Hindi+English sidecar text. Extraction text/version persistence is wired into letter_processing. Runtime verification of OCR binaries/language packs remains pending.


## Structured context provider

The provider-neutral context schema and extraction→context→persistence pipeline are implemented. Gemini is the first runtime-configurable structured-output adapter; provider/model changes do not require schema changes and can be handled by reprocessing versions.


## Search foundation

The separate archive database now has live full-text + trigram search via `search_letters`, plus covering indexes for reported foreign-key gaps. Search remains RLS-protected. Semantic embeddings/ranking are the next search layer.


## Semantic search

The live archive database now has 768-dimensional pgvector storage, HNSW cosine indexing, semantic chunk search, and application-level hybrid ranking that merges text/fuzzy relevance with semantic similarity. Embeddings are version-filtered to support safe future reprocessing.


## Private mobile API/PWA

A FastAPI + Hindi-first mobile PWA shell now sits on top of the RLS-protected search layer. Filtered search and safe letter detail are implemented without leaking Drive object IDs. Passwordless login-request flow exists for pre-authorized users, while callback/session exchange and the private original-file resolver remain deployment/runtime tasks. No production deployment has occurred.
