# Verification Evidence

Observed 2026-10-16.

## Passed
- Gemini direct-provider synthetic text analysis and synthetic original-file analysis previously passed using the configured model.
- Focused DLR tests `tests.test_jobs` and `tests.test_gemini_provider`: 7 passed after the archive_id enqueue correction.
- Controlled production worker job reached `completed`, stage `complete`, 100%, and stored context version `gemini:gemini-3.5-flash-lite:context-v3`.
- Live catalog counts: 19 public tables, 28 public functions, 18 RLS-enabled public tables.
- Local and off-site backup timers reported active.

## Failed / incomplete
- Full DLR unit suite: 374 tests ran; 2 failures in `test_self_healing.py`:
  - `test_lower_tier_low_quality_gets_daily_recovery_job` expected old date suffix but observed changed reason behavior.
  - `test_same_preferred_version_does_not_loop` expected no enqueue but observed one.
- Current working tree changed `QUALITY_VERSION` from `document-quality-v2` to `document-quality-v3`; tests and behavior need reconciliation before release.
- The one real job had confidence 0.45 and `needs_reprocessing=true`; semantic correctness is not verified.
- Embedding version remained `unprocessed`; semantic/vector search remains disabled by design.
- Supabase Gemini gateway remains HTTP 402 quota-blocked; direct Gemini is preferred when the Bitwarden key is injected.
- Hosted Supabase is not a verified database replica; replication/failover drills are incomplete.

## Test safety
Use synthetic documents for repeatable regression. For real records, inspect metadata without logging document contents, do not queue more records automatically, and check notification side effects.
