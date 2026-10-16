# Tasks

## Completed / observed
- [x] Record live Oracle PostgreSQL catalog counts: 19 public tables, 28 public functions, 18 RLS-enabled public tables.
- [x] Verify local and off-site backup timers report active.
- [x] Verify one controlled reprocess completed through the direct Gemini worker path.
- [x] Identify missing `archive_id` on processing-job enqueue as an RLS failure cause.
- [x] Add target-letter archive lookup to DLR queue enqueue and focused regression coverage in the working tree.

## Required next
- [ ] Resolve two failing full-suite tests in `test_self_healing.py`; current working-tree `QUALITY_VERSION=document-quality-v3` changed the expected recovery behavior.
- [ ] Review the full DLR working-tree diff; distinguish prior user work from the queue fix; do not commit unrelated edits together.
- [ ] Verify the completed document's source-grounded fields and low-confidence handling with privacy-safe assertions; confidence 0.45 and `needs_reprocessing=true` remain a quality warning.
- [ ] Run authenticated RLS/job lifecycle tests with an archive editor and verify the job includes the correct `archive_id`.
- [ ] Verify keyword search/detail/original access after reprocess; confirm no unintended mail/WhatsApp delivery.
- [ ] Run Ansible syntax check and validation playbook; deploy only from reviewed, committed `main`.
- [ ] Reconcile schema migration count/drift and root README/current-state contradictions in PostgreSQL Services.
- [ ] Implement and test one-way Oracle-to-Supabase recovery sync, lag/freshness monitoring, restore and manual failover/failback.
- [ ] Define measured RPO/RTO and alerts; retain immutable encrypted snapshots.
- [ ] Remove the remaining Gemini Edge Function dependency from normal worker operation; gateway is still quota-blocked.
- [ ] Re-run full suite and production smoke checks after fixes; update both repositories.
