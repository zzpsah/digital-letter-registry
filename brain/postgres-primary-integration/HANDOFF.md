# Handoff — PostgreSQL Primary Integration

Last reconciled: 2026-10-16.

## First read
1. PostgreSQL Services: `projects/official-letter-intelligence/database-operations/docs/DLR-POSTGRES-INTEGRATION-STATUS-2026-10-16.md`
2. PostgreSQL Services: `docs/PROJECT-ONBOARDING.md` (how this database was created and how future projects are to be added)
3. DLR: `brain/CURRENT_STATE.md`, `brain/TASKS.md`, and this folder.
4. PostgreSQL Services: `docs/LOCAL-PRIMARY-PLAN.md`, `docs/SCHEMA-DRIFT.md`, and `ansible/README.md`.

## Verified checkpoint
- PostgreSQL primary and compatibility APIs are healthy; authenticated login/search/detail/original and unauthenticated access rejection were tested.
- Full DLR test suite is green: 377 passed.
- Fresh local and off-site encrypted backups both restored successfully to disposable databases with 19 tables and 28 functions.
- Ansible validation passed without deploying or restarting services.
- Queue integrity is clean and no active jobs remain.
- Direct Gemini synthetic text/file analysis passed. One real source-conflict result remains low-confidence and flagged for human review; do not treat processing completion as semantic acceptance.

## Next steps
1. Keep the source-conflict record and second reprocessing candidate in human-review state; do not bulk-reprocess.
2. Review historical failed jobs individually if recovery is needed; do not bulk-retry real letters.
3. Reconcile live Oracle schema/migration drift before any future DLR schema migration.
4. Keep hosted Supabase marked as a DR candidate until sync, freshness, restore, failover and failback are tested.
5. Generic project provisioning and registry-driven local/off-site backup wrappers are now implemented and tested against a disposable database; the registry contains only `dlr_primary`. Use PostgreSQL Services `docs/PROJECT-ONBOARDING.md` for the next approved project. n8n orchestration remains the next phase, not part of this release.
