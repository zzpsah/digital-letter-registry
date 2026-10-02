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
- Persistence ports, Supabase row mapping, injected-transport repository adapter, synthetic ingestion preparation, storage ports, and a Drive adapter contract are implemented.
- GitHub CI is configured for synthetic unit tests.

## Current gaps

- Supabase Auth currently has no archive owner user, so normal RLS-backed inserts are not ready.
- No live Google Drive transport or authenticated Supabase transport is wired yet.
- No OCR, AI context extraction, embeddings pipeline, search UI, or live ingestion exists.
- No rename executor is authorized.

## Next action

Create/establish the archive owner authentication identity, then wire the private Drive upload adapter and authenticated Supabase transport with synthetic fixtures only.

## Safety

Do not commit real letters, Drive IDs/URLs, Supabase keys, credentials, SSH keys, or server details to this public repository. Existing Drive files must not be renamed without an approved preview mapping.
