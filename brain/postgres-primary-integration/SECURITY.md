# Security and Data Handling

- PostgreSQL binds to loopback; never expose port 5432 directly.
- Keep local GoTrue/PostgREST behind the compatibility bridge and retain RLS, grants, archive membership checks, and role-specific API controls.
- Do not weaken RLS to work around job insert failures. Queue inserts require the actual target `archive_id` and an active member role.
- Never log or commit Bitwarden secrets, access/refresh tokens, JWT signing material, environment files, private Drive IDs/URLs, document contents, database dumps, or personal-data logs.
- Google Drive remains the private original store. Database backups are encrypted both locally and off-site; test restores only into disposable databases.
- Do not call hosted Supabase a replica until data freshness and recovery behavior are demonstrated.
- Keep embeddings disabled unless explicitly authorized; no automatic vector backfill.
- Treat Gemini output as untrusted derived data. Preserve prior stronger facts and flag low-confidence results for review.
- Preserve existing user-visible UI and access-control behavior; make minimal targeted changes.
- Keep unrelated dirty files in the DLR and PostgreSQL Services worktrees untouched.
