# Handoff

Read project RULES/AGENTS, WhatsApp intake brain and this folder. Reply destinations are private provenance metadata.

## Delivery credential (2026-10-09)

Gmail outbox delivery authenticates with a Gmail app password over `smtp.gmail.com:465`, injected from
Bitwarden Secrets Manager as `DLR_GMAIL_APP_PASSWORD` by
`~/.local/bin/dlr-gmail-outbox-send-with-bitwarden`. The wrapper falls back to the previous OAuth path when
that secret is absent.

The sender account is `umvstudent@gmail.com`; the recipient mailbox is `umvtetahali@gmail.com`. The
archive-owner account `umvtetahali@gmail.com` is a separate identity — its Drive OAuth grant does not carry
`gmail.send`, so do not try to reuse the Drive token for mail.

App passwords require 2-Step Verification on the sender account, and Google revokes them if that account's
main password changes; regenerate and re-store the secret in that case.
