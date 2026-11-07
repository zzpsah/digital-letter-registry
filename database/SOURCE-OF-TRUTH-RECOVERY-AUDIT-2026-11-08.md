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
