# Vercel Hosting — Current State

Last reconciled: 2026-10-10

## Production deployment

Canonical production URL: `https://eletters.vercel.app`.

Production has been deployed and verified over HTTPS. The public app/control plane uses Vercel and Supabase; private Google Drive storage authorization, original-file access, OCR binaries, and background worker responsibilities remain on the Oracle runtime.

## Public entry points — 2026-10-10

The root route was changed from the interactive app shell to a public product-information homepage as part of the OAuth homepage-verification work (commit `025c752c0726992c0c3d4bef67c561a1c4d2b614`).

- `/` — public UMV Storage Automation / eLetters product-information homepage; explains document preservation, organization, and search for authorized school staff, and links to sign-in and the Privacy Policy.
- `/app` — existing eLetters application/authentication interface.
- `/privacy-policy` — public privacy policy.
- `/api/v1/health` — public health endpoint.

Live HTTP checks on 2026-10-10 returned 200 for `/`, `/app`, `/privacy-policy`, and `/api/v1/health`. The root page is intended to support public website information required for OAuth consent-screen review. This route change alone does not establish Google OAuth app approval or generate/renew a Google Drive refresh token.

## Authentication and access

- The normal DLR login is email + password through Supabase Auth.
- Account creation is available at `/app`; newly registered members remain disabled until an admin approves the account and assigns the appropriate role.
- The redundant Vercel Authentication gate is disabled; DLR Supabase authentication and archive-membership/RLS/API controls govern protected app access.
- Password-first login does not depend on Supabase redirect allow-list entries. Such entries remain relevant only if optional Magic Link or Google Sign-In flows are enabled again.

## Deployment boundary and safety

Vercel currently owns the public homepage, application UI, password authentication/session, self-registration/admin approval UI, and Supabase-backed search/admin control plane.

Oracle currently owns private Google Drive OAuth, original-file access, OCR/system binaries and language packs, and private document-worker responsibilities. Do not copy private Drive OAuth credentials into Vercel just to support the public homepage. The homepage is informational; it does not make private archive documents public.

The controlled approved WhatsApp real-document pilot remains on the private Oracle side. Preserve the existing intake authorization and mutation gates; the Vercel deployment does not receive private Drive upload credentials as part of this change.

## Verification boundary

Verified production route availability is not the same as approval by Google OAuth verification. Re-check Google Cloud OAuth consent-screen/publishing status separately if an OAuth warning or token-lifetime issue occurs. Check current source/runtime evidence before claiming automatic Vercel deployment or OAuth verification has completed.
