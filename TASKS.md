# Tasks

## Foundation

- [x] Create repository and DevOS scaffold.
- [x] Establish public-repository privacy boundary.
- [x] Define the exact product problem and user workflow.
- [x] Define immutable-original / replaceable-derived-data architecture.
- [x] Define smart filename requirement.
- [x] Define context-first Hindi/English/Hinglish search requirement.
- [x] Define recursive archive reprocessing requirement.
- [x] Confirm private original-file storage target: existing private UMV Google Drive archive structure.
- [x] Create a separate Supabase archive project and core schema.
- [x] Capture the public-safe Supabase schema in repository migrations.
- [x] Define official archive filename convention.
- [x] Add Unicode-safe Hindi/English/Hinglish filename generation.
- [x] Add preview-only rename mapping.
- [x] Confirm initial AI provider/model adapter contract: configurable Gemini first, provider-neutral schema retained.
- [x] Confirm the archive-owner email identity for RLS-backed writes.

## Phase 1 — Archive foundation

- [x] Define document + processing-version schema.
- [x] Implement synthetic/local ingestion preparation without provider writes.
- [x] Implement Drive storage adapter contract with synthetic transport tests.
- [x] Verify a live synthetic upload into the private Drive originals folder.
- [x] Preserve source identity contract and compute duplicate SHA-256.
- [x] Map original filename + immutable private storage reference through the repository layer.
- [x] Add credential-free Supabase repository adapter with injected authenticated transport.
- [x] Implement runtime authenticated Supabase transport and guarded synthetic integration command.
- [ ] Execute authenticated live synthetic insert/read + RLS denial test with runtime session.

## Phase 2 — Extraction/context

- [x] Add provider-neutral native PDF text extraction contract and usability heuristic.
- [x] Add concrete pypdf native-text backend.
- [x] Add Hindi/English OCR fallback contract with versioned processing result.
- [x] Add concrete local OCRmyPDF/Tesseract backend contract.
- [ ] Verify OCRmyPDF + Hindi/English language packs in the eventual runtime environment.
- [x] Create government/education Hindi vocabulary and deterministic context hints.
- [x] Implement provider-independent structured AI analysis.
- [x] Add configurable Gemini structured-output provider as the first adapter.
- [x] Persist extracted text and extraction version into letter_processing.
- [x] Generate normalized smart filename.
- [x] Use `undated` and `no-ref` placeholders.
- [x] Preserve Hindi/English/Hinglish Unicode text.

## Phase 3 — Search/UI

- [x] Full-text/metadata search.
- [x] Semantic/context search foundation with versioned 768-dimension embeddings.
- [x] Ranking combining filename + text + semantic score.
- [x] Add live full-text + trigram search RPC with combined text/fuzzy ranking.
- [ ] Responsive mobile web/PWA.
- [ ] Filters: date/year, authority, category, file type, validity/status.
- [ ] Open/download original from every result.

## Phase 4 — Intelligence lifecycle

- [ ] Related/superseded/extension/correction links.
- [ ] Processing-version registry.
- [ ] Preview + recursive reprocessing jobs.
- [ ] Safe rename executor only after explicit approval.
- [ ] Historical bulk import.
- [ ] Additional intake channels: Telegram, WhatsApp, email, watched folder.

## Current safety boundary

- Drive archive folders remain private and empty.
- Rename behavior is preview-only.
- No live document ingestion has occurred.
- No production deployment is claimed.
- No Drive IDs/URLs, Supabase credentials, SSH keys, or server details belong in public Git.
