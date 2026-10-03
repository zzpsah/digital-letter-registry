# Tasks

- [x] Define reply/email transcript behavior.
- [x] Preserve source reply destination and user query/caption in private provenance.
- [x] Add idempotent post-processing delivery dispatcher.
- [x] Send same-chat WhatsApp reply after completed processing.
- [x] Prepare queued email transcript + attachment package.
- [ ] Add Gmail sender authorization and live email send.
- [ ] Add Telegram reply parity.

- [x] Gmail sender implementation + dry-run MIME validation.
- [ ] One-time Gmail `gmail.send` OAuth authorization and live email send verification.


## Sender account verification — 2026-10-03

- Connected Gmail sender account: `umvstudent@gmail.com` (profile label: Sender).
- Recipient mailbox remains `umvtetahali@gmail.com`.
- A live test message sent from the Sender connection was received in the school inbox with From: UMV Student <umvstudent@gmail.com>.
- DLR runtime sender configuration now targets `umvstudent@gmail.com`.
- Important boundary: the ChatGPT Gmail linked account proves and enables interactive sends from ChatGPT, but the private Oracle background process still requires its own Gmail-capable server-side OAuth refresh credential before autonomous email-outbox draining can be enabled.
