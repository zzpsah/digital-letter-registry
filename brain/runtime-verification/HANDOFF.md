# Runtime Verification — Handoff

Read project AGENTS/RULES, .ai state, root TASKS, brain root state, and this enhancement folder before continuing.

The real short-lived bearer/PostgREST and authenticated HTTP synthetic vertical slices are complete. Keep credentials runtime-only and preserve `ENABLE_REAL_INTAKE=false` until real archive ingestion is explicitly authorized.

2026-10-02 runtime findings:
- Repository custom-template artifact is correct: `supabase/templates/magic-link.html` sends `token_hash` to `/auth/confirm`.
- Hosted Supabase uses the default direct-confirmation email flow; Dashboard inspection confirmed custom SMTP is required before email template body editing.
- The app now supports the default fragment callback securely, so custom SMTP/template configuration is optional. A guarded Management API helper remains implemented for that optional future path.
- Archive-owner magic-link delivery works.
- Connected remote execution blocked forwarding a one-time auth token to the VPS. Do not bypass this; use the proper server callback or another credential-safe path.
- Auth/API suite passes 29/29; full VPS synthetic suite passes 212/212; Management Auth-config helper focused tests pass 4/4.
- DLR runtime is isolated behind its own tailnet-only HTTPS origin. Password-first bearer verification no longer depends on email/Magic-Link throttling.
- Dedicated DLR Google OAuth is configured with secret-manager-injected refresh credentials; refresh exchange, originals listing, and synthetic-original streaming all passed. The write-capable grant is now verified with synthetic upload/stream/delete cleanup.
- Existing VPS `phone_drive` rclone remains separate and must not be reused for DLR.
- Runtime write/upload is verified with the write-capable grant using a disposable synthetic object; upload, stream/content verification, delete cleanup, and catalog restoration all passed.
- Gemini runtime key is still unavailable; no live Gemini synthetic verification has been completed.

The synthetic verification row was removed through the authorized controlled cleanup path; `letters` is empty.


## Authentication scope

The pending real owner-session test is specifically an **identity + Supabase RLS authorization proof**.

Passwordless email/Magic Link login should prove that:
1. the intended archive owner receives and completes the login;
2. DLR establishes a server-managed authenticated session;
3. Supabase sees the real authenticated user identity;
4. owner-scoped rows are accessible only to that identity;
5. an unauthorized/wrong-user session is denied by RLS.

This test is not a Google Drive authorization test and does not authorize real archive mutation. Drive OAuth, network access, and mutation approvals remain separate controls.


## 2026-10-03 completion note

Live bearer insert/read + RLS denial passed. Authenticated HTTP session/search passed. Disposable HTTP upload → Drive → queue → worker → search → original stream passed, byte comparison passed, and all synthetic artifacts were removed. Full suite passes 266/266. Baseline runtime verification is complete.
