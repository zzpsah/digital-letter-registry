# Tests

- Fresh encrypted backup archive verification: passed.
- Disposable restore: passed (19 public tables, 28 public functions).
- Disposable migration: passed; a 2,000,010-byte extracted-text update succeeded and `search_letter_cards_v7` returned one result.
- Python regression test checks full text is not rewritten/truncated and index/search use a 50,000-character bound.
- Production retry and remaining-job verification: in progress.
