# Current State

- Repository exists and is governed by DevOS/project rules.
- Public-repository privacy boundary is established.
- Product requirements are now concrete: private Hindi-first official-letter archive with context-first search.
- Smart renaming, full-text search, semantic/context search, mobile filters, original-file links, validity states, and recursive archive reprocessing are required.
- Original documents are immutable; all OCR/AI/search/filename layers are derived and versioned.
- AI provider is intentionally replaceable and only one primary model/provider should be active at a time.
- No production deployment, live archive import, private document storage, database, OCR service, AI credential, or application code has been deployed from this repository yet.
- Next step: choose private storage + initial AI provider, then implement the first synthetic/private vertical slice.

## 2026-10-01 — Domain foundation

- Implemented a dependency-free Python domain layer for immutable source identity, processing versions, statuses/relationships, SHA-256 fingerprints, and deterministic smart filenames.
- Verified with five standard-library unit tests and Python compilation.
- No external adapter, credential, live document, or deployment was used.
