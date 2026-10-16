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

## Remaining before release sign-off
- [ ] Final review of all DLR implementation changes and ensure no unrelated work is included; commit/push reviewed changes.
- [ ] Deploy the committed `main` revision using the guarded Ansible application-deploy path; repeat live health, authenticated search/detail/original, and queue checks.
- [ ] Verify worker/timer behavior after deployment without queuing any additional real documents; confirm notification side effects remain unchanged.
- [ ] Keep the low-confidence source-conflict record and second reprocessing candidate flagged for human review.
- [ ] Review historical network-timeout failures individually if recovery is needed; do not bulk-retry real letters.

## Longer-term database/DR work
- [ ] Reconcile live Oracle schema, migration lineage, bootstrap compatibility SQL, and grants/RLS before the next schema change.
- [ ] Implement a generic, least-privilege project database provisioning procedure and extend scheduled local/off-site backups to all approved project databases.
- [ ] Implement one-way Oracle-to-Supabase recovery synchronization, freshness alerts, measured RPO/RTO, and manual failover/failback drills.
- [ ] Design the n8n workflow only after the database onboarding procedure is repeatable, auditable, and tested.
