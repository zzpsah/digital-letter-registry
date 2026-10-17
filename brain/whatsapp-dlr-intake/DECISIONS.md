# Decisions

- Reuse existing Hermes WhatsApp bridge/session.
- Accept only document/image attachments from an explicitly configured source label/chat identity.
- PDF/JPG/JPEG/PNG only; no arbitrary media.
- Preserve WhatsApp message ID as provenance for deduplication.
- Do not expose phone numbers/chat IDs/media paths in public Git.
- Keep real connector intake separately guarded from manual-pilot limit.
- Do not auto-delete or rename originals.

- Keep the cumulative WhatsApp intake cap bounded and explicit; increase it only for a user-authorized recovery window. Current configured cap: 100,000 source messages, hard maximum 1,000,000; never configure below 50,001.
- Keep a separate WhatsApp-only upload-size cap (default 2 GiB for WhatsApp intake; maximum 2 GiB. The normal web upload limit remains independently configured.) so normal web uploads do not broaden.
- A webhook HTTP success is not proof of intake success; the dispatcher must verify the actual staged `done/` or `failed/` outcome before writing an event receipt.
- Never bypass the WhatsApp sender/group allowlist to recover attachments; rejected direct messages must be resent to the approved group or explicitly authorized after identity verification.
