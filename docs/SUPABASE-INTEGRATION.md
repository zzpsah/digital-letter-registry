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

## Current verification state

The archive-owner Supabase Auth identity exists and is confirmed.

DB-level synthetic RLS verification has passed using simulated request JWT claims:
- owner-context insert succeeds,
- owner-context read succeeds,
- a different synthetic user sees zero rows,
- cross-owner insert is denied by RLS.

This does **not** replace the pending real short-lived bearer-session/PostgREST test. One synthetic RLS verification row currently remains in `letters`; no real archive-letter row exists.

Before real ingestion:

1. Obtain a real authenticated owner session at runtime.
2. Run the guarded synthetic HTTP/PostgREST insert/read test with that session.
3. Verify the full synthetic intake → private Drive → queue/worker → search/open-original path.
4. Verify refreshable Drive OAuth/original streaming.
5. Verify Gemini only with synthetic content.
6. Clean up temporary synthetic verification rows through an authorized destructive path.
7. Only after the synthetic vertical slice is complete should real intake even be considered.

## Safety

Do not:

- commit Supabase URLs or credentials,
- insert real letters for testing,
- reuse the existing UMV database,
- use service-role access as a shortcut around the ownership model,
- claim production deployment before live verification.
