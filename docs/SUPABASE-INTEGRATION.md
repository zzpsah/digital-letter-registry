# Supabase Integration Boundary

## Purpose

The Digital Letter Registry uses a dedicated Supabase project separate from the existing UMV database.

The public repository stores only schema, adapter code, and synthetic tests. It does not contain a Supabase project reference, project URL, API key, user token, password, or real archive row.

## Current schema

The core public tables are:

- `letters`
- `letter_processing`
- `letter_relationships`
- `letter_chunks`

The public-safe schema baseline is stored under `supabase/migrations/`.

## RLS model

All archive tables use Row-Level Security.

The ownership rule is:

```text
auth.uid() = owner_id
```

This means normal application writes require an authenticated archive owner identity. The repository adapter must not bypass this with a service-role credential in ordinary user-facing flows.

## Repository architecture

```text
Domain objects
      ↓
public-safe row mapper
      ↓
SupabaseLetterRepository
      ↓
injected authenticated transport
      ↓
Supabase PostgREST / client
```

The adapter contains no hard-coded URL, key, token, project ID, or owner ID.

## UUID boundary

The provider-independent domain model permits opaque record IDs. The Supabase persistence boundary validates that both:

- document record ID
- owner ID

are valid UUIDs before a database transport is invoked.

## Duplicate protection

The database uniquely constrains:

```text
(owner_id, original_sha256)
```

The synthetic in-memory repository implements the same behavior for tests.

## Current blocker

The archive database currently has no authenticated archive owner account. Therefore live RLS-backed writes are intentionally not tested yet.

Before real ingestion:

1. Establish the archive owner through Supabase Auth.
2. Obtain an authenticated user session at runtime.
3. Provide the runtime Supabase transport through secret/config management.
4. Run a synthetic end-to-end insert.
5. Verify RLS permits the owner and denies another user.
6. Only then connect real Drive uploads.

## Safety

Do not:

- commit Supabase URLs or credentials,
- insert real letters for testing,
- reuse the existing UMV database,
- use service-role access as a shortcut around the ownership model,
- claim production deployment before live verification.
