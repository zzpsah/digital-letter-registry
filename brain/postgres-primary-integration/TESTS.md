# Verification Evidence

Observed on Oracle VPS, 2026-10-16.

## Passed
- Full DLR suite: **377 tests passed, 0 failures** (`.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`).
- Focused queue, repository, self-healing, processing pipeline, quality assessment and Gemini tests passed, including explicit tests for archive scoping, low-confidence overwrite protection, and source-conflict warnings.
- Python `compileall` and `git diff --check` passed.
- Direct Gemini synthetic text analysis and synthetic-file analysis passed using `gemini-3.5-flash-lite`; no real document was sent in this provider smoke test.
- Ansible syntax check and live validation playbook passed with no deployment/restart changes.
- Fresh local encrypted backup restore: `dlr_restore_test`, 19 public tables and 28 public functions; disposable database removed afterward.
- Fresh off-site backup: remote SHA-256 verification and decryption passed; disposable restore reported 19 public tables and 28 public functions; temporary database removed.
- Live authenticated worker login, search, letter detail and original-file retrieval passed. Detail response did not expose private storage identifiers. Unauthenticated search/original access returned HTTP 401.
- Live queue integrity: 0 active jobs, 0 missing archive IDs, 0 orphan jobs, 0 archive mismatches, and 0 duplicate letter/reason pairs.
- Live service health: FastAPI, GoTrue and PostgREST returned HTTP 200.

## Remaining caveats
- The code changes are not yet deployed; production smoke checks above exercise the currently running deployment, while the 377 tests exercise the current working tree.
- One real record is low-confidence (0.45), explicitly source-conflict marked and still needs human review; a second record remains flagged for reprocessing. No additional real documents were queued.
- Four historical jobs remain failed: two prior RLS/archive-scope failures and two network/timeout failures. No active jobs remain; no bulk retry was performed.
- Embeddings remain disabled and no vector backfill was performed.
- Hosted Supabase is not a verified replica; schema drift, OAuth/magic-link delivery, and DR failover/failback remain separate gates.
- Existing non-failing Starlette/httpx deprecation and test-file ResourceWarnings remain cleanup items.

## Test safety
Use synthetic documents for repeatable regression. Do not log real document content, do not queue additional real records automatically, and verify notification side effects before any production worker run that processes a new job.
