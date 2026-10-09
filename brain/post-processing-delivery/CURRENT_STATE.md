# Current State

Last updated: 2026-10-09.

## Gmail outbox now sends over SMTP app password (verified 2026-10-09)

- Delivery moved from an OAuth refresh token to a Gmail app password over `smtp.gmail.com:465`.
- Reason: the OAuth refresh token had a 7-day expiry under the Google OAuth client's Testing mode and expired
  on 2026-10-09 14:29 UTC, which silently stopped outbox draining.
- Sender account unchanged: `umvstudent@gmail.com`. Recipient mailbox: `umvtetahali@gmail.com`.
- The 16-character app password is stored only in Bitwarden Secrets Manager as `DLR_GMAIL_APP_PASSWORD`.
  The value is never printed, logged, or committed.
- App passwords require 2-Step Verification on the sending Google account; without it
  `myaccount.google.com/apppasswords` reports the setting as unavailable.
- `~/.local/bin/dlr-gmail-outbox-send-with-bitwarden` now probes `secret-exists DLR_GMAIL_APP_PASSWORD` and,
  when present, runs the outbox under `secret-run-scoped` with that secret injected. Otherwise it falls back
  to the previous OAuth path, so delivery cannot silently stop if the app password is removed.
- `scripts/dlr-gmail-outbox-send.py` already supported both modes; no code change was needed. It selects SMTP
  when `DLR_GMAIL_APP_PASSWORD` is set in the environment.
- Verification performed: SMTP auth through the scoped runner; a live test message delivered and confirmed in
  the sender's Sent Mail over IMAP; and the production `_smtp_send()` function called directly, returning
  `smtp-sent` with the message confirmed in Sent Mail.
- `dlr-gmail-outbox.service` runs to `result=success`; `dlr-gmail-outbox.timer` is active.
- Known limitation: Google revokes all app passwords when the account's main password changes. A future SMTP
  auth failure after a password change means the app password must be regenerated and re-stored.

## Archive-owner Drive OAuth re-consent (verified 2026-10-09)

- The DLR Google Drive refresh token had expired for the same 7-day Testing-mode reason.
- The OAuth app was published from Testing to In production, removing the recurring 7-day refresh-token expiry.
- Consent was completed for the archive owner `umvtetahali@gmail.com` via a loopback PKCE callback on
  `http://127.0.0.1:53682/callback`, driven through a headless Chrome DevTools session.
- The new refresh token was verified (Drive scope live, `originals` folder reachable) and rotated into
  Bitwarden Secrets Manager; the Bitwarden-only refresh path then returned HTTP 200.
- Temporary artifacts were removed: the OAuth handoff file, the temporary consent helper unit, and the copied
  Chrome profile used for the DevTools session.
- Three WhatsApp documents that had been stuck in intake were re-queued and processed; their originals are
  present in the Drive `originals` folder and their letters rows carry populated metadata.

## Semantic search index is not populated (observed 2026-10-09)

- `letter_chunks` holds 0 rows and every `letter_processing.embedding_version` is `unprocessed`.
- Cause: the worker gates chunk embedding on `GEMINI_API_KEY` being present in the worker environment; it is
  not provisioned, so the indexing stage is skipped and the worker reports `chunks=0` on every completed run.
- This is separate from the Supabase `gemini-ai-gateway` key: the gateway keeps its Gemini secret server-side
  and is used for document understanding (24 letters carry
  `context_version = supabase-gemini:gemini-3.5-flash-lite:document-v3`). The gateway does not expose an
  embedding action — its allowed actions are `ask`, `analyze`, `generate-readme`, `analyze-webpage`,
  `analyze-file`, `generate-image`.
- Keyword search is unaffected and covers `extracted_text` in full, plus title, summary, reference, authority,
  concepts, related terms, a Hindi/English alias dictionary and trigram fuzzy matching. OCR text is present for
  35 of 36 letters (~1.54M characters).
- Missing capability is vector similarity only, i.e. conceptual matching with no shared keyword. Enabling it
  requires an embedding-capable credential (a gateway `embed` action or a direct provider key) and a backfill of
  approximately 729 chunks.
- Not actioned; left as-is at the user's direction.

## Prior state — 2026-10-03
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
