# Runtime Verification — Handoff

Read project AGENTS/RULES, .ai state, root TASKS, brain root state, and this enhancement folder before continuing.

Next safe action is completing the real short-lived authenticated HTTP/PostgREST synthetic vertical slice using the supported default hosted Magic Link flow. Keep all credentials runtime-only. Do not confuse DB-level simulated JWT-claim verification with the pending real user-session test.

2026-10-02 runtime findings:
- Repository custom-template artifact is correct: `supabase/templates/magic-link.html` sends `token_hash` to `/auth/confirm`.
- Hosted Supabase uses the default direct-confirmation email flow; Dashboard inspection confirmed custom SMTP is required before email template body editing.
- The app now supports the default fragment callback securely, so custom SMTP/template configuration is optional. A guarded Management API helper remains implemented for that optional future path.
- Archive-owner magic-link delivery works.
- Connected remote execution blocked forwarding a one-time auth token to the VPS. Do not bypass this; use the proper server callback or another credential-safe path.
- Auth/API suite passes 28/28; full VPS synthetic suite passes 208/208; Management Auth-config helper focused tests pass 4/4.
- Connected Google Drive access re-verifies the private archive structure and the single synthetic integration PDF in `originals/`.
- Existing VPS `phone_drive` rclone cannot enumerate archive contents even when direct archive/originals folder IDs are supplied. Treat it as unusable for Digital Letter Registry runtime access.
- Refreshable Google Drive OAuth and end-to-end original streaming remain unverified.
- A dedicated Google OAuth client exists in the private vault from the earlier attempt, but Bitwarden CLI is unavailable on both the connected Windows host and VPS, so automatic credential retrieval is not currently possible.
- Gemini runtime key is still unavailable; no live Gemini synthetic verification has been completed.

One synthetic verification row currently remains and should be removed only through an authorized successful cleanup path.
