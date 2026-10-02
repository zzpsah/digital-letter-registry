# Runtime Verification — Handoff

Read project AGENTS/RULES, .ai state, root TASKS, brain root state, and this enhancement folder before continuing.

Next safe action remains the real short-lived authenticated HTTP/PostgREST synthetic vertical slice. Keep all credentials runtime-only. Do not confuse DB-level simulated JWT-claim verification with the pending real user-session test.

2026-10-02 runtime findings:
- Archive-owner magic-link delivery is working.
- Hosted Supabase email currently uses the default direct confirmation URL; the app's server callback is designed for a token-hash verification flow. Configure the hosted template/Site URL before treating browser/server auth as complete.
- The connected remote execution layer blocked forwarding a one-time auth token to the VPS. Do not bypass this; use the proper server callback or another credential-safe path.
- Connected Google Drive access re-verified the private archive structure and the single synthetic integration PDF in `originals/`.
- The VPS's existing read-only rclone remote does not expose the archive path, so it is not a substitute for the pending Drive OAuth runtime credentials.
- Refreshable Google Drive OAuth and end-to-end original streaming remain unverified.

One synthetic verification row currently remains and should be removed only through an authorized successful cleanup path.
