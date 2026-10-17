# Current State

Verified 2026-10-03:
- Existing Hermes WhatsApp bridge/session is reused; no second WhatsApp login exists.
- Live source group is bound privately as `EDU- Letters`; exact group identity stays outside public Git.
- Group metadata query returned the expected group name and three current participants.
- The event-driven path watcher is active; legacy one-minute intake/worker timers are disabled. The intake consumer itself is invoked by the n8n event pipeline.
- Fresh unique synthetic PDF sent through the live WhatsApp bridge was automatically staged and ingested into DLR.
- Provenance recorded `source_channel=whatsapp` with a non-empty external message-id dedup key.
- Dedicated DLR worker completed processing.
- Authenticated DLR search found the synthetic record and private original streaming succeeded.
- Synthetic Drive object and all synthetic database/provenance/job rows were deleted after verification.
- Outbound bridge-sent synthetic/test media now also passes the same DLR staging helper, enabling reproducible E2E connector tests.
- Real archive letters were untouched.

Next observation: first genuine PDF/JPG/PNG posted by another member in `EDU- Letters`.

- Genuine public official CBSE circular proof also passed: WhatsApp intake, worker processing, corrected explicit CBSE metadata, search and original streaming.
- Real-document review exposed and fixed CBSE-vs-UDISE classification precedence.


## Official public PDF connector proof — 2026-10-03

- A public official education PDF was sent through the live `EDU- Letters` WhatsApp group path using a test-marked filename so the outbound safety guard could exercise the connector.
- Connector staging succeeded; WhatsApp provenance and external message-id dedup were stored.
- Worker processing completed.
- Authenticated search found the record and private original streaming returned the archived PDF successfully.
- A transient Bitwarden lookup failure was observed on the first consumer attempt; the private Oracle consumer was hardened with bounded retry/backoff for that exact transient condition.
- After retry hardening, the consumer service reports success and both connector and worker timers are active.
- The test archive copy and all derived DB/provenance/job rows were cleaned after verification. Real archive letters were untouched.


## 2026-10-18 recovery findings

- Oracle local PostgreSQL primary had 100 WhatsApp provenance records and the configured real-intake cap was also 100; this caused later attachments to be quarantined with `WhatsApp intake limit reached (100)`.
- Several staged PDFs exceeded the prior WhatsApp-specific 20 MiB intake size default. The WhatsApp-only cap is now configurable and bounded at 100 MiB; normal web/API upload policy remains unchanged.
- The event dispatcher now checks the per-message `done/` or `failed/` staging outcome after n8n returns. A quarantined item is recorded under `event-dispatch/failed/`, not falsely reported as completed.
- The current live direct WhatsApp message from an unapproved sender was rejected by Hermes before staging. Do not weaken the allowlist; the sender must use the configured approved group or be verified and explicitly authorized by the owner.
- Recovery target is the existing 18 staged failures. No attachment is deleted; retries use the original message ID and duplicate checks.
