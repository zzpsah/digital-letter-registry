# Current State

- Canonical repository: `zzpsah/digital-letter-registry`.
- Formal archive name: **Official Letter Intelligence Archive**.
- Public-repository privacy boundary is established: code/docs/synthetic fixtures/schema only.
- Existing private UMV Google Drive is the selected original-file storage.
- Private archive structure exists with `originals/`, `quarantine/`, and `exports/`; a synthetic integration PDF has been used in `originals/`, but no real archive letters have been ingested.
- A separate Supabase archive project exists, isolated from the existing UMV database.
- Core tables exist: `letters`, `letter_processing`, `letter_relationships`, and `letter_chunks`.
- RLS is enabled on all public archive tables; security advisor is clean.
- Supabase archive-owner Auth identity exists and is confirmed; no real archive-letter rows have been ingested.
- The public-safe core schema is captured under `supabase/migrations/`.
- Domain code includes immutable source identity, SHA-256 fingerprints, processing versions, statuses/relationships, and smart filenames.
- Official filename pattern is `short-title__issuer__date__reference-number.ext`.
- Naming now preserves Hindi/English/Hinglish Unicode and uses `undated` / `no-ref` placeholders.
- Rename functionality is preview-only; no Drive rename executor is authorized yet.
- Persistence ports, Supabase row mapping, an injected-transport Supabase repository adapter, synthetic/local ingestion preparation, storage ports, and an injected Google Drive storage adapter are implemented.
- GitHub CI runs the synthetic unit-test suite on pushes/PRs.
- No real archive-letter ingestion or production deployment has occurred. OCR/AI/search pipelines are implemented but not yet live-verified against real letters.

## Next step

Establish an authenticated archive owner for RLS-backed writes, then wire the live Google Drive transport and real authenticated Supabase transport using synthetic fixtures before any live-letter ingestion.


## 2026-10-02 — Live synthetic integration checkpoint

- Live private Drive upload was verified with a synthetic PDF in `originals/`.
- The synthetic PDF uses the approved smart-filename pattern and remains private.
- A Supabase archive-owner Auth identity was created through passwordless email signup.
- Supabase archive-owner email is confirmed.
- Runtime authenticated Supabase PostgREST transport and a guarded synthetic integration command are implemented; the final live insert/RLS-denial execution remains pending.
- No real archive letter was ingested or renamed.


## Runtime Supabase integration

- `src/letter_registry/supabase_runtime.py` provides environment-only authenticated PostgREST transport.
- `scripts/run_synthetic_supabase_integration.py` refuses non-synthetic filenames and performs no Drive upload.
- No project URL, publishable key, access token, owner UUID, or Drive object ID is stored in Git.


## Phase 2 extraction/context foundation

- Provider-neutral native PDF extraction contract is implemented.
- Native-text usability heuristic prefers embedded text and requests OCR only when needed.
- Hindi + English OCR fallback contract is implemented and versioned, but no concrete OCR engine is wired yet.
- Hindi/English/Hinglish government and education vocabulary is implemented.
- Deterministic pre-AI context hints detect concepts such as registration, exam form, deadline/extension, UDISE, PEN, scholarship, correction, verification, training, and government letter structure markers.


## Concrete extraction backends

- `PypdfTextBackend` provides native embedded PDF text extraction.
- `OcrmypdfTesseractBackend` provides local Hindi+English OCR via OCRmyPDF/Tesseract and sidecar text.
- OCR binaries/language packs are runtime dependencies, not bundled into the repo.
- Extraction results now map into `letter_processing.extracted_text` and `ocr_version`.


## Structured AI analysis

- Provider-neutral structured document context schema is implemented.
- Extracted text flows through deterministic Hindi/education hints before provider analysis.
- Gemini is the first configurable adapter, using structured JSON output.
- AI provider/model/key are runtime configuration only; database schema remains vendor-neutral.
- Structured context persists full JSON + concepts + context version, while searchable metadata is projected into `letters`.


## Search foundation

- Live Supabase migration adds full-text search over extracted text and fuzzy trigram matching for smart filename/title/authority.
- `search_letters` RPC is deployed with security-invoker semantics so RLS remains authoritative.
- Search ranking currently combines text rank (75%) and fuzzy rank (25%).
- Foreign-key covering indexes reported by the performance advisor were added.
- Performance advisor now reports only unused-index informational notices, expected for the nearly empty archive.
- Supabase security advisor currently warns that leaked-password protection is disabled at the Auth project setting; no RLS/schema warning was reported.


## Semantic + hybrid search

- Gemini embedding adapter uses runtime-configurable `gemini-embedding-2` with 768 dimensions.
- Extracted text is deterministically chunked and each chunk stores its own embedding version.
- Live Supabase `letter_chunks.embedding` is constrained to vector(768).
- HNSW cosine index and `search_letter_chunks_semantic` RPC are deployed.
- Hybrid search combines text/fuzzy rank with semantic similarity.
- Embedding spaces remain explicitly versioned so future provider/model changes require controlled re-embedding rather than mixed-vector comparison.


## Private mobile API/PWA

- FastAPI private API foundation is implemented.
- Hindi-first mobile PWA shell is implemented with query and filters.
- Filtered text/fuzzy search RPC is live in the archive database.
- Search API uses the caller's Supabase bearer session, preserving RLS as the data boundary.
- Search/detail responses never expose private storage object identifiers.
- Safe authenticated letter-detail endpoint is implemented.
- Passwordless email link request is implemented with `create_user=false`; callback/session exchange remains a deployment-time integration.
- PWA service worker caches only public app-shell assets and never caches `/api/` data.
- Server-side original streaming is implemented: the API resolves private storage references under RLS and can stream Google Drive bytes without exposing Drive object IDs. Live runtime credential verification remains pending.
- Application CI is green after fixing native-PDF, blank-embedding, and Drive-reader source-generation regressions. DevOS context-sync is also green using the vendored local helper.

## Last automated change
- Commit: 9f9131bcb5e5957fb138a601c8e2668b7c3d989d
- Change: feat: add reviewable relationship suggestion repository
- Date: 2026-10-02
- Durable context synchronization: completed
