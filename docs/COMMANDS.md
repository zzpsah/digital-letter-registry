# Commands

From the repository root:

```bash
git status
git diff
git diff --cached
```

## Tests

This repository uses a `src/` layout. Run tests with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Recommended local setup:

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

For OCR fallback, runtime must also provide:

- `ocrmypdf`
- Tesseract
- Hindi language data (`hin`)
- English language data (`eng`)

These system tools are intentionally not bundled or hard-coded into the repository.

## Guarded live synthetic Supabase integration

This command is for **synthetic/test data only**. It does not upload to Drive and refuses files whose names do not contain `synthetic` or `test`.

Required runtime environment:

```bash
SUPABASE_URL=...
SUPABASE_PUBLISHABLE_KEY=...
SUPABASE_ACCESS_TOKEN=...
SUPABASE_OWNER_ID=...
```

Run:

```bash
PYTHONPATH=src python3 scripts/run_synthetic_supabase_integration.py \
  --file /private/path/synthetic-integration-test.pdf \
  --storage-reference runtime-private-object-reference
```

The command verifies:

- authenticated source insert,
- processing-row initialization,
- owner-visible read,
- duplicate SHA protection.

Actual values must never be committed or pasted into public logs.

## Production

No production deployment command is defined.
