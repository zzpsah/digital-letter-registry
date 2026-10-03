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


## Sender account verification — 2026-10-03

- Connected Gmail sender account: `umvstudent@gmail.com` (profile label: Sender).
- Recipient mailbox remains `umvtetahali@gmail.com`.
- A live test message sent from the Sender connection was received in the school inbox with From: UMV Student <umvstudent@gmail.com>.
- DLR runtime sender configuration now targets `umvstudent@gmail.com`.
- Important boundary: the ChatGPT Gmail linked account proves and enables interactive sends from ChatGPT, but the private Oracle background process still requires its own Gmail-capable server-side OAuth refresh credential before autonomous email-outbox draining can be enabled.


## Background Gmail delivery live — 2026-10-03

- Sender account: `umvstudent@gmail.com`; recipient mailbox: `umvtetahali@gmail.com`.
- `umvstudent@gmail.com` was added as an OAuth test user for the UMV Storage Automation Google Auth app.
- Gmail `gmail.send` consent completed successfully for the sender account.
- Gmail API is enabled for the UMV Storage Automation project.
- Private Oracle uses a protected mode-0600 OAuth handoff file as the background sender credential source; token values are not stored in public Git or logs.
- Live Oracle background send passed and the recipient inbox verified the message from UMV Student <umvstudent@gmail.com> with the PDF attachment present.
- `dlr-gmail-outbox.timer` is active; service result is success; queued outbox count is zero after verification.
- Failed send attempts are returned to retryable state instead of remaining stuck in `sending`.
- Synthetic email test package was cleaned after verification.
