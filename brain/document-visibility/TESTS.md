# Tests

- Supabase migration applied successfully; all existing 19 documents remained Public.
- Supabase security advisor run after DDL; returned pre-existing unrelated advisories, no new visibility-policy warning identified.
- Full Python suite: 326/326 passed.
- Web shell: visibility controls covered; inline JavaScript `node --check` passed.
- Oracle index isolated test: Public retained; Private/Personal excluded.
- Oracle private-WhatsApp suppression helper isolated test passed.
- Python compile and `git diff --check` passed for changed runtime scripts.
