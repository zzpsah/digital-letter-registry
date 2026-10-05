# Project Brain — Handoff

Before meaningful work, read `AGENTS.md`, `RULES.md`, README/PRD, `.ai/manifest.yaml`, `.ai/STATE-INDEX.md`, `.ai/PROJECT.md`, `.ai/CURRENT-STATE.md`, root `TASKS.md`, `brain/README.md`, and the relevant enhancement brain.

Repository evidence is authoritative over chat memory. After meaningful work, synchronize source evidence plus all affected README/docs, root tasks, `.ai/`, and relevant `brain/` records.

Current runtime checkpoint:
- DB-level synthetic owner RLS insert/read and wrong-user denial are verified using simulated request JWT claims.
- Checked-in magic-link template uses the server-side token-hash callback, but hosted Supabase email templates cannot be edited on the current default mailer without custom SMTP. This is no longer a blocker: the app now supports Supabase's default fragment callback, validates the owner server-side, converts the session to HttpOnly cookies, and clears fragment tokens. The Management API helper remains available for an optional future custom-SMTP path.
- VPS auth/API tests pass 29/29; full synthetic suite passes 212/212; Supabase Management Auth-config helper tests pass 4/4.
- DLR has a dedicated tailnet-only HTTPS runtime origin; Supabase Site URL/redirect configuration is aligned to it. Do not publish the private hostname/port in Git.
- A real short-lived authenticated HTTP/PostgREST vertical slice is still pending. The current blocker is Supabase email-send throttling; magic-link throttles now return HTTP 429 rather than 500.
- Dedicated DLR Google OAuth is configured through secret-manager-injected refresh credentials with a write-capable Drive grant; refresh/list/stream and disposable synthetic upload/stream/delete verification passed.
- The existing `phone_drive` rclone credential remains separate and unused by DLR.
- Current runtime readiness has Drive configured; Gemini is the only failing readiness check.
- Gemini runtime key remains unavailable.
- The synthetic DB verification row was removed through controlled cleanup; no archive-letter rows exist.

Do not deploy, ingest real documents, activate live connectors, rename real Drive files, configure or expose secrets, or perform destructive live-data actions without the required explicit authorization.


## Drive account handoff

- Current private deployment is single archive-owner/single archive tree.
- DLR code itself is not tied to that account.
- To use another Google Drive, authorize that account separately and configure separate secret-manager OAuth keys plus archive folder references.
- Never silently reuse another deployment's refresh token or switch its target folders.


## Auth boundary

Magic Link/passwordless email authentication is an identity/session layer only. It exists so Supabase RLS can enforce owner-scoped database access and so future users/schools can remain isolated. It does not replace Tailscale, does not grant Google Drive access, and does not authorize real ingestion/rename/delete actions by itself.


## Google Sign-In handoff

Application support is complete and 220/220 synthetic tests pass. Supabase currently reports Google provider disabled. Resume from `brain/google-signin/`. Create a separate Google Web OAuth client, configure Supabase Google provider, then prove the existing archive-owner user id is preserved through automatic identity linking before running the real authenticated synthetic RLS vertical slice.


## Multi-user authorization handoff

The hosted archive now uses membership/role authorization rather than a configured single-owner check.

- Authentication providers are interchangeable; Gmail/Google is not required.
- Email/password and Magic Link work under the same membership model; Google Sign-In is optional.
- Registration is invite-only.
- Roles are admin/editor/viewer and are enforced by RLS plus API checks.
- The bootstrap owner is currently the sole active admin.
- The database prevents loss of the last active admin; live disable test passed.
- Admin invite/member management is implemented.
- Invite links use fragments rather than query parameters.
- Full synthetic suite passes 249/249.
- Supabase leaked-password protection is still disabled and should be enabled when Auth configuration access is available.
- Resume from `brain/multi-user-authz/`.

## Latest web UI handoff — 2026-10-05

Treat the current responsive eLetters shell as the UI baseline. Preserve the compact English-default navigation and mobile breakpoints. Do not regress Admin back to add-only recipient/WhatsApp controls: current entries must remain visible and manageable.

## Admin operations handoff — 2026-10-05

Preserve the Overview and Audit tabs and route WhatsApp group actions through the Oracle proxy when running on Vercel. Keep group descriptions plain text. Never convert send+pin into editing an assumed stale message ID: create a fresh message, pin it, then update runtime state. Audit persistence is best-effort after external side effects so a temporary audit write failure does not falsely report an already-completed WhatsApp/recipient action as rolled back.
