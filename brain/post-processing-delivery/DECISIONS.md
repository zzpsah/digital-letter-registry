# Decisions

- Reply only after processing completes.
- Reply to the exact source chat, not a fixed broadcast destination.
- WhatsApp reply is concise: title/what it is about, short summary, authority/reference/date when available, logical archive path and portal pointer.
- Email contains the user query/caption, automated reply, structured document details, logical Drive path and original attachment.
- Do not expose Google Drive object IDs in chat/email; use the logical archive path.
- Delivery must be idempotent.
- Gmail send activation requires an explicit Gmail-capable runtime grant; Drive-only OAuth is not widened silently.
