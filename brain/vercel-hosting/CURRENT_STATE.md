# Vercel Hosting — Current State

Work started after explicit user approval to host DLR on Vercel. No production deployment has been completed yet.


## Production deployed

Production URL: `https://digital-letter-registry.vercel.app`

Status:
- Vercel project created and linked;
- FastAPI production deployment READY;
- required Supabase public/runtime configuration stored in Vercel environments;
- real intake explicitly disabled;
- redundant Vercel Authentication disabled;
- home, health and auth-provider endpoints verified HTTP 200;
- recent production error scan clean.

Not yet migrated:
- Google Drive OAuth/private original access;
- OCR/system-binary worker functions;
- other Oracle-only worker responsibilities.

Pending:
- Supabase Auth redirect allow-list for the Vercel origin;
- Vercel GitHub integration authorization for automatic deployments.


## Account UI update

The canonical Vercel UI now uses password-first authentication:
- canonical alias: `https://umv-dlr.vercel.app`;
- simple Create Account form is visible;
- primary Magic-Link UI is removed;
- pending accounts are admin-approved from the access panel;
- health and home return HTTP 200;
- latest test suite is 257/257 PASS.

The Supabase `dlr-confirm-account` Edge Function is part of account approval and runs outside Vercel. It confirms the target Auth identity only after verifying an active archive-admin caller.
