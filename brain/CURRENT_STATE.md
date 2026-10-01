# Current Working State

Last verified: 2026-10-01

## Current state

- Canonical repository: `zzpsah/digital-letter-registry`.
- Product requirements and architecture baseline are documented.
- Context-first search, smart renaming, Hindi-government understanding, original-file preservation, validity states, and recursive reprocessing are required.
- No application runtime or production deployment has been created from this repository.

## Open setup decisions

- private durable storage for original PDFs/images
- initial AI provider/model
- authentication method for the web UI
- exact queue/worker implementation

## Next concrete step

Choose private storage + initial AI provider, then implement the first synthetic/private vertical slice:

`Upload → preserve original → extract/OCR → derive context → smart rename → index → search → open original`
