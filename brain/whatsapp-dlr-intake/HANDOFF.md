# Handoff

Read project RULES/AGENTS, this brain folder, private oracle-server WhatsApp brain, and live runtime before changes. Reuse the existing Hermes gateway/session. Never commit source chat IDs/numbers/session data. Current two-letter manual pilot cap is already reached; connector must not bypass it accidentally.


Connector is now live. The exact group identifier, member identifiers and credentials stay only in private runtime configuration. Current public-safe facts: group label is `EDU- Letters`, only PDF/JPG/JPEG/PNG are accepted, text is silently skipped, connector cap is 20, timers are active, and synthetic E2E verification passed with cleanup.


## 2026-10-18 operational recovery

- Production is local Oracle PostgreSQL via the local Supabase-compatible API; hosted Supabase is not the live processing primary.
- Intake count cap was reached at 100. Recovery cap set to 150 and WhatsApp-only size cap to 100 MiB.
- A sender rejected by Hermes at 19:51 UTC was not staged; do not infer that message attachments were archived. Ask the owner to resend via the configured approved group or verify/authorize the sender explicitly.
- Retry the existing quarantined attachments only after preserving the failed receipts and verifying deduplication. Verify letter source rows and job status after worker runs.
