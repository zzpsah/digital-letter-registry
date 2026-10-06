# Decisions

1. Public is the backward-compatible default.
2. Private means authenticated archive members only; never public index/share.
3. Personal means marker user + admins, while original ingest owner retains access so background processing still works.
4. Privacy is enforced in RLS and runtime publication, not only hidden in UI.
5. Existing documents are not silently reclassified.
