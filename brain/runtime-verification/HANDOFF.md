# Runtime Verification — Handoff

Read project AGENTS/RULES, .ai state, root TASKS, brain root state, and this enhancement folder before continuing.

Next safe action remains applying the hosted Supabase magic-link template/Site URL and then completing the real short-lived authenticated HTTP/PostgREST synthetic vertical slice. Keep all credentials runtime-only. Do not confuse DB-level simulated JWT-claim verification with the pending real user-session test.

2026-10-02 runtime findings:
- Repository template artifact is correct: `supabase/templates/magic-link.html` sends `token_hash` to `/auth/confirm`.
- Hosted Supabase email still uses the default direct confirmation URL, so live Auth configuration has not been applied.
- VPS has Supabase app runtime credentials but no Management API token/CLI login. A guarded Management API check/apply helper is implemented and tested; it is blocked only on the missing scoped management token.
- Archive-owner magic-link delivery works.
- Connected remote execution blocked forwarding a one-time auth token to the VPS. Do not bypass this; use the proper server callback or another credential-safe path.
- Focused auth/session/API suite passes 35/35; full VPS synthetic suite passes 205/205; Management Auth-config helper focused tests pass 4/4.
- Connected Google Drive access re-verifies the private archive structure and the single synthetic integration PDF in `originals/`.
- Existing VPS `phone_drive` rclone cannot enumerate archive contents even when direct archive/originals folder IDs are supplied. Treat it as unusable for Digital Letter Registry runtime access.
- Refreshable Google Drive OAuth and end-to-end original streaming remain unverified.
- A dedicated Google OAuth client exists in the private vault from the earlier attempt, but Bitwarden CLI is unavailable on both the connected Windows host and VPS, so automatic credential retrieval is not currently possible.
- Gemini runtime key is still unavailable; no live Gemini synthetic verification has been completed.

One synthetic verification row currently remains and should be removed only through an authorized successful cleanup path.
