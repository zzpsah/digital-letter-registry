# PostgreSQL Primary Integration — Project

Updated: 2026-10-16

## Goal
Keep the Digital Letter Registry (DLR/eLetters) application aligned with the Oracle-hosted PostgreSQL primary while preserving the Supabase-compatible API contracts, immutable Google Drive originals, and independent recovery options.

## Scope
- Document the database/app dependency boundary and current production topology.
- Record PostgreSQL primary, Auth/Data API bridge, migrations, backups, Ansible and pending DR replication.
- Record the DLR queue/RLS correction and direct Gemini processing checkpoint.
- Track validation gaps without representing a completed job as proof of correct document intelligence.

## Ownership
- Database schema, SQL migrations, backup/restore, database operations and DR design: `zzpsah/postgresql-services`, under `projects/official-letter-intelligence/database-operations/`.
- API, worker, processing rules, frontend and tests: `zzpsah/digital-letter-registry`.
- Host, Docker, systemd, networking and Ansible runtime: Oracle VPS operations repository.
- Private originals: Google Drive; secrets: Bitwarden Secrets Manager.

## Out of scope
No UI redesign, no bulk reprocessing, no embedding backfill, no security-policy weakening, no second writable primary, and no production data export to Git.

## Acceptance
Current state and dependencies are documented in both canonical repositories; verification claims match observed runtime/tests; unresolved failures remain visible; no unrelated working-tree changes are discarded.
