# Current State

Verified 2026-10-03:

- A private WhatsApp group named `EDU- Letters` exists on the already-connected Hermes WhatsApp session.
- The group contains the current finite WhatsApp allowlist membership; raw phone/JID values remain private runtime state.
- Hermes group policy is allowlist-only and the DLR connector is bound only to this group.
- Target-group PDF/JPG/JPEG/PNG attachments are staged by the private Hermes hook; target-group text/unsupported media are skipped without an agent reply.
- A protected one-minute systemd timer consumes the staging queue through a Bitwarden-backed DLR worker identity.
- WhatsApp provenance preserves channel, source label and external message id for deduplication.
- Connector-specific real intake is enabled with a cap of 20 WhatsApp documents. The separate manual web pilot cap remains reached and unchanged.
- Synthetic queue→DLR verification passed, including WhatsApp provenance persistence and retry repair after a partial-ingest failure; the synthetic Drive/DB test record was cleaned up.
- Real archive remains at the two previously validated pilot letters after synthetic cleanup.
- Full DLR suite passes 280/280.
- Gateway, WhatsApp intake timer and DLR worker timer are active.

Next live proof is simply the first real PDF/image posted by an allowed member into `EDU- Letters`; no further setup is required.
