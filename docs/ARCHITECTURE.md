# Architecture

## Core rule

**Preserve originals forever; version and regenerate everything derived.**

## Logical flow

```text
Web / future messaging intake
          ↓
      Ingestion API
          ↓
 Save immutable original ───────────────┐
          ↓                            │
 Detect embedded text                  │
          ↓                            │
 OCR only if needed                    │
          ↓                            │
 Hindi government vocabulary           │
          ↓                            │
 Replaceable AI context adapter        │
          ↓                            │
 Smart title / filename / metadata     │
          ↓                            │
 Full-text + semantic indexes          │
          ↓                            │
 Search API + filters                  │
          ↓                            │
 Mobile web/PWA ── Open Original ──────┘
```

## Recommended initial components

- Python + FastAPI backend
- PostgreSQL for metadata and full-text search
- pgvector for semantic search
- Redis + lightweight worker queue for asynchronous processing
- PyMuPDF/pypdf for embedded text extraction
- Tesseract/OCRmyPDF for Hindi/English OCR fallback
- provider-independent AI adapter
- durable private original-file storage
- responsive web/PWA frontend

Exact provider/storage choices remain configuration, not domain logic.

## Document model

Store source data separately from derived data.

### Immutable/source
- record ID
- original filename
- original file hash
- original private storage reference
- received/upload provenance

### Derived/versioned
- extracted/OCR text
- title/context/summary
- smart filename
- category/subcategory
- concepts/keywords
- authority and date hints
- action/deadline hints
- validity/status
- related-document links
- embeddings/search vectors
- processor/model/dictionary/rule versions

## Search model

Final relevance should blend:
1. smart filename/title match,
2. metadata/full-text match,
3. semantic/context similarity,
4. filters and recency/status rules where appropriate.

The original document remains the authority for exact dates, memo numbers, amounts, and wording.

## Reprocessing

A queue job must be able to select documents by processing version and regenerate any derived layer without duplicating originals. Reprocessing must be idempotent and auditable.

## Deployment boundary

The planned Oracle VPS may host processing/API/search components, but original documents should not depend on that VPS as their only durable copy.
