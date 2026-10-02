# Multi-user authorization — Tests

## Synthetic/unit
- Archive membership role parsing and permission checks.
- Admin invite/list/update/revoke service behavior.
- Email/password sign-in.
- Invite validation and invite-only password signup.
- Magic-Link invite signup metadata path.
- Admin-only access APIs.
- Viewer write denial at application authorization boundary.
- Provider contract exposes password login and invite-only registration.
- Invite registration path uses URL fragment.
- Full test suite: 249/249 passed.

## Hosted verification
- Membership migrations present in Supabase migration history.
- Archive/member/invite tables have RLS enabled.
- Current membership contains one active admin.
- No disabled members or pending invites.
- No real archive-letter rows.
- Last-active-admin disable attempt was rejected; post-test state remained one active admin and zero disabled members.

## Pending
- Real browser/session editor and viewer vertical-slice verification.


## Hosted RLS matrix verification — 2026-10-02

Transaction-safe synthetic claim tests on hosted Supabase verified:
- viewer can read archive letters;
- viewer update affects zero rows;
- editor can insert;
- editor can update;
- editor delete affects zero rows;
- non-member reads zero archive rows;
- non-member insert is denied;
- admin delete succeeds.

The first harness incorrectly treated zero-row UPDATE/DELETE denials as failures; the corrected harness measured affected rows. A separate admin check captured the admin identity before role switching and confirmed delete success.

Post-test cleanup verified:
- zero synthetic test Auth users;
- zero synthetic test letters;
- zero synthetic test memberships;
- zero pending invites.


## Password flow verification

- Supabase authenticated-user password update helper covered by unit tests.
- Passwords shorter than the DLR minimum are rejected.
- Member-only API endpoint covered.
- Signed-in Account UI covered.
- Live private runtime confirms Account form is present.
- Live unauthenticated password-change call returns HTTP 401.
- Full suite: 255/255.
