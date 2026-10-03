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
- [x] Verify live runtime original streaming with refreshable Drive credentials (authorized-user file, synthetic original only).

- [x] Passwordless email login request endpoint for existing authorized users.
- [x] Implement server-side token-hash auth callback + HttpOnly cookie session/refresh without browser token storage.
- [x] Support Supabase default hosted Magic Link fragment callback: same-origin bridge validates owner session server-side, sets HttpOnly cookies, clears URL tokens, and requires no custom SMTP.
- [x] Authenticated safe letter-detail endpoint without storage IDs.

## Phase 3.5 — Intake/runtime

- [x] Private upload/intake API with synthetic-first safety guard.
- [x] Durable Supabase processing-job queue with atomic claim/complete/fail RPCs.
- [x] Upload → duplicate preflight → private archive → enqueue derived processing.
- [x] Isolate DLR runtime on a dedicated tailnet-only HTTPS origin and align Supabase Site URL/redirect allow-list without exposing private routing details in Git.
- [x] Surface Supabase magic-link email throttling as HTTP 429 instead of 500.
- [ ] Live authenticated synthetic API vertical slice (routing verified; awaiting a fresh email after Supabase send-rate throttling clears).
- [x] Add guarded Supabase Management API helper to check/apply the checked-in Magic Link template, Site URL, and redirect allow-list without printing credentials.
- [ ] Optional later: enable custom SMTP and apply the checked-in token-hash Magic Link template/Site URL if desired; this is no longer required for the default hosted login flow.
- [x] Runtime auth callback/session exchange implemented with HttpOnly cookies and refresh rotation.
- [x] Add same-origin CSRF protection for cookie-authenticated mutations.
- [x] Authenticated owner upload panel with explicit synthetic/test mode status.
- [x] Secret-safe runtime readiness CLI/API/UI checks.
- [x] Refreshable Google Drive OAuth credential strategy with in-memory access-token caching.
- [x] Add authorized-user file fallback and secret-manager-injected refresh credential support.
- [x] Verify live secret-manager-only refresh/list/stream with synthetic data; retire the Oracle runtime file credential after cutover.
- [x] Verify runtime synthetic upload/write after the approved write-capable Drive re-consent; disposable upload/stream/delete cleanup passed.

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
- Supabase synthetic RLS-verification row was removed; `letters` currently contains zero rows and no real archive-letter rows.
- Rename behavior is preview/approval locked; no real rename has been approved or executed.
- No real archive-letter ingestion has occurred.
- Public Vercel control-plane deployment is live; real archive-letter intake remains disabled.
- No Drive IDs/URLs, Supabase credentials, SSH keys, tokens, or server details belong in public Git.


## Google Sign-In / persistent session

- [x] Add provider-aware Google Sign-In application flow.
- [x] Keep Magic Link as fallback/recovery.
- [x] Add persistent 30-day refresh-session cookie with bounded configuration.
- [x] Preserve archive-owner user-id validation before setting DLR cookies.
- [x] Pass full synthetic suite: 220/220.
- [ ] Create/configure separate Google Web OAuth client.
- [ ] Enable Google provider in Supabase Auth.
- [ ] Verify same-email Google identity links to the existing archive-owner user id.
- [ ] Complete the authenticated synthetic owner/RLS vertical slice.


## Multi-user DLR accounts

- [x] Add archive membership model with `admin`, `editor`, and `viewer` roles.
- [x] Preserve the existing archive owner as bootstrap admin.
- [x] Enforce role-aware RLS across archive data.
- [x] Add email/password sign-in independent of Gmail.
- [x] Replace invite-only registration with self-service password registration plus disabled-by-default membership.
- [x] Add admin access UI/API for invites, roles, and active/disabled status.
- [x] Add last-active-admin database protection.
- [x] Add optional Google Sign-In and Magic Link under the same membership model.
- [x] Move invite codes from query strings to URL fragments and clear them after browser prefill.
- [x] Verify hosted database state; latest live check on 2026-10-03 shows two active admins, one active viewer, one accepted invite, and zero real archive letters.
- [x] Verify final-admin disable attempt is rejected by the live database trigger.
- [x] Full synthetic suite passes 249/249.
- [ ] Enable Supabase leaked-password protection when Management/Dashboard configuration is available.
- [x] Create and activate an additional dedicated admin account.
- [ ] Complete the real authenticated HTTP/PostgREST multi-role vertical-slice test with actual sessions.


## Multi-user runtime verification update

- [x] Verify hosted viewer read / write-deny behavior.
- [x] Verify hosted editor insert/update / delete-deny behavior.
- [x] Verify hosted non-member read/insert denial.
- [x] Verify hosted admin delete behavior.
- [x] Verify all synthetic users/rows/memberships were removed after the test.
- [x] Add one-click registration-email onboarding for pending invites.
- [x] Full synthetic suite passes 251/251.
- [ ] Complete the real short-lived owner bearer-session/PostgREST vertical slice through the normal browser/email completion path.


## Password-based independent login

- [x] Add authenticated member password set/change endpoint.
- [x] Add signed-in Account UI with password confirmation.
- [x] Keep Magic Link as recovery/passwordless login.
- [x] Require active archive membership before password update.
- [x] Unauthenticated password update fails closed with HTTP 401.
- [x] Full synthetic suite passes 255/255.
- [x] Complete one real owner browser session and set the bootstrap admin password.


## Magic Link callback repair

- [x] Confirm real Supabase Magic Link redemption succeeded.
- [x] Confirm archive-owner Auth user id matches active admin membership.
- [x] Identify DLR callback failure as HTTP 422 in session-from-fragment.
- [x] Remove unnecessary fixed token-shape assumptions while preserving Supabase + membership validation.
- [x] Pass full synthetic suite: 256/256.
- [ ] Complete browser retry and verify DLR HttpOnly session cookie creation.


## Second admin onboarding

- [x] Create a second administrator invite through the normal archive-admin RPC.
- [x] Send invite-validated registration email.
- [x] Confirm the Auth user was created with invite metadata but remains unconfirmed.
- [x] Confirm database trigger activates membership only after email confirmation.
- [x] Complete email confirmation; accepted invite + active admin membership verified live.


## Vercel hosting

- [x] Add native Vercel FastAPI entrypoint and function configuration.
- [x] Create and link the `digital-letter-registry` Vercel project.
- [x] Configure production/preview Supabase URL, publishable key, archive ID, and real-intake-off flag.
- [x] Deploy production successfully.
- [x] Disable redundant Vercel Authentication protection.
- [x] Verify home/health/auth endpoints return HTTP 200.
- [x] Verify recent Vercel error log scan is clean.
- [ ] Add Vercel origin to Supabase Auth redirect allow-list.
- [ ] Authorize Vercel GitHub integration so pushes to `main` auto-deploy.
- [ ] Migrate only the intended Drive/original-access secrets if/when Vercel should serve originals directly.


## Simple account creation

- [x] Make `zzpsah@gmail.com` an active DLR admin.
- [x] Add `Create Account` with email/password/confirm-password.
- [x] Remove Magic-Link controls from the primary UI.
- [x] Auto-create new archive memberships as `viewer / disabled`.
- [x] Add protected admin confirmation Edge Function.
- [x] Confirm account when admin changes pending member to Active.
- [x] Keep role/status approval in the DLR admin panel.
- [x] Deploy final Vercel build and verify canonical UI/health.
- [x] Run 257/257 tests successfully.
- [ ] Reconcile the hosted pending-membership trigger into a repository migration file when an allowed migration-source path is available.
- [ ] Optionally disable legacy Magic-Link backend routes after a deprecation period.


## Gemini-independent processing fallback

- [x] Add conservative deterministic context provider using checked-in Hindi/English vocabulary.
- [x] Allow worker completion when semantic embeddings are unavailable.
- [x] Use deterministic context + OCR/full-text indexing when `GEMINI_API_KEY` is absent.
- [x] Treat Gemini as optional in Oracle runtime readiness.
- [x] Verify Oracle scoped readiness reports fully ready in synthetic-only mode.
- [x] Full synthetic suite passes 261/261.
- [ ] Add Gemini later for richer structured context + semantic embeddings; historical records can be reprocessed then.


## Dedicated Oracle worker identity

- [x] Add worker transport that can sign in a dedicated non-human Supabase account with email/password.
- [x] Keep direct `SUPABASE_ACCESS_TOKEN` only as a one-shot/manual integration fallback.
- [x] Add tests for direct-token preference, dedicated worker sign-in, and missing worker credentials.
- [x] Full synthetic suite passes 264/264.
- [x] Provision dedicated worker Auth identity. (Signup created on 2026-10-03 with the intended Bitwarden-backed credentials; email confirmation is still required before password login works.)
- [x] Store `DLR_SUPABASE_WORKER_EMAIL` and `DLR_SUPABASE_WORKER_PASSWORD` in Bitwarden and verify wrapper injection reaches Supabase Auth.
- [ ] Confirm the dedicated worker email address.
- [ ] Assign/verify minimum `editor` archive membership for the worker.
- [ ] Run one-shot worker login/idle verification.
- [ ] Enable Oracle worker timer only after the one-shot verification passes.
- [ ] Complete synthetic upload → Drive → queue → worker → search/open-original vertical slice.
