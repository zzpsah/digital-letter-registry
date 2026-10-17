# Tasks

- [x] Establish connector architecture and safety boundary.
- [x] Inspect live Hermes inbound/media hook contract.
- [x] Implement private connector bridge without credentials in Git.
- [x] Add configurable source-group allow rule.
- [x] Add connector-specific real-intake guard/cap (bounded runtime cap; currently 100,000, hard maximum 1,000,000).
- [x] Add message-id dedup/provenance verification.
- [x] Synthetic live verification through existing WhatsApp runtime.
- [x] Enable real group intake after synthetic verification passed.

- [ ] Verify the first real attachment posted by an allowed member in `EDU- Letters` is archived and processed automatically.

- [ ] Observe the first real inbound PDF/image posted by a group member and confirm automatic staging without manual intervention.

- [x] Fresh bridge-originated synthetic PDF E2E: WhatsApp send → stage → intake → worker → search → original stream → cleanup.
- [ ] Observe first genuine member-posted document after final verification.

- [x] Add configurable WhatsApp-only size limit up to 2 GiB without changing normal web uploads.
- [x] Verify staged message outcome before the event dispatcher marks it completed; retain failed receipts separately.
- [ ] Reprocess 18 quarantined staged attachments and verify every resulting processing job reaches completed or a clearly reported review/failure state.
- [ ] User must resend any attachments rejected before staging from an unapproved WhatsApp sender/chat via the configured approved group or explicitly authorize that sender after identity verification.
