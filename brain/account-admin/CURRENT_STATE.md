# DLR Account Administration — Current State

Work started 2026-10-02.

Observed before this enhancement:
- live hosted Supabase contains one archive row;
- the existing UMV account is an active admin member;
- archive role migrations are already applied live;
- admin/editor/viewer RLS enforcement is present;
- password login and optional Google/Magic Link authentication paths exist;
- full synthetic suite passes 233/233;
- no real archive letters exist.

Missing:
- admin-facing member list;
- invite/pre-authorization workflow;
- role/status management;
- invited user registration/activation path.
