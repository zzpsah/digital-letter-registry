# Project Brain — Tests

## Verified evidence

- Synthetic application/unit suite is implemented and has passed in prior recorded runtime checkpoints.
- Localhost FastAPI smoke test previously verified health/PWA 200 and unauthenticated session/search 401 boundaries.
- Hindi/English OCR synthetic PNG and image-only PDF smoke tests passed on the Oracle ARM64 runtime.
- Anonymous Supabase Data API read is RLS-scoped and anonymous insert is rejected.
- 2026-10-02 DB-level RLS verification:
  - owner-context synthetic insert: passed;
  - owner-context synthetic read: passed;
  - wrong-user read of that row: zero visible rows;
  - cross-owner insert: rejected by row-level security.

## Important limitation

The 2026-10-02 RLS verification used simulated database request JWT claims. It does **not** complete the pending real browser/PostgREST short-lived bearer-session vertical slice.

## Data status

One synthetic RLS verification row remains in the archive database because the connected destructive cleanup action was blocked. No real archive-letter record was created.
