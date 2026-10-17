# Decisions

- Reuse existing Hermes WhatsApp bridge/session.
- Accept only document/image attachments from an explicitly configured source label/chat identity.
- PDF/JPG/JPEG/PNG only; no arbitrary media.
- Preserve WhatsApp message ID as provenance for deduplication.
- Do not expose phone numbers/chat IDs/media paths in public Git.
- Keep real connector intake separately guarded from manual-pilot limit.
- Do not auto-delete or rename originals.

- Keep the cumulative WhatsApp intake cap bounded and explicit; increase it only for a user-authorized recovery window. Current configured cap: 150 source messages, hard maximum 500.
- Keep a separate WhatsApp-only upload-size cap (default 20 MiB; production recovery setting 100 MiB, hard maximum 100 MiB) so normal web uploads do not broaden.
- A webhook HTTP success is not proof of intake success; the dispatcher must verify the actual staged `done/` or `failed/` outcome before writing an event receipt.
- Never bypass the WhatsApp sender/group allowlist to recover attachments; rejected direct messages must be resent to the approved group or explicitly authorized after identity verification.
