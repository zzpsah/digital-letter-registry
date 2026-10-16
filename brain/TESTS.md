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

- Full DLR suite: **377 tests passed, 0 failures** after making the self-healing test target quality versions explicit and adding low-confidence/source-conflict merge coverage.
- Python compile check and `git diff --check` passed.
- Live authenticated worker login, search, detail and original-file retrieval passed; detail response omitted private storage references. Unauthenticated search/original access returned HTTP 401.
- Fresh local and off-site encrypted backups were created and restored to disposable databases; each restore reported 19 public tables and 28 public functions. Ansible syntax and validation passed without deployment/restart.
- Direct Gemini synthetic text and synthetic-file analysis passed with `gemini-3.5-flash-lite`.
- Live queue integrity passed: no active jobs, missing `archive_id`, orphaned jobs, archive mismatches or duplicate letter/reason pairs.
- One low-confidence source-conflict record and a second record remain flagged for review. Four historical jobs remain failed (two prior RLS/archive-scope failures, two network/timeouts); no bulk retry was performed.
- The reviewed implementation is deployed as Oracle revision `b16c899` (implementation commit `aa2c54d`); Ansible regression and post-deploy smoke checks passed. Remaining caveats are listed in `brain/postgres-primary-integration/TESTS.md` and `TASKS.md`.
