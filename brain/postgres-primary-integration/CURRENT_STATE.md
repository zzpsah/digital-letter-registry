# PostgreSQL Primary Integration — Current State

Observed 2026-10-16 on Oracle VPS unless stated otherwise.

## Database plane
- PostgreSQL 16 + pgvector runs in Docker container `dlr-postgres`; database `dlr_primary`; listener is loopback-only at `127.0.0.1:5432`.
- Live catalog check: 19 public base tables, 28 public functions, 18 public tables with RLS enabled.
- Current row counts: 68 letters, 68 letter_processing rows, 102 processing_jobs; 4 jobs failed and 0 pending/processing at the observed checkpoint. Counts change with normal operation.
- Local GoTrue and PostgREST are behind the FastAPI compatibility bridge. The application retains Supabase-compatible Auth/REST/RPC route contracts; this is a compatibility architecture, not proof all Supabase-specific auxiliary functions have been removed.

## Recovery
- Encrypted local and private Google Drive off-site backups and disposable restore checks were previously verified.
- Both `dlr-postgres-backup.timer` and `dlr-postgres-offsite-backup.timer` reported active during this checkpoint.
- Hosted Supabase is not a verified replica. No continuous replication, automatic failover, or failback is claimed.

## Application/worker checkpoint
- Direct Gemini API structured output was repaired and synthetic text + file analysis passed.
- A single controlled real archived-letter reprocess completed at worker status `complete/100%` using `gemini:gemini-3.5-flash-lite:context-v3`.
- That record still reported confidence 0.45 and `needs_reprocessing=true`; embedding version remained `unprocessed`. Therefore this proves the worker path executed, **not** that the extracted meaning is acceptable or that search/notification behavior is fully validated.
- Queue enqueue initially failed with RLS because `archive_id` was missing. The DLR working tree now resolves the target letter's `archive_id` before inserting a job. Focused job/Gemini tests passed 7/7; full suite currently has 2 failures in self-healing tests after a working-tree quality-version change.

## Repository state
- DLR working tree contains multiple pre-existing/uncommitted feature and test changes, including the queue fix. Do not reset, stage, commit, or deploy those changes as a group without review.
- PostgreSQL Services working tree contains an unrelated untracked migration `20261014163501_restore_osint_rpc_access.sql`; preserve it.
- See the cross-repository status note in PostgreSQL Services for the dependency matrix and gates.
