# Architecture and Dependency Map

## Runtime path
```text
Vercel DLR web control plane
  └─ Supabase-compatible Auth/REST/RPC paths
      └─ Oracle HTTPS compatibility bridge (FastAPI)
          ├─ local GoTrue Auth
          ├─ local PostgREST
          └─ PostgreSQL 16 + pgvector: dlr_primary
               ├─ letters / letter_processing
               ├─ durable processing_jobs
               └─ RLS, grants, RPCs and archive membership

Private Oracle worker
  ├─ claims a durable processing_jobs row
  ├─ fetches immutable original from private Google Drive
  ├─ extracts text / Hindi-English OCR
  ├─ direct Gemini structured analysis (Bitwarden-injected key)
  └─ persists derived context; embeddings remain disabled

Recovery
  ├─ encrypted local backup
  ├─ encrypted private Google Drive off-site backup
  └─ hosted Supabase: intended DR target, not yet verified replica
```

## Source-of-truth boundaries
- Original document bytes and Drive object identity are authoritative.
- PostgreSQL stores identity, queue state, derived extraction/context, and searchable metadata.
- Gemini output is derived and must remain evidence-grounded; a successful API call or completed job does not certify semantic quality.
- Database schema and backup scripts are versioned in PostgreSQL Services; application persistence/queue contracts are versioned in DLR.
- Secrets and real document content never enter either Git repository.

## Dependency order for changes
1. Define or inspect the schema contract and live migration state in PostgreSQL Services.
2. Make/test a reviewed migration there when a database contract changes; never use staging-only migration helpers on production.
3. Update DLR transport/repository/queue code and tests to match the database contract.
4. Run unit tests, RLS/role checks, and authenticated API/worker smoke tests.
5. Take/verify backup before production schema or runtime changes.
6. Deploy through the documented Ansible workflow only after source changes are reviewed and committed.
7. Verify application behavior and backup freshness; document remaining hosted Edge Function dependencies.
8. Enable one-way DR sync only after schema/Auth compatibility, lag monitoring, and restore/failover tests exist.

## Non-goals
No public PostgreSQL listener, no dual-writer mode, no broad reprocessing by default, no embedding backfill, and no UI redesign.
