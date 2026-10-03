# Current State

Verified 2026-10-03:
- WhatsApp intake provenance now retains a private reply destination and query/caption metadata.
- A private Oracle post-processing dispatcher is active on a one-minute timer.
- Dispatcher waits for completed processing, then sends a concise description back to the exact source WhatsApp chat.
- Local receipt state prevents duplicate WhatsApp replies across dispatcher reruns.
- Dispatcher prepares a private email-outbox package containing the user query/caption, automated reply, logical Drive path, portal pointer and original attachment.
- Gmail MIME assembly dry-run passed with the attachment included.
- Existing DLR Google OAuth grant is Drive-only; Gmail sending therefore remains queued until a separate Gmail `gmail.send` authorization is configured.
- A Gmail outbox sender is implemented and ready for Bitwarden-injected OAuth credentials.
- Full DLR suite passes 281/281.
- Synthetic E2E test artifacts were cleaned from Drive, Supabase and local outbox state.
