# Product Requirements Document

## Product

**Digital Letter Registry** — a private searchable memory for Hindi-first official letters, circulars, orders, PDFs, scans, and images.

## Problem

The user receives many official documents through messaging channels. Files often have meaningless names and become difficult to recover later. The user usually remembers the subject or context, not the exact memo number/date/filename.

Examples of real search intent:
- `inter exam last date`
- `BSEB form date extension`
- `UDISE PEN correction`
- `11th registration`
- `board ne exam form bharne ka date badhaya tha`

## Primary outcome

An authorized user can privately ingest a PDF/image and later find it using remembered meaning, keywords, Hindi/English/Hinglish wording, date/category filters, or ordinary filename search.

## Required processing

1. Preserve original privately and immutably.
2. Extract embedded text when available.
3. Run Hindi/English OCR only when needed; perfect OCR is not required.
4. Apply government/education vocabulary and structural hints.
5. Use one replaceable AI provider to derive context.
6. Generate a short normalized smart filename.
7. Save structured metadata, full text, concepts, and processing versions.
8. Index for filename, full-text, and semantic/context search.
9. Always link back to the original.

## Required metadata

At minimum: record ID, original filename, smart filename, storage reference, authority/department, subject/title, category/subcategory, summary/context, issue/received/upload dates when known, deadlines, action-required hint, concepts/keywords, file type, validity/status hint, related-document links, and processing-version fields.

## Validity and relationships

Documents may be `Current`, `Expired`, `Historical`, `Superseded`, or `Unknown`. Later extension/correction/cancellation letters should be linkable to earlier records. Historical letters remain searchable.

## Smart filename

Suggested pattern:

`YYYY-MM-DD_CATEGORY_SHORT-SUBJECT[_LETTER-NO].pdf`

Uncertain fields are omitted rather than guessed. Original filename is retained in metadata.

## Search

Ranking should combine:
- normalized smart filename/title,
- metadata and full extracted/OCR text,
- semantic/context similarity,
- optional filters.

## Recursive upgrades

All derived processing is versioned. Future changes to OCR, dictionary, AI model/provider, filename rules, categories, embeddings, or validity logic must be able to reprocess historical records without re-uploading originals.

## Mobile/web requirement

Primary interface is a responsive web/PWA view optimized for mobile and low bandwidth. Search remains simple; advanced filters stay optional.

## Privacy boundary

No real letters, private identifiers, credentials, API keys, storage paths containing secrets, or archive content belong in this public repository.

## First useful vertical slice

A synthetic/private test document can be uploaded, preserved outside Git, processed into context + smart filename + searchable text, found through contextual search and filters, and opened from its original private storage reference.
