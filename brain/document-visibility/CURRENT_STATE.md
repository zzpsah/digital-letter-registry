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

## Portal all-documents visibility fix — 2026-10-06

Home now renders up to 100 archive documents latest-first instead of only the latest 6. This prevents older Public documents from appearing to disappear as new files are uploaded. Search and Personal remain separate views.

## Compact privacy control + pagination — 2026-10-06

- Public/Private dropdown was removed from document cards.
- A lock icon beside the Important star now toggles Public ↔ Private directly: 🔓 Public, 🔒 Private.
- Personal remains a separate action/workspace.
- Home archive uses server-side pagination, 20 documents per page, with Previous/Next controls.
- Pagination uses an offset-aware Supabase RPC, so the archive is not capped at 100 documents.

## Year-wise Archive — 2026-10-06

- Archive is separate from Public/Private/Personal visibility and Trash.
- Editor/Admin can move a document to Archive and choose an archive year.
- Archived documents are excluded from Home, normal Search, and Personal workspace.
- Archive has its own top-level tab, year filter, search, 20-item pagination, and year-grouped cards.
- Restore returns the document to the main archive without changing its visibility.
- Archived documents are excluded from the generated public Drive index.

## Page-size selector + Important workspace — 2026-10-06

- Home, Important, and Archive pagination default to 50 documents per page.
- Users can choose 20 / 50 / 100 per page from the pager controls.
- The top-level Personal navigation button was replaced by `★ Important`. Personal documents remain available through the Search visibility filter and card Personal action.
- Important uses server-side pagination with `important_only=true`, so starred documents scale beyond one page.

## Dedicated archive upload workflow — 2026-10-06

- Normal document cards no longer show an Archive action.
- Archive is managed from the dedicated Archive tab.
- Archive tab accepts an archive year plus multiple PDF/Image files and uploads them directly into that year.
- Those uploads are immediately marked archived, so they do not enter normal Home/Search/Personal lists.
- Archived cards expose Restore; Restore sends the document back to the main archive without changing visibility.

## Large page-size selector — 2026-10-06

- Home, Important, and Archive default to 50 documents per page.
- User-selectable page sizes: 50 / 100 / 200 / 500.
- Backend API and search RPC accept up to 500 rows per page.
- Pagination remains unlimited across pages.

## Personal tab + persistent pagination — 2026-10-06

- Personal remains a top-level tab alongside Important and Archive.
- Home/Important/Archive remember the current page and selected page size in local browser storage.
- Refreshing or switching tabs returns to the same page where possible, so later-page documents do not appear to disappear.

## Cold archive bulk manager — 2026-10-06

- Archive means moving low-use older documents out of the main Home/Search/Personal views, not uploading a second copy.
- Archive tab loads existing active documents by source year and optional source month.
- Users can select individual files or Select all matching files, then bulk archive them.
- When a month is chosen, selected files are archived under that year/month. When All months is chosen, each file is grouped under its own issue/upload month.
- Archived documents are browsed year/month-wise and can be restored.

## Unified privacy icon — 2026-10-06

- Removed the separate Personal action button from document cards.
- A single privacy icon beside the star cycles Public → Private → Personal → Public.
- Icons: 🔓 Public, 🔒 Private, 👤 Personal.
- Personal remains a top-level tab for browsing Personal documents.

## Reprocess enqueue RLS fix — 2026-10-06

Manual reprocess jobs now use the requesting editor/admin as `processing_jobs.owner_id`. This matches the RLS rule `owner_id = auth.uid()` and allows editors/admins to reprocess documents originally uploaded by another user.

## Reprocess live progress — 2026-10-06

Reprocess jobs persist `progress_stage`, `progress_percent`, and `progress_detail`. The worker updates major stages from queue/start through text/OCR, AI analysis, metadata save, indexing, relationship checks, and completion/failure. The portal polls the job every 2 seconds and shows a live percentage/progress bar on the document card until terminal state. Job IDs are stored locally so progress resumes after a page refresh.

## Reprocess derived-owner RLS fix — 2026-10-06

Manual reprocess now separates queue ownership from document-derived-data ownership. `processing_jobs.owner_id` remains the requesting editor/admin to satisfy queue RLS, while `letter_processing`, embeddings, and relationship writes use the original letter owner so derived-table RLS remains valid.
