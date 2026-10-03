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
