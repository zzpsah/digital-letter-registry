# Current State

Verified 2026-10-03:
- Existing Hermes WhatsApp bridge/session is reused; no second WhatsApp login exists.
- Live source group is bound privately as `EDU- Letters`; exact group identity stays outside public Git.
- Group metadata query returned the expected group name and three current participants.
- WhatsApp→DLR intake timer and bridge hook are active.
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
