# Runtime Verification — Tests

Passed:
- DB-level owner insert with simulated authenticated JWT subject.
- DB-level owner read.
- DB-level wrong-user read returned zero visible rows.
- DB-level cross-owner insert rejected by RLS.

Not yet passed:
- Real browser/PostgREST short-lived bearer-session vertical slice.
- Drive OAuth/original streaming runtime test.
- Gemini runtime synthetic test.

Data note: one synthetic verification row remains; no real archive-letter row exists.
