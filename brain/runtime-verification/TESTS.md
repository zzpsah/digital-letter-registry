# Runtime Verification — Tests

Passed:
- DB-level owner insert with simulated authenticated JWT subject.
- DB-level owner read.
- DB-level wrong-user read returned zero visible rows.
- DB-level cross-owner insert rejected by RLS.
- VPS auth/API suite: 29/29 tests passed on 2026-10-02 after adding default hosted Magic Link fragment compatibility and safe rate-limit handling.
- VPS full synthetic unit suite: 212/212 tests passed on 2026-10-02 after file-based Drive OAuth support.
- Dedicated tailnet-only HTTPS health check passed from an authorized tailnet client.
- Supabase Site URL/redirect configuration was moved off the unrelated localhost origin to the dedicated private DLR origin.
- Supabase Management Auth-config helper focused suite: 4/4 tests passed on 2026-10-02.
- Repository custom magic-link template artifact uses the server callback pattern: `/auth/confirm?token_hash={{ .TokenHash }}&type=email`.
- Default Supabase hosted Magic Link callback bridge is covered: callback page serves no-store/no-referrer/CSP headers, validates owner identity server-side, sets HttpOnly cookies, and clears fragment tokens.

Passed additionally:
- File-based authorized-user Drive OAuth provider unit coverage.
- Live Google OAuth refresh exchange using the dedicated DLR desktop client.
- Live originals folder listing returned exactly one synthetic integration file.
- Live `GoogleDrivePrivateTransport` stream/download of the synthetic original succeeded (24,668 bytes).
- Runtime readiness reports Drive credentials configured without exposing secret values.

Not yet passed:
- Real browser/PostgREST short-lived bearer-session vertical slice after Supabase email-send throttling allows a fresh one-time link.
- Optional custom-SMTP/token-hash template application in the live project.
- Runtime Drive write/upload verification passed with a disposable synthetic object; stream/content verification and cleanup also passed.
- Gemini runtime synthetic test.

Data note: the retained synthetic verification row was removed; `letters` now contains zero rows.

## OCR readiness override verification

Passed:
- Focused runtime-readiness unit suite: 5/5.
- The configured-command test confirms explicit OCR paths are resolved without exposing them in readiness output.


Passed on 2026-10-03:
- Live synthetic worker vertical slice: Drive upload → durable queue → Oracle worker → OCR/context persistence → text search → private original stream.
- Private original byte content matched the uploaded synthetic source.
- Initial live run exposed and then verified the fix for partial-letter UPSERT failure; context writes now PATCH the existing letter row.
- Focused PostgREST/repository tests: 15/15.
- Full Oracle synthetic suite after the fix: 269/269.
- Cleanup verified: zero synthetic letters, jobs, and processing rows remain; disposable Drive object removed.


## Actual-session multi-role RLS verification — 2026-10-03

Using the dedicated worker's genuine short-lived Supabase Auth session, archive membership was temporarily exercised through all three live roles while the worker timer was paused:
- viewer: SELECT allowed; INSERT denied;
- editor: INSERT and UPDATE allowed; DELETE affected zero rows and the row remained present;
- admin: DELETE returned the target row and removed it.

The worker membership was restored to `editor / active`, the timer was restarted and verified active, and live archive counts returned to zero letters/jobs. Note: PostgREST may return an HTTP-success response with an empty representation when RLS filters out a DELETE; tests must inspect affected rows rather than status code alone.


## PostgREST delete regression hardening — 2026-10-03

- Added a filtered DELETE helper to the authenticated runtime transport with archive scoping preserved.
- DELETE always requests `return=representation`; callers can distinguish an actually deleted row from an RLS-filtered no-op even when HTTP status is successful.
- Empty DELETE representation is explicitly covered as zero affected rows.
- DELETE without filters fails closed.
- Focused runtime transport suite passes 13/13; full Oracle DLR suite passes 269/269.
