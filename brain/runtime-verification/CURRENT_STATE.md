# Runtime Verification — Current State

Observed on 2026-10-02:
- Owner-scoped RLS policies are present on public archive tables.
- Synthetic DB-level owner insert/read passed.
- Wrong-user read returned zero rows.
- Cross-owner synthetic insert was rejected by RLS.
- Verification used simulated database request JWT claims, not a real PostgREST/browser bearer session.
- One synthetic verification row remains in the letters table.
- No real archive-letter row exists.

Pending: real short-lived owner-session HTTP/PostgREST test, Drive OAuth/original streaming verification, Gemini synthetic verification, hosted magic-link configuration, and synthetic-row cleanup when authorized tooling permits.
