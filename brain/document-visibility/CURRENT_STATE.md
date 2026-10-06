# Current State

Implemented 2026-10-06.

- `letters.visibility`: `public`, `private`, `personal`; existing rows default to `public`.
- Personal rows carry `personal_owner_id`.
- Admin can read/manage every document; Personal is otherwise visible only to its marker and original ingest owner; Private remains visible to authenticated archive members.
- Search/open/download inherit RLS visibility.
- UI exposes compact visibility selector on document cards for editor/admin.
- Public Drive index must only include Public documents.
- Oracle runtime revokes anonymous Drive sharing for non-public documents and suppresses/removes generated WhatsApp receipts for non-public documents.

## Personal collection UI

- Top navigation includes Personal.
- Personal page loads `/api/v1/search?visibility=personal` and therefore reuses authenticated/RLS-filtered search.
- Search advanced filters include Any/Public/Private/Personal visibility.
- Visibility changes refresh the Personal page so moving a document out of Personal removes it immediately.

## Personal workspace UI

- Top navigation includes `🔒 Personal`.
- Personal page shows only documents whose `personal_owner_id` matches the signed-in user, even for admins.
- Personal page has its own quick search box and refresh.
- General Search includes Visibility filter: Any / Public / Private / Personal.
- Personal cards show a `🔒 Personal` badge and can be changed back to Public/Private from the same card.
