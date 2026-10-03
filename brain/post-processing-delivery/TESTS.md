# Tests

Planned: source metadata captured without public leakage; pending jobs do not reply; completed jobs reply once; repeat dispatcher runs do not duplicate replies; email package contains query/reply/logical Drive path/original; missing Gmail sender leaves email queued without losing the WhatsApp reply.


## Live synthetic E2E — 2026-10-03

Passed:
- WhatsApp test document + caption staged and processed.
- Private reply destination persisted.
- Completed processing triggered exactly one same-chat reply; dispatcher rerun did not resend because of local receipt state.
- Email package contained transcript, captured user query, automated reply, logical archive path and original PDF attachment.
- Gmail message MIME assembly dry-run validated successfully.
- Full DLR suite: 281/281.
- Synthetic Drive/DB/outbox artifacts cleaned after verification.

Pending: live Gmail API send, blocked only by missing Gmail-capable OAuth grant; current DLR OAuth is Drive-only.


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
