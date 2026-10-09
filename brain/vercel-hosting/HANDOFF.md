# Vercel Hosting — Handoff

Read repository rules and this enhancement before continuing. Preserve the real-intake safety gate and keep heavy OCR/worker responsibilities separate from the Vercel control plane.

## Live deployment handoff — 2026-10-10

Canonical production URL: `https://eletters.vercel.app`.

Production entry points:
- `/` — public product-information homepage for UMV Storage Automation / eLetters.
- `/app` — actual eLetters sign-in/application interface.
- `/privacy-policy` — public privacy policy.
- `/api/v1/health` — health endpoint.

These four routes were checked over HTTPS and returned HTTP 200 on 2026-10-10. The public root page was introduced in commit `025c752c0726992c0c3d4bef67c561a1c4d2b614` for OAuth homepage information requirements; it does not itself verify/approve the Google OAuth app.

Do not assume Vercel has private Drive OAuth credentials. Google Drive authorization, original-file access, OCR/system-binary processing, and worker duties stay on Oracle. Preserve the existing real-intake gates. Use `/app` when validating password-first login; the root route is not the app shell.
