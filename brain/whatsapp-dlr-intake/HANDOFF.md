# Handoff

Read project RULES/AGENTS, this brain folder, private oracle-server WhatsApp brain, and live runtime before changes. Reuse the existing Hermes gateway/session. Never commit source chat IDs/numbers/session data. Current two-letter manual pilot cap is already reached; connector must not bypass it accidentally.


Connector is now live. The exact group identifier, member identifiers and credentials stay only in private runtime configuration. Current public-safe facts: group label is `EDU- Letters`, only PDF/JPG/JPEG/PNG are accepted, text is silently skipped, connector cap is 20, timers are active, and synthetic E2E verification passed with cleanup.


## 2026-10-18 operational recovery

- Production is local Oracle PostgreSQL via the local Supabase-compatible API; hosted Supabase is not the live processing primary.
- Intake count cap was reached at 100. Recovery cap set to 100,000 and WhatsApp-only size cap to 2 GiB.
- A sender rejected by Hermes at 19:51 UTC was not staged; do not infer that message attachments were archived. Ask the owner to resend via the configured approved group or verify/authorize the sender explicitly.
- Recovery completed: all 18 quarantined staged attachments were retried; 17 source records were recorded, one duplicate was detected, and all 12 created processing jobs completed. Two event receipts still show downstream Gmail outbox degradation. One separate direct message was rejected before staging and must be resent via the approved group or explicitly authorized after sender verification.
