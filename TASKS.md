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
- [x] Verify DB-level owner insert/read isolation and wrong-user RLS denial using synthetic JWT-claim simulation.
- [ ] Execute authenticated live synthetic insert/read + RLS denial test with a real short-lived runtime bearer/session.
- [x] Remove the retained synthetic RLS verification row through a controlled exact-match cleanup; verified `letters` contains zero rows afterward.

## Phase 2 — Extraction/context

- [x] Add provider-neutral native PDF text extraction contract and usability heuristic.
- [x] Add concrete pypdf native-text backend.
- [x] Add Hindi/English OCR fallback contract with versioned processing result.
- [x] Add concrete OCRmyPDF PDF fallback + direct Tesseract image OCR backends.
- [x] Verify OCRmyPDF + Tesseract Hindi/English language packs in Oracle runtime (user-local ARM64 install; synthetic PNG and image-only PDF OCR passed).
- [x] Create government/education Hindi vocabulary and deterministic context hints.
- [x] Implement provider-independent structured AI analysis.
- [x] Add configurable Gemini structured-output provider as the first adapter.
- [x] Persist extracted text and extraction version into letter_processing.
- [x] Generate normalized smart filename.
- [x] Use `undated` and `no-ref` placeholders.
- [x] Preserve Hindi/English/Hinglish Unicode text.
- [x] Extract explicit issue date + reference number into structured context.
- [x] Smart filename is derived automatically when title + authority are confidently available.
- [x] Promote summary/reference number into searchable metadata.

## Phase 3 — Search/UI

- [x] Full-text/metadata search.
- [x] Semantic/context search foundation with versioned 768-dimension embeddings.
- [x] Ranking combining filename + text + semantic score.
- [x] Add live full-text + trigram search RPC with combined text/fuzzy ranking.
- [x] Responsive Hindi-first mobile web/PWA shell.
- [x] Filters: year, authority, category, file type, validity/status.
- [x] Server-side private original streaming contract + Google Drive reader implemented.
- [ ] Verify live runtime original streaming with short-lived/refreshable Drive credentials.

- [x] Passwordless email login request endpoint for existing authorized users.
- [x] Implement server-side token-hash auth callback + HttpOnly cookie session/refresh without browser token storage.
- [x] Support Supabase default hosted Magic Link fragment callback: same-origin bridge validates owner session server-side, sets HttpOnly cookies, clears URL tokens, and requires no custom SMTP.
- [x] Authenticated safe letter-detail endpoint without storage IDs.

## Phase 3.5 — Intake/runtime

- [x] Private upload/intake API with synthetic-first safety guard.
- [x] Durable Supabase processing-job queue with atomic claim/complete/fail RPCs.
- [x] Upload → duplicate preflight → private archive → enqueue derived processing.
- [ ] Live authenticated synthetic API vertical slice.
- [x] Add guarded Supabase Management API helper to check/apply the checked-in Magic Link template, Site URL, and redirect allow-list without printing credentials.
- [ ] Optional later: enable custom SMTP and apply the checked-in token-hash Magic Link template/Site URL if desired; this is no longer required for the default hosted login flow.
- [x] Runtime auth callback/session exchange implemented with HttpOnly cookies and refresh rotation.
- [x] Add same-origin CSRF protection for cookie-authenticated mutations.
- [x] Authenticated owner upload panel with explicit synthetic/test mode status.
- [x] Secret-safe runtime readiness CLI/API/UI checks.
- [x] Refreshable Google Drive OAuth credential strategy with in-memory access-token caching.

## Phase 4 — Intelligence lifecycle

- [x] Reviewable related/superseded/extension/correction relationship lifecycle.
- [x] Owner-scoped processing-version registry.
- [x] Conservative explicit-reference relationship suggestion rules.
- [x] Confirm/reject review API with status recalculation only after confirmation.
- [x] Preview + explicit-confirmation recursive reprocessing jobs.
- [x] One-job processing worker orchestration with durable success/failure state.
- [x] Approval-locked rename executor + private Drive rename transport implemented; no mapping approved/executed yet.
- [x] Preview-first historical bulk import/adoption pipeline for local files and existing private Drive objects; no real import executed.
- [x] Provider-neutral Telegram/WhatsApp/email/watched-folder intake normalization + provenance persistence.
- [ ] Activate live Telegram/WhatsApp/email/watched-folder connectors with runtime credentials and synthetic verification.

## Current safety boundary

- Drive archive folders remain private; only synthetic integration data has been used.
- Supabase currently contains one synthetic RLS-verification row and no real archive-letter rows.
- Rename behavior is preview/approval locked; no real rename has been approved or executed.
- No real archive-letter ingestion has occurred.
- No production deployment is claimed.
- No Drive IDs/URLs, Supabase credentials, SSH keys, tokens, or server details belong in public Git.
