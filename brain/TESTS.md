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


## 2026-10-16 PostgreSQL/Gemini checkpoint

- Focused `tests.test_jobs` + `tests.test_gemini_provider`: 7 passed after queue enqueue began resolving the target letter's `archive_id`.
- Full suite: 374 tests, 2 failures in `test_self_healing.py`; see `brain/postgres-primary-integration/TESTS.md`.
- A controlled real reprocess completed, but its output remained confidence 0.45 with `needs_reprocessing=true`; do not treat completion as semantic correctness.
- Local PostgreSQL catalog: 19 public tables, 28 public functions, 18 RLS-enabled tables. Backup timers active at check time.
