# DLR archive quality audit — 2026-11-04

Read-only production snapshot. Regenerate with `scripts/audit_document_pipeline.py`; this repository intentionally stores aggregate counts, not private archive filenames or document contents.

## Inventory at 18:15 UTC

| Measure | Count |
|---|---:|
| Documents | 138 |
| Processing rows | 138 |
| Missing processing rows | 0 |
| Source/provenance rows | 142 |
| Processing jobs | 185 |
| Completed jobs | 180 |
| Failed jobs | 3 |
| Pending jobs | 0 |
| Processing jobs | 1 |
| Stale processing jobs (45m+) | 0 |
| Documents requiring human review | 23 |

## OCR method inventory

| Method | Documents |
|---|---:|
| OCRmyPDF/Tesseract PDF Hindi+English | 59 |
| Tesseract image Hindi+English | 48 |
| Native PDF text | 30 |
| pdftotext layout | 1 |
| Unprocessed | 1 |

## Delivery state inventory

| State | Source rows |
|---|---:|
| Complete | 117 |
| Partial | 8 |
| Needs review | 11 |
| Processing | 0 |
| Unset | 6 |

Partial/unset are review targets; they do not by themselves prove an original file is missing.

## Quality flag inventory

| Flag | Documents |
|---|---:|
| Missing reference number and issue date | 14 |
| Low context confidence | 11 |
| Missing core metadata | 8 |
| No clean document text | 8 |

The 23 review-queue count is the union of unresolved quality flags, not the sum of the flag counts. Some flags overlap. Missing reference/date can be legitimate for forms and manuals; inspect the source before accepting or correcting it.

## Failed jobs requiring action

1. One legacy image record failed with `unsupported storage provider: local`. Resolve its original-file storage reference before retrying; this is a storage compatibility issue, not OCR.
2. The 2025-26 UDISE guidance PDF had two failed attempts under the former timeout/bridge stop. A new retry is currently processing with the 3,600-second OCR timeout and 3,900-second systemd/bridge ceiling.

## Current reprocessing

The 51-page Hindi Master Circular (`01.pdf`) has completed OCR. Its transcript contains 111,817 characters, including 76,964 Devanagari characters. The original remains unchanged. The record is held for human review because OCR completion does not verify the AI interpretation; the issue/effective dates and procedural claims still require source-page confirmation. The newly ingested scan completed in the same recovery session. The UDISE guidance PDF is now the sole processing job, running through OCR under the extended timeout.

## Review workflow

The Admin → Operations → Quality review API now includes documents with unresolved OCR, confidence, missing-core-metadata, missing-reference/date and source-conflict flags even when `needs_reprocessing` was not set. The administrator must inspect the original before accepting a record. Reprocess extraction failures; do not invent dates, memo numbers or amounts.


## Latest verification

- Master Circular OCR: completed; all 51 pages represented; 76,964 Devanagari characters detected.
- Master Circular delivery: held for human review; OCR output is present, but AI-derived effective date and summary details are not yet verified page by page.
- Current queue at 18:15 UTC: zero pending jobs and one processing job (the UDISE OCR retry); no stale processing jobs.
- The one-minute legacy timer had been disabled during the event-driven migration. The WhatsApp webhook chain invoked the worker only for WhatsApp events, leaving manually queued reprocess and ordinary upload jobs without a wake-up trigger. The fallback timer is now enabled with `OnUnitInactiveSec=1min`, so it runs one minute after each worker exit. It does not poll WhatsApp intake. The webhook and fallback share the same flock-protected worker wrapper.
- Full DLR test run: **433 tests passed**. The two stale web-shell assertions were corrected to test the current original-document streaming endpoint and current session refresh flow.
- n8n Operations test run: **66 tests passed** after updating the bridge timeout assertion to 3,900 seconds.
