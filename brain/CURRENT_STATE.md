# Project Brain — Current State

Last verified: 2026-10-02

## Working

- DevOS lifecycle is MANAGED.
- Public-safe repository scaffold and domain package exist.
- Private UMV Drive is selected for archive originals.
- Archive folder structure exists and is empty: `originals/`, `quarantine/`, `exports/`.
- Separate Supabase archive database exists with four core RLS-protected tables.
- Security advisor is clean.
- Unicode-safe official naming and preview-only rename mapping are implemented.

## Current gaps

- Supabase Auth currently has no archive owner user, so normal RLS-backed inserts are not ready.
- No private storage adapter or Supabase repository adapter is implemented yet.
- No OCR, AI context extraction, embeddings pipeline, search UI, or live ingestion exists.
- No rename executor is authorized.

## Next action

Create/establish the archive owner authentication identity, then implement and verify the storage/database repository adapter with synthetic fixtures only.

## Safety

Do not commit real letters, Drive IDs/URLs, Supabase keys, credentials, SSH keys, or server details to this public repository. Existing Drive files must not be renamed without an approved preview mapping.
