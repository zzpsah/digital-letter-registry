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
