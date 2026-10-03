# Tests

Passed 2026-10-03:

- Target group text-only event: skipped without agent dispatch.
- Non-target WhatsApp group event: ignored by DLR hook.
- Supported target-group PDF event: staged into protected queue.
- Plugin doctor: runtime discovery/import/registration passed.
- Consumer timer and DLR worker timer active.
- Synthetic staged attachment entered canonical DLR intake.
- A live partial-ingest failure exposed PostgREST incompatibility with a partial unique index; provenance persistence was changed to select-before-insert idempotency.
- Retry of the same staged attachment repaired the existing letter by linking WhatsApp provenance without a duplicate Drive upload.
- Verified provenance: channel=whatsapp, source label=EDU- Letters, external message id preserved.
- Synthetic Drive file and database row were deleted after verification.
- Final archive count returned to the two real pilot letters and zero synthetic WhatsApp provenance rows.
- Full DLR suite: 280/280.


## Live synthetic verification — 2026-10-03

Passed:
- configured source group exists and is already allowed by the live Hermes group policy;
- bridge/group test PDF delivery succeeded;
- protected pending-inbox staging format accepted;
- WhatsApp provenance persisted with source channel and message ID;
- DLR processing job completed through the dedicated worker;
- authenticated search found the synthetic record;
- authenticated original streaming succeeded;
- replaying the same WhatsApp message ID returned duplicate-message and created no duplicate;
- synthetic Drive/database artifact cleanup returned zero residual rows;
- connector timer remains active;
- private invite fallback to one allowlisted-but-missing group member succeeded.

Not yet claimed:
- a genuine inbound attachment posted by another group member has not yet been observed after the final live bridge hook.


## Live E2E — 2026-10-03

- Source group binding present and live metadata name matched `EDU- Letters`.
- Gateway active; DLR WhatsApp intake timer active; bridge staging hook present.
- Fresh unique synthetic PDF sent into the group via the live bridge.
- Automatic connector intake created a DLR record with WhatsApp provenance and message-id dedup key.
- Worker completed processing.
- Authenticated search returned the record.
- Authenticated original stream returned the archived bytes.
- Synthetic Drive object deleted after verification.
- Synthetic letter/job/processing/source rows cleaned to zero.
- Group currently reports three participants. Allowlist also has three configured entries, but identity-alias differences mean this count is not treated as proof that every allowlisted identity is already a participant.


## Genuine official circular proof

Passed 2026-10-03: public official CBSE PDF sent into the bound group, ingested with WhatsApp provenance, processed by the dedicated worker, reprocessed after fixing CBSE authority precedence, found by authenticated search, and streamed from private original storage. Corrected metadata includes CBSE authority, affiliation category, explicit notification reference/date and smart filename. Full suite: 281/281.
