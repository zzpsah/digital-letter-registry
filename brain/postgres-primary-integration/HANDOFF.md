# Handoff — PostgreSQL Primary Integration

Last reconciled: 2026-10-16.

## First read
1. PostgreSQL Services: `projects/official-letter-intelligence/database-operations/docs/DLR-POSTGRES-INTEGRATION-STATUS-2026-10-16.md`
2. DLR: `brain/CURRENT_STATE.md`, `brain/TASKS.md`, and this folder.
3. PostgreSQL Services: `docs/LOCAL-PRIMARY-PLAN.md`, `docs/SCHEMA-DRIFT.md`, `ansible/README.md`.

## Immediate state
- The local PostgreSQL primary is running and both backup timers were active at the last check.
- One real reprocess completed but the derived result is low confidence (0.45) and still flagged for reprocessing. Do not treat as semantic acceptance.
- Queue enqueue was corrected in the DLR working tree to resolve the target letter's archive_id before insert. It is not yet a reviewed/released commit.
- Full DLR suite currently has two self-healing failures after a working-tree quality version change.
- DLR worktree contains other changes not created by this documentation checkpoint. PostgreSQL Services has an unrelated untracked SQL migration. Preserve both.

## Next sequence
1. Fix/reconcile the two self-healing tests.
2. Review all dirty DLR changes and run tests; stage/commit only reviewed files.
3. Test queue insert and RLS with the correct archive membership; inspect reprocess result and search/open-original behavior.
4. Run Ansible validation and fresh backup checks; deploy only from reviewed main.
5. Keep Supabase replication marked pending until verified.
