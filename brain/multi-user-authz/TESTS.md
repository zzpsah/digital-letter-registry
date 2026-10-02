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
