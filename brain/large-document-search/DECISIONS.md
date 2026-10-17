# Decisions

- Never truncate the stored full OCR extraction merely to satisfy a search-index limit.
- Bound the indexed/search-ranking window to 50,000 characters; this is safely below PostgreSQL's ~1 MiB tsvector limit even for dense tokenization.
- Keep the active search RPC and GIN index expression aligned.
- Apply schema changes to Oracle primary only after a verified backup and disposable restore/test; do not blindly replay the full migration directory because the live schema has known drift.
