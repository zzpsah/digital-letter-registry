# Decisions

## Accepted
- Oracle PostgreSQL `dlr_primary` is the primary transactional data plane for the migrated DLR workload.
- Keep PostgreSQL port 5432 loopback-only; expose only the compatibility bridge through the established route.
- Preserve Supabase-compatible Auth/REST/RPC paths to avoid unnecessary application-wide rewrites.
- Keep Google Drive originals and independent encrypted backups; the database is not the only copy of a document.
- PostgreSQL Services owns schema/migrations/backup/DR; DLR owns application/worker code; Oracle VPS repository owns host/service automation.
- Use Ansible as the repeatable validation/deployment entry point. Do not treat it as a database migration or replica by itself.
- Keep hosted Supabase labeled as a DR candidate until one-way sync, freshness, restore and failover/failback are tested.
- Gemini embeddings are explicitly opt-in; no embedding backfill without a separate decision.

## Operational guardrails
- Never weaken RLS to make the worker pass.
- A queue row must include the target letter's actual `archive_id`; resolve it from the letter under the authenticated transport and fail closed if invisible/missing.
- Reprocess must update the same logical letter, preserve stronger existing facts, avoid duplicate jobs/delivery, and remain reviewable when confidence is low.
- Do not claim production-ready document intelligence solely from `status=completed`.
- Preserve unrelated dirty/untracked files in both repositories.
