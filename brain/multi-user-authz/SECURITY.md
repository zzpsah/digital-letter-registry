# Multi-user authorization — Security

- Authorization must be based on stable Supabase user id + active archive membership.
- Do not authorize from `user_metadata`, email domain, or authentication provider.
- Role checks must be enforced server-side/database-side.
- Open signup must not imply archive membership.
- Keep service-role/secret credentials out of user sessions.
- Existing real-document mutation approval gates remain separate from user role.
