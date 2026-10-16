# PostgreSQL Primary Integration — Current State

Observed on Oracle VPS, 2026-10-16.

## Database plane
- PostgreSQL 16 + pgvector runs in Docker container `dlr-postgres`; database `dlr_primary`; listener is loopback-only at `127.0.0.1:5432`.
- Live catalog: 19 public base tables, 28 public functions, 18 public tables with RLS enabled; 53 public RLS policies.
- Data snapshot: 68 letters, 68 `letter_processing` rows, 102 processing jobs (98 completed, 4 failed, 0 active). These are point-in-time counts.
- Integrity checks passed: no job missing `archive_id`, no orphan job, no job/letter archive mismatch, and no duplicate `(letter_id, reason)` job pairs.
- Local GoTrue and PostgREST are behind the FastAPI compatibility bridge. PostgreSQL port 5432 remains private.

## Recovery and operations
- A fresh encrypted local backup and a fresh encrypted private Google Drive backup were created through the Ansible backup path.
- Both local and off-site snapshots restored into disposable databases; each reported 19 public tables and 28 public functions. The temporary restore databases were removed. Off-site hash verification and decryption passed.
- Ansible syntax check and read-only validation playbook passed (13 tasks successful, no changes, no failures). No deployment or service restart was performed during validation.
- Both daily backup timers are active. Latest disk check: 91% used, approximately 9.3 GiB free; recheck capacity before adding workload or retaining more backups.
- Hosted Supabase is not a verified replica. No continuous replication or automatic failover/failback is claimed.

## Application and worker validation
- Full DLR regression suite: **377 tests passed, 0 failures**. Python compile check and `git diff --check` passed. A Starlette/httpx deprecation warning and existing ResourceWarnings remain non-failing cleanup items.
- Direct Gemini text and synthetic-file analysis passed using `gemini-3.5-flash-lite` through the Bitwarden-scoped key injection. The worker code selects direct Gemini whenever `GEMINI_API_KEY` is available; the quota-blocked Edge gateway is not needed for that path.
- Live authenticated worker login, search, letter detail and original-file retrieval passed. Detail JSON did not expose private storage references. Unauthenticated search and original-file requests were rejected (401).
- Queue code now resolves the target letter's `archive_id` before inserting a job and fails closed if the letter is not visible. Unit tests cover the insert contract and inaccessible-letter case; live queue integrity checks passed.
- Subject/body mismatch handling now creates a clear source-conflict warning, lowers confidence, and requires human review. The one known low-confidence Gemini result is explicitly conflict-marked and still has `needs_reprocessing=true`. One other record is also flagged for reprocessing. No additional real documents were queued during this validation.
- Embeddings remain disabled; no vector backfill was started.

## Release and repository state
- The reviewed implementation is still in the DLR working tree and has not been deployed in this validation pass. Keep the changes uncommitted until the final diff review and then commit/push before the guarded Ansible deployment.
- PostgreSQL Services has a separate, unrelated untracked migration `20261014163501_restore_osint_rpc_access.sql`; preserve it.
- Four historical jobs remain failed: two classified as prior RLS/archive-scope failures and two as network/timeout failures. There are no active jobs. Do not bulk-retry them; review any real-document retry separately.

## Remaining release/DR gates
- Review the exact DLR diff, run the full suite again, commit/push reviewed changes, deploy from canonical `main`, and repeat production smoke checks.
- Keep the conflict-marked low-confidence record and the other reprocessing candidate in human-review state; do not treat `completed` as semantic acceptance.
- Reconcile the live Oracle schema against migration/bootstrap history before any schema migration. Do not blindly replay the DLR migration directory.
- Hosted Supabase remains a DR candidate, not a replica. One-way synchronization, freshness/lag alerts, RPO/RTO, and tested failover/failback remain future work.
- Google OAuth/magic-link delivery and embeddings are not certified by these checks.
