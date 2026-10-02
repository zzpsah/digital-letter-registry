# Project Brain — Handoff

Before meaningful work, read `AGENTS.md`, `RULES.md`, README/PRD, `.ai/manifest.yaml`, `.ai/STATE-INDEX.md`, `.ai/PROJECT.md`, `.ai/CURRENT-STATE.md`, root `TASKS.md`, `brain/README.md`, and the relevant enhancement brain.

Repository evidence is authoritative over chat memory. After meaningful work, synchronize source evidence plus all affected README/docs, root tasks, `.ai/`, and relevant `brain/` records.

Current runtime checkpoint:
- DB-level synthetic owner RLS insert/read and wrong-user denial are verified using simulated request JWT claims.
- Checked-in magic-link template uses the server-side token-hash callback, but hosted Supabase email templates cannot be edited on the current default mailer without custom SMTP. This is no longer a blocker: the app now supports Supabase's default fragment callback, validates the owner server-side, converts the session to HttpOnly cookies, and clears fragment tokens. The Management API helper remains available for an optional future custom-SMTP path.
- VPS auth/API tests pass 28/28; full synthetic suite passes 208/208; Supabase Management Auth-config helper tests pass 4/4.
- A real short-lived authenticated HTTP/PostgREST vertical slice is still pending.
- Connected Drive access verifies the private archive and synthetic original.
- The existing VPS `phone_drive` rclone credential cannot enumerate archive contents even with direct folder IDs, so it is not suitable for registry Drive runtime access.
- Gemini runtime key remains unavailable.
- A dedicated Google OAuth client exists in a private vault from the earlier attempt, but Bitwarden CLI is unavailable locally and on the VPS, so current tooling cannot retrieve it automatically.
- The synthetic DB verification row was removed through controlled cleanup; no archive-letter rows exist.

Do not deploy, ingest real documents, activate live connectors, rename real Drive files, configure or expose secrets, or perform destructive live-data actions without the required explicit authorization.
