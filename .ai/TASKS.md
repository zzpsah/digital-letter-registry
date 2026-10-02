# Tasks

## Completed foundation

- [x] Create and onboard the public repository.
- [x] Establish the public-repository privacy boundary.
- [x] Create a separate archive database schema with owner-scoped RLS.
- [x] Select the private Drive archive structure.
- [x] Implement immutable source identity, fingerprints, processing versions, statuses, relationships, and official smart filenames.
- [x] Document and implement the Unicode-safe filename convention.
- [x] Implement Supabase persistence/runtime ports and Google Drive storage contracts.
- [x] Implement synthetic-first intake, duplicate preflight, source provenance, durable processing jobs, and worker foundations.
- [x] Implement native PDF extraction and Hindi/English OCR backend contracts.
- [x] Implement structured context, embeddings, full-text/fuzzy/semantic/hybrid search foundations.
- [x] Implement FastAPI private API, Hindi-first PWA, secure passwordless session handling, and safe original-streaming path.
- [x] Implement preview-first historical import, reviewable relationships, recursive-reprocessing preview, and approval-locked rename execution.
- [x] Add synthetic unit-test coverage and GitHub workflow definitions.
- [x] Verify DB-level synthetic owner insert/read and wrong-user RLS isolation using simulated JWT request claims.

## Runtime verification next

- [ ] Complete authenticated synthetic HTTP/PostgREST owner-session vertical-slice verification using a real short-lived session.
- [ ] Configure and verify refreshable Google Drive OAuth runtime credentials using synthetic data only.
- [ ] Configure and verify Gemini runtime credentials using synthetic data only.
- [ ] Configure Supabase hosted magic-link template and final Site URL/redirects through the dashboard.
- [ ] Verify original streaming and synthetic upload from the deployed/private runtime.
- [ ] Remove the retained synthetic RLS verification row through an authorized cleanup path.
- [ ] Re-read runtime readiness after each external configuration change.

## Explicitly deferred

- [ ] Ingest real archive letters.
- [ ] Execute any historical import.
- [ ] Rename existing Drive files.
- [ ] Activate Telegram, WhatsApp, email, or watched-folder connectors.
- [ ] Deploy to production.

All deferred actions require explicit user authorization and must preserve the repository privacy boundary.
