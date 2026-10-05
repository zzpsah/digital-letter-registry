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
- Application tests and DevOS context-sync are green. Oracle ARM64 runtime has a Python 3.12 virtual environment and passes the full synthetic suite (188/188). A localhost-only FastAPI smoke test verified health/PWA 200 responses and unauthenticated session/search 401 boundaries.

## Current gaps

- DB-level owner RLS insert/read and cross-user isolation are verified with synthetic request-JWT claim simulation. A final HTTP/PostgREST test using a short-lived real user bearer session is still pending. One synthetic verification row currently remains in `letters`; no real archive-letter row exists.
- Passwordless auth now uses a server-side token-hash callback with Secure HttpOnly access/refresh cookies and refresh rotation. The PWA does not persist auth tokens in browser storage.
- Google Drive OAuth refresh-token lifecycle is implemented with in-memory access-token caching; private-runtime secret-manager-backed refresh/list/stream and disposable synthetic upload/stream/delete verification passed.
- Live original streaming through the API still needs runtime verification.
- Oracle OCR runtime is verified using a user-local ARM64 Tesseract 5.3.4 install with `eng`, `hin`, and `osd`, plus OCRmyPDF 16.13.0 in the project virtualenv. Synthetic PNG and image-only PDF OCR smoke tests both passed.
- No real archive letters have been ingested.
- Approval-locked rename execution code exists, but no rename plan has been approved or executed.

## Next action

Complete the authenticated synthetic HTTP/PostgREST vertical slice with a short-lived owner session, refreshable Drive OAuth credentials, and synthetic upload/read verification. OCR runtime is already verified through the user-local toolchain; no sudo package installation is required for that verified path.

## Safety

Never commit real letters, Drive IDs/URLs, Supabase project references/keys, OAuth tokens, credentials, SSH keys, or server details. Do not rename existing Drive files without an approved preview mapping. No production deployment without explicit approval.


## Intake + processing worker

Synthetic-first private intake is implemented end-to-end in code: authenticated owner lookup, duplicate SHA preflight, immutable Drive upload, source/processing rows, durable queued job, atomic RLS-aware claim, private original download, extraction/OCR, structured context, smart filename metadata, embeddings, and durable completed/failed job transition. Real intake remains disabled by default and no production deployment has occurred.

PDF and image paths are both represented: PDF uses native text then OCRmyPDF/Tesseract fallback; JPG/JPEG/PNG uses direct Tesseract Hindi+English OCR. The remaining milestone is live synthetic runtime verification with short-lived user/Drive credentials and locally available OCR binaries.


## 2026-10-02 — Schema sync and auth shell

- Applied the pending relationship-review migration to the empty archive database.
- Live schema now includes processing jobs, search/semantic RPCs, summary/reference metadata, and reviewable relationship lifecycle.
- Earlier rollback-only RLS checks were followed by a new synthetic DB-level claim-simulation check: owner insert/read passed, wrong-user read returned zero rows, and cross-owner insert was denied. One synthetic verification row is currently retained; no real archive row exists.
- PWA uses the server-side token-hash magic-link callback with Secure HttpOnly session cookies and can open streamed original bytes.
- No real letter ingestion, rename execution, or production deployment occurred.


## Relationship intelligence

The worker now generates only conservative, reviewable relationship suggestions when explicit extension/correction/superseding language references a known prior letter number. Suggestions never change status automatically. Authenticated review endpoints confirm/reject them, and only confirmed supersedes links affect the older letter's status through an RLS-aware recalculation function.


## Relationship + recursive reprocessing

Relationship inference is deliberately conservative and reviewable: explicit relationship wording plus a referenced prior letter is required before a suggestion is created. Suggestions do not change status until confirmed by the authenticated owner.

A live processing-version registry and reprocessing preview/enqueue flow now exist. Version changes can be previewed per letter/stage first; recursive reprocessing is queued only after explicit confirmation and is idempotent for the same target-version profile.


## Rename execution

A dormant Google Drive rename path now exists behind an approval-locked executor. It cannot run from an arbitrary proposed name: the exact reviewed mapping must match its deterministic digest, explicit confirmation is required, and the current stored filename is revalidated before any mutation. No rename mapping has been approved or executed.


## Historical import

Historical import is implemented as preview-first, approval-locked adoption. Local candidate files can be hashed in a non-mutating preview. Existing private Drive files can be listed read-only, classified as eligible/unsupported/already archived/real-document-blocked, and only after explicit confirmation are their bytes read for SHA-256 duplicate verification, source identity persisted against the existing Drive object, and a historical processing job queued. Real historical documents remain blocked by default and no real historical import has been executed.


## Intake channels

Provider-neutral adapters now normalize Telegram, WhatsApp, email, watched-folder, and web-style attachments into the canonical IntakeService. Owner-scoped source provenance is persisted in the live `letter_sources` schema without storing attachment bytes in provenance records. No live external connector has been activated yet; runtime connector wiring and synthetic end-to-end verification remain pending.


## Oracle runtime verification

- Oracle repository was fast-forwarded cleanly to the current main branch; no local source changes were present.
- A project-local Python 3.12 virtual environment is installed and the full synthetic test suite passes: 188/188.
- A temporary localhost-only FastAPI smoke run verified `/api/v1/health` = 200, Hindi PWA shell = 200, unauthenticated session = 401, and unauthenticated search = 401; the temporary process was stopped afterward.
- ARM64 Ubuntu repositories provide Tesseract, Hindi/English language packs, and OCRmyPDF, but package installation is still pending because the `prashant` account requires interactive sudo authorization.
- Supabase performance advisor no longer reports duplicate processing-profile RLS policies after cleanup. Remaining unused-index notices are informational while the archive is nearly empty.


## Runtime readiness + secure browser auth

The browser auth flow is now server-side and token-safe: Supabase token-hash magic links are verified at `/auth/confirm`, access/refresh sessions are stored in HttpOnly SameSite=Lax cookies, access expiry is refreshed server-side, and browser JavaScript never reads auth tokens. Cookie-authenticated mutations are protected by same-origin checks; explicit Bearer API clients remain supported.

The owner PWA now includes authenticated synthetic-first upload and safe runtime readiness panels. Readiness checks report only boolean/status information for Supabase, auth callback, Drive OAuth/folder, Gemini, OCRmyPDF, Tesseract Hindi+English, and the synthetic-only safety flag. No secret values or private folder IDs are returned.

Refresh-token Google Drive credentials now enable both upload and original streaming; a direct short-lived access token remains an optional fallback.

Application CI is green with these changes included. The remaining blocker before a live browser synthetic vertical slice is hosted Supabase Auth configuration: copy `supabase/templates/magic-link.html` into the project Magic Link template and configure the Site URL/redirect for the app's `/auth/confirm` endpoint. The connected Supabase tool cannot mutate hosted Auth templates/settings, so this external dashboard step has not been claimed as complete.

Real intake remains disabled by default. No real archive letter has been ingested or renamed and no production deployment has occurred.


## 2026-10-02 — Runtime readiness follow-up

- Oracle local runtime now passes the full synthetic suite (200/200 at this checkpoint).
- Supabase runtime URL/publishable key/owner mapping is configured locally; anonymous Data API read returns an empty RLS-scoped result and anonymous insert is rejected with 401.
- The private Drive archive folder and its `originals/`, `quarantine/`, and `exports/` children were verified through the connected Drive account; the expected private synthetic integration PDF is present in `originals/`.
- Oracle local `.env` contains only runtime-only mappings and remains Git-ignored with restrictive permissions.
- Auth callback is configured for localhost `/auth/confirm`.
- OCR no longer requires sudo: Tesseract 5.3.4 and Hindi/English language data are installed under the user account; OCRmyPDF 16.13.0 is installed in the project virtualenv.
- Current readiness blockers are only Google Drive runtime OAuth credentials and a Gemini API key. The authenticated owner-session test also still requires a user-approved/manual one-time login boundary because transferring a one-time email credential directly between connected tools is not permitted.

## 2026-10-02 - Repository context reconciliation

- Source and test configuration confirm that the project is no longer planning-only: the private API/PWA, guarded synthetic intake, worker, storage/persistence adapters, OCR contracts, structured analysis, search, historical-import preview, and approval-locked rename path are implemented.
- Project-level AI scope and task records were reconciled to the implemented source.
- This reconciliation does not verify external runtime credentials, hosted Supabase Auth settings, live provider behavior, real-letter ingestion, Drive rename execution, or production deployment.
- The next safe runtime work remains synthetic-only: refreshable Drive OAuth verification, Gemini credential verification, and an authenticated owner-session HTTP/PostgREST vertical slice.


## 2026-10-02 — DB-level RLS verification follow-up

- Re-read project RULES, AGENTS, .ai state, root tasks/docs, and brain context before continuing.
- Inspected the public archive RLS policies and confirmed owner-scoped authenticated access.
- Synthetic owner-context insert/read passed.
- Synthetic wrong-user read returned zero visible rows.
- Synthetic cross-owner insert was rejected by RLS.
- Test method used simulated database request JWT claims, so the real short-lived authenticated HTTP/PostgREST vertical slice remains pending.
- Exactly one synthetic RLS verification row remains in `letters`; no real archive-letter row exists.
- Destructive cleanup was not claimed because the connected cleanup action was blocked.
- No secrets, private IDs, real letters, deployment, live import, or real rename were added.

## 2026-10-05 — Admin controls and mobile web polish

- Admin UI now exposes current delivery recipients and allowed WhatsApp users instead of providing add-only controls.
- Admin can add/remove managed recipients/users and control the broader account/category workflow from the web console.
- Mobile web CSS was refined for compact sticky navigation, responsive search/actions, one-column filters/forms, readable document cards, horizontal admin tabs and touch-friendly controls.
- The full automated suite passed after the mobile change (308 tests).
