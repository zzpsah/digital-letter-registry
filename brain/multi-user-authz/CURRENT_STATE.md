# Multi-user authorization — Current State

Work started 2026-10-02.

Observed starting point:
- Current public tables are owner-scoped with `auth.uid() = owner_id` RLS.
- Runtime has a configured `SUPABASE_OWNER_ID` and fragment-session bridge rejects any different user id.
- Existing archive owner must be preserved during migration.
- Real archive tables are currently empty of real letters.

Implementation and verification pending.
