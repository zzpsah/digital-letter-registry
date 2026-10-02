# Google Sign-In — Project

## Purpose
Make Google Sign-In the primary DLR user-authentication experience so the archive owner does not need to request an email Magic Link repeatedly.

## Scope
- Primary browser authentication: Google Sign-In through Supabase Auth.
- Fallback: passwordless email Magic Link remains available.
- Session: server-managed HttpOnly cookies with refresh rotation.
- Database authorization remains owner-scoped Supabase RLS.
- Google Drive OAuth remains a separate backend credential/permission system.

## Identity model
The existing archive owner already exists in Supabase Auth through the email provider. Supabase automatic identity linking is expected to link a verified Google identity using the same email address to that existing user, preserving the existing user id and RLS ownership.

Do not use user-editable metadata for authorization. RLS continues to rely on auth.uid() = owner_id.
