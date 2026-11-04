# DLR archive quality audit — 2026-11-04

Read-only production snapshot. Regenerate with `scripts/audit_document_pipeline.py`; this repository intentionally stores aggregate counts, not private archive filenames or document contents.

## Inventory at 17:36 UTC

| Measure | Count |
|---|---:|
| Documents | 138 |
| Processing rows | 138 |
| Missing processing rows | 0 |
| Source/provenance rows | 142 |
| Processing jobs | 185 |
| Completed jobs | 178 |
| Failed jobs | 3 |
| Pending jobs | 2 |
| Processing jobs | 1 |
| Stale processing jobs (45m+) | 0 |
| Documents requiring human review | 24 |

## OCR method inventory

| Method | Documents |
|---|---:|
| OCRmyPDF/Tesseract PDF Hindi+English | 57 |
| Tesseract image Hindi+English | 48 |
| Native PDF text | 31 |
| pdftotext layout | 1 |
| Unprocessed | 1 |

## Delivery state inventory

| State | Source rows |
|---|---:|
| Complete | 117 |
| Partial | 8 |
| Needs review | 10 |
| Processing | 1 |
| Unset | 5 |

Partial/unset are review targets; they do not by themselves prove an original file is missing.

## Quality flag inventory

| Flag | Documents |
|---|---:|
| Missing reference number and issue date | 14 |
| Low context confidence | 12 |
| Missing core metadata | 9 |
| No clean document text | 9 |

The 24 review-queue count is the union of unresolved quality flags, not the sum of the flag counts. Some flags overlap. Missing reference/date can be legitimate for forms and manuals; inspect the source before accepting or correcting it.

## Failed jobs requiring action

1. One legacy image record failed with `unsupported storage provider: local`. Resolve its original-file storage reference before retrying; this is a storage compatibility issue, not OCR.
2. One 2025-26 UDISE guidance PDF failed with `OCRmyPDF timed out` under the former timeout. Retry it after the 40-minute OCR timeout and worker session-refresh fix are confirmed.

## Current reprocessing

The 51-page Hindi Master Circular (`01.pdf`) was manually requeued after its previous run timed out at 15 minutes and failure reporting failed with an expired JWT. At this snapshot its new OCR run is active (page raster/OCR has advanced through page 17); the UDISE retry and a newly ingested scan are queued behind it. The earlier UDISE retry was deliberately stopped when we found the n8n bridge still had a 15-minute timeout; that attempt is retained as a failed job for audit, and a fresh retry is queued under the corrected 45-minute bridge timeout. The original file is preserved; its metadata has been corrected from the original first page, but the full OCR transcript remains unverified until the new run completes.

## Review workflow

The Admin → Operations → Quality review API now includes documents with unresolved OCR, confidence, missing-core-metadata, missing-reference/date and source-conflict flags even when `needs_reprocessing` was not set. The administrator must inspect the original before accepting a record. Reprocess extraction failures; do not invent dates, memo numbers or amounts.
