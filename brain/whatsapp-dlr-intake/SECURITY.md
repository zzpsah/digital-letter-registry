# Security

WhatsApp session credentials, phone numbers, group JIDs/IDs, message contents and media paths remain private Oracle runtime state. Public Git contains code and synthetic fixtures only. Connector is deny-by-default and source-scoped. DLR Drive/database secrets remain injected at runtime. No arbitrary shell execution from message content.

- WhatsApp-specific size and cumulative-count limits remain bounded; do not relax the sender/group allowlist to recover an unapproved direct message.
- Recovery preserves original attachments and message-ID provenance; no source file is deleted during retry.
