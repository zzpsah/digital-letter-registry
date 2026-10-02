# Runtime Verification — Tests

Passed:
- DB-level owner insert with simulated authenticated JWT subject.
- DB-level owner read.
- DB-level wrong-user read returned zero visible rows.
- DB-level cross-owner insert rejected by RLS.
- VPS focused auth/session/API suite: 35/35 tests passed on 2026-10-02.
- VPS full synthetic unit suite: 205/205 tests passed on 2026-10-02.
- Supabase Management Auth-config helper focused suite: 4/4 tests passed on 2026-10-02.
- Repository magic-link template artifact uses the server callback pattern: `/auth/confirm?token_hash={{ .TokenHash }}&type=email`.

Not yet passed:
- Real browser/PostgREST short-lived bearer-session vertical slice.
- Hosted Supabase magic-link template/Site URL application in the live project.
- Drive OAuth/original streaming runtime test.
- Gemini runtime synthetic test.

Data note: one synthetic verification row remains; no real archive-letter row exists.

## OCR readiness override verification

Passed:
- Focused runtime-readiness unit suite: 5/5.
- The configured-command test confirms explicit OCR paths are resolved without exposing them in readiness output.
