# Project Brain — Tasks

## Completed

- [x] Establish repository and DevOS foundation.
- [x] Design and implement the private runtime boundary in code.
- [x] Build synthetic-first archive/intake/search/runtime foundations.
- [x] Verify owner-scoped RLS structure.
- [x] Verify DB-level synthetic owner insert/read and wrong-user isolation with simulated JWT request claims.
- [x] Verify local Hindi/English OCR runtime.

## Next

- [ ] Complete real short-lived authenticated HTTP/PostgREST owner-session synthetic vertical slice.
- [ ] Configure/verify refreshable Google Drive OAuth credentials with synthetic data only.
- [ ] Verify private original streaming end-to-end.
- [ ] Configure/verify Gemini runtime credentials with synthetic data only.
- [ ] Configure hosted Supabase magic-link template/Site URL.
- [ ] Remove retained synthetic RLS verification row through an authorized cleanup path.
- [ ] Re-run readiness and synchronize README/docs/.ai/brain after each meaningful checkpoint.
- [ ] Decide whether to enable vector/semantic search: provide an embedding-capable credential and backfill
      approximately 729 chunks. Keyword search already covers full extracted text, so this is an enhancement,
      not a defect. Left as-is at the user's direction on 2026-10-09.
- [ ] Regenerate and re-store `DLR_GMAIL_APP_PASSWORD` if the sender account's Google password is ever changed.

## Done — 2026-10-09

- [x] Restore DLR document delivery after the 7-day OAuth refresh-token expiry (publish OAuth app to production,
      re-consent the archive-owner Drive token, rotate it into the secret manager).
- [x] Move Gmail outbox delivery to a non-expiring app password over SMTP with an OAuth fallback.
- [x] Reprocess the three intake documents that were stuck behind the expired credential.

## Deferred by safety boundary

- [ ] Real letter ingestion.
- [ ] Historical live import.
- [ ] Real Drive rename.
- [ ] Live messaging/email connector activation.
- [ ] Production deployment.
