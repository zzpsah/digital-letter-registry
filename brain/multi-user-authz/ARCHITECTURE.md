# Multi-user authorization — Architecture

Planned model:

```text
Supabase Auth user
  -> archive_members membership
  -> role: admin | editor | viewer
  -> RLS / application authorization
  -> archive data
```

Authentication provider and archive authorization remain separate.
