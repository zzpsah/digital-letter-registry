# History

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
