# History

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
