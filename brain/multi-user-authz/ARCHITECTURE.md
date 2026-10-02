# Multi-user authorization — Architecture

```text
Any supported identity provider
  ├─ Email + password
  ├─ Magic Link
  ├─ Google Sign-In (optional)
  └─ future provider
        ↓
Supabase Auth user id
        ↓
archive_members
  archive_id + user_id + role + status
        ↓
RLS + application authorization
        ↓
Official Letter Intelligence Archive
```

## Roles
- admin: membership/invite administration and privileged archive operations.
- editor: read/search plus content intake/update.
- viewer: read/search only.

## Important distinction
The legacy `owner_id` fields on letter/processing rows are retained as actor/audit provenance for the user that created the row. They are not the archive authorization boundary. `archive_id` + active membership is the authorization boundary.

## Authentication is not authorization
An authenticated Supabase account does not automatically receive archive access. Membership must be active. The login provider, email domain, and user-editable metadata do not define permissions.

Google Drive OAuth remains server-side storage authorization and is independent of DLR user login.
