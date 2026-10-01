# Active Working Decisions

Only current implementation-relevant decisions belong here. Durable rationale lives in `docs/DECISIONS.md`.

- Preserve originals immutably outside public Git.
- Treat OCR, context, filenames, categories, embeddings, validity, and relationships as derived/versioned data.
- Use one replaceable AI provider/model at a time through an adapter.
- Optimize OCR for retrieval/context rather than perfect transcription.
- Keep the primary UI simple and mobile-first with optional filters.
- Do not deploy production or import live archive data without explicit approval.
