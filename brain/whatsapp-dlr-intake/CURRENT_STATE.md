# Current State

Observed 2026-10-03:
- Existing Oracle Hermes WhatsApp bridge/session is reused; no second WhatsApp login was created.
- One configured private source group is allowlisted and bound to DLR through a private runtime group-id file.
- Bridge stages only inbound PDF/JPG/JPEG/PNG attachments from that exact group into a protected local pending inbox.
- A 60-second systemd timer consumes pending attachments through the existing Bitwarden-backed DLR WhatsApp intake wrapper.
- Connector real intake is explicitly enabled with a bounded connector limit of 100 source messages.
- WhatsApp message ID is persisted as provenance and duplicate message IDs are ignored.
- Synthetic downstream E2E passed: staged attachment -> DLR queue -> dedicated worker -> search -> original stream -> duplicate-message guard.
- Synthetic Drive/database artifact was cleaned after verification.
- A live synthetic test PDF and success message were delivered to the configured WhatsApp group.
- One allowlisted WhatsApp member was not directly addable by the bridge; a private group invite fallback was sent successfully.
- Full DLR suite remains 280/280 from the latest code regression run.

Privacy boundary: no group IDs, phone numbers, session data, message bodies, Drive IDs or credential values are stored in public Git.

Remaining live observation: the next real attachment posted by another group member will be the first true inbound bridge-hook proof.
