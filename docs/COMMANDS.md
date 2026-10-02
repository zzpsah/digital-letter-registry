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

## Structured AI runtime

The first adapter is Gemini, but the stored schema remains provider-neutral.

Runtime variables:

```bash
AI_PROVIDER=gemini
AI_MODEL=gemini-3.8-flash
GEMINI_API_KEY=...
```

Do not commit the real API key. The model name is configurable so the archive can be reprocessed later with a different provider/model.

## Production

No production deployment command is defined.


## FastAPI local development

Install the package, then run the private app locally:

```bash
python3 -m pip install -e .
fastapi dev
```

Required runtime configuration for authenticated search:

```bash
SUPABASE_URL=...
SUPABASE_PUBLISHABLE_KEY=...
AUTH_REDIRECT_URL=http://localhost:8000/auth/callback
```

For hybrid semantic search also provide:

```bash
GEMINI_API_KEY=...
EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSIONS=768
```

The passwordless redirect URL must be explicitly allowlisted in Supabase Auth settings. Do not use a private Drive URL or object ID as an auth redirect.

The PWA service worker caches only the application shell. It intentionally does not cache `/api/` responses or private letter data.


## Private original streaming

The server-side Google Drive reader requires a runtime-only OAuth access token:

```bash
GOOGLE_DRIVE_ACCESS_TOKEN=...
```

The token is used only by the backend. The browser receives file bytes through the authenticated API and never receives the Drive object ID or private Drive URL.

The current adapter accepts a short-lived access token. A refresh-token/service credential lifecycle is intentionally still pending before production use.


## Synthetic-first private intake runtime

The HTTP intake endpoint is `POST /api/v1/intake` and requires an authenticated Supabase bearer session.

Runtime-only configuration:

```bash
SUPABASE_URL=...
SUPABASE_PUBLISHABLE_KEY=...
SUPABASE_ACCESS_TOKEN=...
GOOGLE_DRIVE_ACCESS_TOKEN=...
DRIVE_ORIGINALS_FOLDER_REFERENCE=...
ENABLE_REAL_INTAKE=false
```

With `ENABLE_REAL_INTAKE=false` (default), intake and processing accept only filenames clearly containing `synthetic` or `test`. Duplicate SHA-256 content is rejected before a second Drive upload.

## One-job synthetic worker

The worker claims at most one pending job and then exits:

```bash
PYTHONPATH=src python3 scripts/run_worker_once.py
```

It performs:

```text
claim job
  → private original download
  → native PDF text / Hindi+English OCR fallback
  → structured context extraction
  → smart filename + metadata persistence
  → chunk embeddings
  → complete or fail durable job
```

For PDF OCR install OCRmyPDF + Tesseract `hin`/`eng`; image OCR uses Tesseract directly. This command is for synthetic integration verification until real intake is explicitly approved.
