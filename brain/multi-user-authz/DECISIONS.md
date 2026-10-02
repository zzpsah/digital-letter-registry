# Multi-user authorization — Decisions

1. Do not make Gmail/Google a requirement.
2. Do not use Supabase service-role as an application admin identity.
3. Use stable Supabase user ids for membership.
4. Keep signup/invitation controlled; no open archive access.
5. Preserve the existing owner as the bootstrap admin.
6. Use database/RLS enforcement, not frontend-only role checks.
