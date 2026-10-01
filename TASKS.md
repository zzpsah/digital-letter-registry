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
- [ ] Confirm initial AI provider/model and fallback adapter contract.
- [ ] Establish the archive owner authentication identity for RLS-backed writes.

## Phase 1 — Archive foundation

- [x] Define document + processing-version schema.
- [ ] Implement private upload with synthetic fixtures.
- [x] Preserve source identity contract and compute duplicate SHA-256.
- [ ] Store original filename + immutable private storage reference through a repository adapter.
- [ ] Add Supabase repository adapter using authenticated owner identity.

## Phase 2 — Extraction/context

- [ ] Extract existing PDF text before OCR.
- [ ] Add Hindi/English OCR fallback.
- [ ] Create government/education Hindi vocabulary.
- [ ] Implement provider-independent structured AI analysis.
- [x] Generate normalized smart filename.
- [x] Use `undated` and `no-ref` placeholders.
- [x] Preserve Hindi/English/Hinglish Unicode text.

## Phase 3 — Search/UI

- [ ] Full-text/metadata search.
- [ ] Semantic/context search.
- [ ] Ranking combining filename + text + semantic score.
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
