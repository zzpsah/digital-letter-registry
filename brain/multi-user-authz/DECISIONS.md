# Multi-user authorization — Decisions

1. Gmail is not required.
2. Google Sign-In is optional convenience, not the authorization model.
3. Native email/password login is supported.
4. Registration is invite-only; no open archive membership.
5. A dedicated DLR admin is a normal Supabase Auth user with an active `admin` archive membership.
6. Never use Supabase service-role as a human admin login.
7. Use stable Supabase user ids + archive membership for authorization.
8. Preserve the bootstrap owner as the initial admin.
9. Database/RLS enforcement is mandatory; frontend role hiding is only UX.
10. The database must retain at least one active admin.
11. Invite codes travel in URL fragments, not query strings, and are removed from the browser URL after prefill.
12. Real archive mutation approval boundaries remain separate from account role.
