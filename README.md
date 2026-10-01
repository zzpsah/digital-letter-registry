# Digital Letter Registry

A private, Hindi-first, mobile-friendly searchable memory for official school and government letters.

## Core problem

Important PDFs/images often arrive with useless names such as `DOC10086.pdf`. Months or years later the user usually remembers only the meaning — for example `inter exam last date`, `UDISE PEN correction`, or `registration extension` — not the memo number, exact date, or filename.

## Product goal

```text
Upload / Forward
      ↓
Preserve original
      ↓
Extract text / rough OCR
      ↓
Understand Hindi government-letter context
      ↓
Generate smart filename + structured metadata
      ↓
Index filename + full text + semantic meaning
      ↓
Search later in normal Hindi / English / Hinglish
      ↓
Open or download the original
```

## Non-negotiable architecture

- Original PDF/image is immutable and authoritative.
- OCR, title, filename, category, summary, embeddings, status, and relationships are derived/versioned data.
- Derived data must be recursively reprocessable for the entire archive.
- Search must combine filename, metadata/full text, and semantic/context search.
- Smart filenames should remain useful even outside the custom web app.
- Hindi government/education terminology and document structure must be first-class.
- AI provider must be replaceable; no permanent lock-in to one vendor/model.
- Originals and private archive data stay outside public Git.

## Planned user experience

The main interface is one search box plus optional filters such as date/year, authority, category, file type, and current/historical status. Results show a short context preview and always provide **Open Original** / **Download Original**.

## Status

Planning and governance baseline is now defined. No production deployment or live document migration is authorized yet.

See:
- `PRD.md`
- `docs/PROJECT-HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `TASKS.md`

## Workflow

`READ → UNDERSTAND → PLAN → IMPLEMENT → TEST → REVIEW → FIX → COMMIT → UPDATE DOCUMENTATION`
