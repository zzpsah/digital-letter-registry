# Native PostgreSQL cutover plan

## Target

- Oracle PostgreSQL 16 is the only application database.
- FastAPI uses direct parameterized SQL through `psycopg`.
- Native DLR identity, password verification, signed access tokens and hashed refresh sessions replace GoTrue.
- Google Drive remains the private original-document store.
- Vercel serves the frontend and forwards API requests to the Oracle FastAPI service.

## Safety gates

1. Encrypted PostgreSQL backup and restore verification before schema changes.
2. Preserve existing user UUIDs and bcrypt password hashes during identity migration.
3. Preserve all 141 currently indexed letter records and their Google Drive object references.
4. Migrate archive membership, invitations, audit records, and every FK before retiring `auth.users`.
5. Convert every RPC that currently relies on `auth.uid()` to explicit, validated user/archive context.
6. Move worker and admin operations to the same native SQL repository.
7. Verify login, refresh, logout, password change, invitation, role checks, upload, OCR, search, archive, download and VidyaDesk summary before cutover.
8. Only then remove GoTrue, PostgREST, Supabase proxy routes, Supabase SDKs, environment variables and hosted Supabase calls.

## Current implementation stage

- `letter_registry.postgres_runtime` provides direct SQL CRUD/RPC transport, archive scoping, and native identity/session repository access.
- `letter_registry.native_auth` provides legacy bcrypt verification, Argon2 password hashing, signed access tokens, rotating hashed refresh tokens, session revocation, and account lifecycle operations.
- Oracle PostgreSQL now has additive `public.app_users`, `public.app_sessions`, and `public.app_email_tokens` tables. Existing four account UUIDs and password hashes were copied to `app_users`.
- Public-domain foreign keys now reference `public.app_users` (22 constraints). Auth-user write/delete compatibility triggers keep the identity mirror synchronized while the old gateway is drained.
- The full native identity SQL migration was validated in a rollback-only transaction, including native account activation, invite registration, admin account operations, and archive-account RPC replacements.
- The Oracle `dlr-api.service` is now running with native PostgreSQL and native password/session authentication enabled. The public Tailscale Funnel path `/dlr` reaches this API.
- The Vercel `app.py` reverse proxy is implemented and has been tested against the live native Oracle API, including HTML, provider discovery, and a password-auth request. It has **not yet been deployed** to the production Vercel project.
- The worker has a separate `DLR_NATIVE_WORKER_ENABLED` switch and a stable migrated worker user ID. It remains on its existing worker transport until its own cutover test is complete.
- Native mode supports password sign-in, invite/password registration, admin password resets, approved-account activation, and direct Google OIDC when a separate web OAuth client is configured. Magic-link sign-in is disabled in native mode. Google web OAuth credentials are not yet configured, so password sign-in is the current supported login method.
- GoTrue/PostgREST remain online as a compatibility fallback. Do not stop them until Vercel is switched, the worker is migrated, and the final production checks pass.
