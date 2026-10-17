# Current State

- Observed failure: PostgreSQL rejected an OCR text write because `to_tsvector` exceeded the ~1 MiB per-vector limit (reported input 1,435,716 bytes).
- Production migration `20261018193000_bound_fts_text_size.sql` was applied to Oracle `dlr_primary` after a fresh encrypted backup and disposable restore test.
- `letter_processing.extracted_text` remains full length. The GIN index and `search_letter_cards_v7` use the first 50,000 characters.
- A disposable migration test stored a 2,000,010-byte text value and returned a search match successfully.
- Recovery job processing is ongoing; do not claim all jobs are complete until the local queue is verified.
