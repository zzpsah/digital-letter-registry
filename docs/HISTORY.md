# History

- 2026-10-16: Verified `DLR_GEMINI_API_KEY` exists in Bitwarden Secrets Manager and the Oracle scoped runner injects it without exposing the value. Live synthetic text and original-file calls succeeded on the configured `gemini-3.5-flash-lite` model. Root cause of the direct API failure was invalid structured-output request syntax: changed to `responseMimeType` plus Gemini-compatible `responseSchema` conversion (including nullable fields). Supabase gateway remains blocked by HTTP 402 `exceed_egress_quota`; direct Gemini is the worker's preferred path. All 365 unit tests pass. Embeddings remain separately opt-in.

## 2026-10-09 — Restore DLR delivery and remove the 7-day credential expiry

- Diagnosed the DLR intake stall: the Google Drive OAuth refresh token had expired at 2026-10-09 14:29 UTC,
  exactly 7 days after issue, because the OAuth client was still in Testing mode. Three WhatsApp documents were
  stuck in the intake queue behind it.
- Published the OAuth app from Testing to In production, removing the recurring 7-day refresh-token lifetime.
- Completed archive-owner Drive re-consent for `umvtetahali@gmail.com` through a loopback PKCE callback on
  `http://127.0.0.1:53682/callback`, driven via a headless Chrome DevTools session on the same host. Google
  accepts only loopback redirect URIs for this client, so no tailnet or remote callback URL is usable.
- Verified the new token live (Drive scope, `originals` folder reachable) and rotated it into Bitwarden Secrets
  Manager; a secret-manager-only refresh then returned HTTP 200.
- Reprocessed the three stuck documents; their originals are in the Drive `originals` folder with populated
  letters metadata.
- Moved Gmail outbox delivery from an OAuth refresh token to a Gmail app password over `smtp.gmail.com:465`,
  stored as `DLR_GMAIL_APP_PASSWORD` in Bitwarden Secrets Manager. The wrapper
  `~/.local/bin/dlr-gmail-outbox-send-with-bitwarden` probes for the secret and keeps the OAuth path as a
  fallback, so delivery degrades instead of breaking if the app password is removed.
- Verified the SMTP path by authenticating through the scoped secret runner, delivering a live test message
  confirmed in the sender's Sent Mail over IMAP, and calling the production `_smtp_send()` directly (`smtp-sent`).
- Documented in the Oracle runbook that app passwords require 2-Step Verification on the sender account and are
  revoked when that account's main password changes.
- Retired temporary artifacts: OAuth handoff file, temporary consent helper unit, and the copied Chrome profile.
- Recorded that vector/semantic search is inactive — `letter_chunks` is empty because the worker's embedding
  stage is gated on an unprovisioned `GEMINI_API_KEY`. Keyword search is unaffected and covers full extracted
  text. Left as-is at the user's direction.

## 2026-10-10 — Google Drive OAuth View/Download incident

- Recorded the production symptom and evidence: Google OAuth refresh returned HTTP 401 `invalid_client` with an invalid-client-secret message; Bitwarden's saved OAuth Client ID was also found not to match the Vercel Production Client ID.
- The user later confirmed authenticated View and Download both worked.
- Documented the accurate boundary: recovery is user-verified, but the exact environment-variable change was not independently captured; do not claim a particular credential rotation without evidence.
- Added a safe recurrence checklist and explicitly prohibited logging/committing secrets or making private originals public.


## 2026-10-01 — Foundation

- Created public repository zzpsah/digital-letter-registry.
- Applied DevOS onboarding and verified MANAGED lifecycle state.
- Added privacy-safe product planning and foundation brain.

## 2026-10-01 — Domain foundation

- Added pure Python contracts for immutable document identity, processing versions, statuses/relationships, SHA-256 fingerprints, and smart filename derivation.
- Verified with five unit tests and Python compilation.

## 2026-10-02 — Naming and storage/database foundation

- Verified the private archive folder structure without committing private Drive identifiers.
- Verified the separate Supabase archive schema, RLS state, empty data state, and clean security advisor.
- Captured a public-safe schema migration in Git.
- Defined the official `short-title__issuer__date__reference-number.ext` naming contract.
- Added Unicode-safe Hindi/English/Hinglish filename generation and preview-only rename mapping.
- No real document was renamed, ingested, or deployed.


## 2026-10-02 — Secure browser runtime foundation

- Replaced browser token storage/URL-fragment handling with Supabase token-hash callback and HttpOnly cookie sessions.
- Added server-side session refresh and logout.
- Added same-origin CSRF protection for cookie-authenticated mutations.
- Added refresh-token-aware Drive runtime detection and secret-safe runtime capability/readiness status.
- Added an authenticated synthetic-first owner upload panel in the Hindi-first PWA.
- Application CI is green on the completed runtime/readiness baseline.
- Hosted Supabase Magic Link template/Site URL configuration remains an external dashboard step before the live browser synthetic test.
- No real archive letters were ingested or renamed and no production deployment was performed.

## 2026-10-06 — Context/handoff reconciliation

- Verified GitHub and Oracle runtime working copy at the same HEAD: `bbcce5a81c71cd98e0dd3d272349b6b41489c292`.
- Reconciled `brain/CURRENT_STATE.md`, `brain/HANDOFF.md`, and `.ai/CURRENT-STATE.md` so current truth is presented first instead of being buried beneath 2026-10-02 synthetic-only checkpoints.
- Explicitly separated current real WhatsApp pilot behavior from older synthetic cleanup milestones.
- Locked the source-first intelligence and same-document reprocess contracts into the top-level handoff.
- Historical checkpoints remain available in Git history, this file, `.ai/CHANGELOG.md`, and enhancement-specific brain folders.
- Runtime application code was not changed by this reconciliation.

## 2026-10-06 — Restore full archive visibility and speed up reprocess

- Home archive view now loads up to 100 documents latest-first instead of only six recent cards.
- Verified 28 active database documents, all Public, and 28/28 visible through editor RLS/search.
- Public Drive index was refreshed successfully with 28 documents.
- Manual/quality reprocess reuses existing extracted OCR text when available, avoiding expensive repeat OCR. Initial processing still OCRs documents when required.

## 2026-10-15 — Restore eLetters search visibility after auth recovery

- Diagnosed a live `403 Forbidden` from `search_letter_cards_v7`: the authenticated role lacked `SELECT` on the canonical authority reference tables used by the search function. Granted authenticated read access to `authorities` and `authority_aliases`; row-level security policies remain enabled and continue to scope rows to archive membership.
- Added migration `20261015181000_grant_archive_authority_read.sql` and committed it on `main` (`7eb538a`).
- Verified live search RPC and authority-list requests now return HTTP 200. The primary archive contains 68 letter rows (67 not trashed); all 68 stored Google Drive object references resolve through Drive metadata, and a read-only original download succeeded. One row is already in Trash; no originals were moved, deleted, or re-uploaded.
- Hardened the Home list against stale persisted pagination and silent fetch/JSON failures. Login now starts Home at page zero, invalid stale pages reset directly to page zero, and list failures display an actionable status rather than leaving an empty-looking panel.
- Bumped the service-worker cache version so the updated shell registration is picked up. Existing UI layout and styling were preserved.
- Verified the focused web-shell suite (24 tests). Production browser-level confirmation after deployment remains pending a user refresh/session check.

## 2026-10-16 — PostgreSQL primary integration and Gemini worker checkpoint

- Documented cross-repository ownership and dependency gates in `brain/postgres-primary-integration/` and the PostgreSQL Services database operations folder.
- Live Oracle PostgreSQL catalog check: 19 public tables, 28 public functions, 18 RLS-enabled tables. At the check, there were 68 letters, 68 letter_processing rows, 102 processing jobs, 4 failed jobs and no active jobs. Counts are operational snapshots.
- Both encrypted local/off-site backup timers reported active; previously verified disposable restore evidence remains documented in PostgreSQL Services.
- Direct Gemini structured output works in synthetic text and original-file tests. Supabase Gemini gateway remains quota-blocked; embeddings remain disabled.
- A controlled real reprocess completed at 100%, but output confidence was 0.45 and `needs_reprocessing=true`; this is not a semantic-quality pass.
- Diagnosed processing-job insert RLS failure: the job payload omitted target `archive_id`. DLR working tree now resolves the archive from the target letter and fails closed if unavailable; focused queue/Gemini tests passed 7/7.
- Full DLR suite ran 374 tests and had 2 self-healing failures after an uncommitted `document-quality-v3` version change. No production release is claimed; review/fix is required.
- No bulk reprocessing, embeddings backfill, RLS relaxation, or replication activation was performed.


## 2026-10-16 — DLR primary release verification

- Reviewed and pushed implementation commit `aa2c54d`; deployed Oracle checkout revision `b16c899` using the guarded Ansible path. The playbook completed 17 successful tasks, 2 expected changes, 0 failures and ran the full regression suite before restarting the API.
- Full DLR suite: 377 tests passed, 0 failures. Post-deploy API/Auth/REST health, authenticated search/detail/original access, unauthenticated rejection, queue-integrity checks and synthetic direct-Gemini text/file checks passed.
- Live queue snapshot: 103 jobs (99 completed, 4 failed, 0 active); no missing/mismatched archive IDs, orphan jobs or duplicate letter/reason jobs.
- One worker timer invocation overlapped the API restart and failed once with connection refused; the next scheduled run returned idle and the timer remained active.
- One low-confidence source-conflict record and a second reprocessing candidate remain flagged for human review. Hosted Supabase remains an unverified DR candidate, not a replica.


## 2026-10-16 — Bound source subject extraction

- Commit `1470fe17683dfc1b571e5cf526f376d907a9a4ad` removes multiline regex matching from source-subject extraction and conflict detection. When the subject is not followed by a recognized transition heading, the parser declines to guess instead of consuming body text.
- Added a regression case for a subject followed by ordinary body lines before the formal salutation. Focused tests passed 4/4; the full DLR suite passed 385/385.
- Live authenticated read-only smoke checks passed for search, detail, and original streaming; unauthenticated search returned HTTP 401. A temporary synthetic Oracle row passed authenticated archive/restore and important-mark/clear mutations, then was deleted and verified absent. No real letter was changed.
- The guarded Ansible deployment and post-deploy checks are the next release gate for this source commit.
