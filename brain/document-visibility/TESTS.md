# Tests

- Supabase migration applied successfully; all existing 19 documents remained Public.
- Supabase security advisor run after DDL; returned pre-existing unrelated advisories, no new visibility-policy warning identified.
- Full Python suite: 326/326 passed.
- Web shell: visibility controls covered; inline JavaScript `node --check` passed.
- Oracle index isolated test: Public retained; Private/Personal excluded.
- Oracle private-WhatsApp suppression helper isolated test passed.
- Python compile and `git diff --check` passed for changed runtime scripts.

## Personal collection UI tests

- Full Python test suite: 326/326 passed.
- Web shell assertions cover Personal nav/page, Visibility filter, and Personal query.
- Extracted inline JavaScript passed `node --check`.
- `git diff --check` passed.
