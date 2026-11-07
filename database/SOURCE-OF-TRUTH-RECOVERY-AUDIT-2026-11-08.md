# DLR source-of-truth and recovery audit — 2026-11-08

## Decision

The authoritative DLR system of record is split by data type:

1. **Oracle PostgreSQL `dlr_primary`** — canonical structured letter records, archive and membership records, source provenance, processing state/jobs, relationships and searchable metadata.
2. **Configured private Google Drive archive** — canonical original PDF/image bytes. PostgreSQL stores each original's Drive object reference.
3. **Hosted Supabase** — historical/divergent legacy copy. It is not the current DLR source of truth and is not a verified replica. Do not promote it or use it to overwrite Oracle.

## Live production snapshot (read-only verification)

| Dataset | Count |
|---|---:|
| Archives | 1 |
| Archive memberships | 4 |
| Native users | 4 |
| Letters | 144 |
| Letter sources | 148 |
| Letter processing rows | 144 |
| Processing jobs | 191 |
| Letter relationships | 41 |

All 144 letter rows use the Google Drive storage provider and have an object reference. Read-only Drive metadata checks confirmed all 144 distinct referenced objects are accessible and not trashed. Their aggregate reported size was approximately 360 MB. This verifies object availability metadata, not a byte-for-byte content checksum for every original.

The public index contains 136 cards, matching the live public/non-trashed/non-archived filter. The remaining eight rows are one personal, two private and five trashed records. The index is a derived presentation/cache, not the source of truth.

## Backup recovery evidence

Two independent encrypted snapshots dated 2026-11-07 were restored into disposable PostgreSQL databases and then cleaned up:

- Local encrypted backup: `dlr-primary-dlr_primary-20261107T023038Z.dump.gpg`.
- Private off-site backup: `dlr-primary-dlr_primary-20261107T030459Z.dump.enc`.

Both restore checks passed. The off-site path also passed remote SHA-256 verification, decryption and PostgreSQL archive listing. Both snapshots restored 22 public tables, 35 public functions, one archive, four memberships, 141 letters, 145 sources, 187 jobs and four native users.

The live database is newer than these snapshots by:
- 3 letters;
- 3 source records;
- 4 processing jobs;
- 2 relationships.

**Never restore either November 7 snapshot over the live primary without reconciling and preserving this post-snapshot delta.** These backups prove recoverability, not permission to roll production backward.

## Recovery-script warning

Use the canonical registry-driven backup/restore scripts under the PostgreSQL Services project and the database-specific pointer `LATEST-dlr_primary.txt`. A legacy global `LATEST.txt` pointer was observed to identify a Report Central backup. Never assume a global pointer belongs to DLR; the canonical restore script validates the requested database identity.

## Earlier zero-row observation corrected

An initial row-level query omitted the configured archive-member identity in its RLS context and returned zero rows. That result was invalid as an archive-wide count. Subsequent worker-context queries and independent administrative aggregate counts verified the live data shown above. Do not use the earlier zero-row result for operational decisions.

## Current safety gates

- Do not apply the prepared native-auth detachment migration yet.
- Do not retire hosted Supabase until authenticated end-to-end checks pass and all remaining live dependencies are accounted for.
- Do not restore over production or promote the hosted Supabase copy.
- Reconcile the three post-snapshot letters and associated provenance/processing/relationship rows, including Drive references and user/archive ownership.
- Verify authenticated login, archive membership, search, original viewing and downloads before declaring recovery complete.
- Verify actual original-file bytes/checksums for a representative sample, then expand verification as needed.
- Keep real letters, OCR text, personal identifiers, credentials, tokens and private storage object IDs out of Git.

## Verification boundary

This audit records read-only production inspection and disposable backup-restore rehearsals. It does not claim authenticated browser login, document-view/download E2E, full original-byte checksum validation, migration application or Supabase retirement. No production data was changed during these checks.

## Post-snapshot delta reconciliation — 2026-11-08

The three letters created after the 2026-11-07 off-site snapshot were inspected read-only. All three have the expected archive ID and owner ID, use Google Drive storage, have a non-empty object reference and stored original SHA-256. Their three source records and three completed processing jobs reference the corresponding letter IDs. Four post-snapshot jobs were identified in total; one is a completed job for an older letter. Two post-snapshot relationships also reference existing archive letters. No orphan relationship/source/job was observed in this focused linkage check.

Most importantly, the original bytes for all three post-snapshot letters were downloaded read-only from private Drive and SHA-256 compared against each database `original_sha256`. **All three matched.** The exact document content, names and Drive object IDs are intentionally excluded from Git.

This validates the post-snapshot originals and their stored hashes; it does not yet certify every older original byte-for-byte or complete authenticated browser/API view/download flows.

## Full original-byte integrity verification — 2026-11-08

A complete read-only integrity pass downloaded all 144 original files referenced by the live database (approximately 359,781,661 bytes total) from the configured private Drive archive and computed SHA-256 for each file. Each digest was compared with its corresponding `letters.original_sha256` value.

**Result: 144/144 SHA-256 matches; zero download errors; zero mismatches.** This confirms the original-file bytes currently in Drive match the hashes recorded in the live PostgreSQL catalogue. No originals were modified, renamed or deleted.

## Regression suite checkpoint — 2026-11-08

After the recovery/source-of-truth changes, the full DLR test suite was rerun on the Oracle working tree with the repository root on `PYTHONPATH`: **453 passed, 9 subtests passed, one Starlette/httpx deprecation warning**, in 44.61 seconds. No test failures. The deprecation warning is non-blocking and should be addressed in a separate dependency-maintenance change.


## Authentication and backup-scheduler checkpoint — 2026-11-08

The running API was checked read-only after the regression run:

- `GET /api/v1/health`: HTTP 200, `{"status":"ok"}`.
- `GET /app`: HTTP 200; the served application contains the password sign-in form and archive search UI.
- `GET /api/v1/auth/providers`: password sign-in enabled, Google sign-in disabled, magic link disabled, registration is invite-only.
- Without an authenticated session, `GET /api/v1/auth/session`, `GET /api/v1/readiness`, and `GET /api/v1/search` correctly return HTTP 401. This is expected access control, not proof of a successful user login.
- Authenticated browser sign-in, search, original view and download remain unverified. The connected browser context was unavailable for this run, and no credentials or synthetic session were used. A real authorized user session is still required to complete this gate.

The user-level systemd timers `dlr-postgres-backup.timer` and `dlr-postgres-offsite-backup.timer` are both enabled and active (waiting). Their next scheduled runs were reported for 2026-11-08 02:31:54 UTC and 03:02:40 UTC respectively. The prior local and off-site snapshots have already passed disposable restore verification. Timer activation confirms scheduling only; the next backup execution and its resulting artifact still need post-run verification.

The full test suite was rerun on 2026-11-08: **453 passed, 9 subtests passed, one non-blocking Starlette/httpx deprecation warning, 47.48 seconds**. No production migration, database mutation, restore, deployment or secret access was performed during this checkpoint.
