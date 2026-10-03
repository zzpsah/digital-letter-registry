# Decisions

- Reuse existing Hermes WhatsApp bridge/session.
- Accept only document/image attachments from an explicitly configured source label/chat identity.
- PDF/JPG/JPEG/PNG only; no arbitrary media.
- Preserve WhatsApp message ID as provenance for deduplication.
- Do not expose phone numbers/chat IDs/media paths in public Git.
- Keep real connector intake separately guarded from manual-pilot limit.
- Do not auto-delete or rename originals.
