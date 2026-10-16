# Document quality review

The quality-review queue is available to archive administrators in **Admin → Operations → Quality review**. It is deliberately separate from the failed-job retry queue: a document can finish processing and still need a person to verify its extracted metadata.

## Review a document

1. Sign in to eLetters with an administrator account.
2. Open **Admin → Operations → Quality review** and select **Refresh**.
3. Select **View original** (or **Download**) to inspect the source document. Compare the source against the displayed title, issuing authority, category, reference number, issue date, and summary. Pay special attention to the reason shown, such as a possible heading/body conflict or uncertain reference/date extraction.
4. If the extracted metadata is correct, choose **Confirm reviewed** and confirm the prompt. The server records `reviewed_at`, changes `needs_reprocessing` to `false`, adds a `human_review.status=accepted_as_is` marker, and attempts to write an admin audit event. The metadata is then protected from automatic low-confidence overwrites.
5. If the metadata is wrong or the source conflict remains unresolved, **do not confirm it**. Choose **Reprocess**, wait for processing to finish, refresh the queue, and inspect the new result. If reprocessing still cannot resolve the discrepancy, leave the item flagged; manual field editing is not yet provided by this queue.

## What the queue does and does not do

- The list is server-side admin-only and is limited to records with `needs_reprocessing=true` and no `reviewed_at` timestamp.
- It skips trashed documents and returns only the fields needed to review them; it does not return extracted full text, storage object IDs, access tokens, or private storage paths.
- **Confirm reviewed** is an explicit human action. Nothing is automatically accepted, reprocessed, deleted, or retired by opening the queue.
- **Reprocess** uses the existing per-document reprocessing endpoint and confirmation prompt. It is a real write/processing action, so use it only after checking the original.
- The n8n queue/review watch remains a read-only aggregate monitor. It can alert on counts, but it does not make review decisions or modify DLR records.
- `source_conflict_count` is a quality-flag count, not necessarily the number of unresolved queue entries; a source-conflict flag is preserved as provenance even after a human accepts the current metadata.

## Access and audit

The API endpoints are `GET /api/v1/admin/review-queue` and `POST /api/v1/admin/review-queue/{letter_id}/accept`. Both require the archive administrator role; the mutation also uses the existing same-origin protection for cookie-authenticated requests. Accepted decisions update the existing `letter_processing.reviewed_at` field and `structured_context`; no schema migration is required. The app attempts to record `document_quality_review_accepted` in the existing admin audit log.

The queue is a focused first step, not a general metadata editor. If a person cannot resolve a conflict by reviewing/reprocessing, leave it flagged for a later, explicitly scoped manual-correction feature.
