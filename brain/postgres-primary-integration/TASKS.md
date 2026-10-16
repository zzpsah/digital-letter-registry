# Tasks — PostgreSQL Primary Integration

## Verified complete on 2026-10-16
- [x] Record live Oracle PostgreSQL catalog and data counts; verify job `archive_id`/letter consistency and duplicate-job invariants.
- [x] Resolve the two self-healing test failures by making test quality-version expectations explicit.
- [x] Add a guard so low-confidence direct-Gemini output does not overwrite stronger unreviewed metadata unless it explicitly flags a source conflict; add regression tests for both paths.
- [x] Add subject/body conflict detection and human-review regression coverage.
- [x] Run the full DLR suite: 377 passed, 0 failures; Python compile and whitespace checks passed.
- [x] Verify direct Gemini text and synthetic-file analysis using the configured model.
- [x] Run authenticated login, search, detail and original-file smoke checks; verify private storage references stay out of detail JSON and unauthenticated access is rejected.
- [x] Run Ansible syntax and live validation checks without deployment/restart.
- [x] Create fresh encrypted local/off-site backups and restore both to disposable databases; both restore checks report 19 tables and 28 functions.
- [x] Confirm no active jobs and no missing/mismatched archive IDs; classify the four historical failed jobs without retrying them.
- [x] Document the actual PostgreSQL creation path and a future-project onboarding contract in PostgreSQL Services.

## Release verification completed; remaining quality/operational follow-ups
- [x] Review and commit/push the DLR implementation changes (`aa2c54d`, included in deployed revision `b16c899`). DLR `main` matches `origin/main`; working tree is clean.
- [x] Deploy the committed `main` revision through the guarded Ansible application-deploy path; all 17 Ansible tasks passed with 2 expected changes and 0 failures.
- [x] Repeat live health/Auth/REST checks, authenticated search/detail/original access, unauthenticated rejection, queue integrity, and synthetic direct-Gemini text/file checks after deployment.
- [x] Confirm the worker timer recovered after one transient connection-refused run during API restart; next scheduled run was idle, no active job, timer active. No new real document was queued for this verification.
- [ ] Keep the low-confidence source-conflict record and second reprocessing candidate flagged for human review.
- [ ] Review historical network-timeout failures individually if recovery is needed; do not bulk-retry real letters.

## Longer-term database/DR work
- [ ] Reconcile live Oracle schema, migration lineage, bootstrap compatibility SQL, and grants/RLS before the next schema change.
- [x] Implement generic least-privilege project database provisioning and registry-driven scheduled local/off-site backups; test against a disposable database and restore both backup types. Test database/roles were removed and registry returned to DLR-only.
- [ ] Implement one-way Oracle-to-Supabase recovery synchronization, freshness alerts, measured RPO/RTO, and manual failover/failback drills.
- [ ] Design the n8n workflow after an actual second project has an approved manifest/registry entry, project-specific Bitwarden secrets, reviewed migrations/RLS, and passing local/off-site restore checks.
