# DLR archive quality audit — 2026-11-04

Read-only snapshot of the configured production archive. Generated from local PostgreSQL through the protected worker identity. This is an operational triage list, not a claim that every flagged field is wrong.

## Inventory

| Measure | Count |
|---|---:|
| Documents (`letters`) | 136 |
| Processing rows | 136 |
| Documents missing processing rows | 0 |
| Source/provenance rows | 140 |
| Processing jobs | 181 |
| Completed jobs | 177 |
| Failed jobs | 2 |
| Retired jobs | 1 |
| Processing jobs at snapshot | 1 |
| Documents requiring human quality review | 7 |

### OCR method inventory

| Method | Documents |
|---|---:|
| OCRmyPDF/Tesseract PDF Hindi+English | 57 |
| Tesseract image Hindi+English | 48 |
| Native PDF text | 30 |
| pdftotext layout | 1 |

### Delivery state inventory

| State | Source rows |
|---|---:|
| Complete | 117 |
| Partial | 12 |
| Needs review | 5 |
| Processing | 1 |
| Unset | 5 |

`partial` and `unset` are audit targets; they do not by themselves prove that a document or original file is missing.

## Documents requiring human quality review

These seven records were selected because `needs_reprocessing=true`, confidence is below 0.60, or a low-readability/no-clean-text flag is present. Inspect the original before accepting or editing metadata.

| File | Current title | Confidence | Main concern |
|---|---|---:|---|
| `01.pdf` | Master Circular on Bihar Government Servants CCA Rules | 0.96 | Legacy Hindi native text layer was corrupted; OCR recovery still required |
| `eshikshakosh attendance date03-11-2026.pdf` | Examination Instructions | 0.52 | Low confidence and no clean document text |
| `FIR on Government Servants.pdf` | FIR on Government Servants | 0.52 | Low confidence; missing core metadata; no clean text |
| `Letter No-276 Dated-06-03-2026.pdf` | Teacher Service Grievance Redressal SOP | 0.52 | Low confidence and no clean text; review even though `needs_reprocessing` is false |
| `New CRC code for All.pdf` | Examination Instructions | 0.59 | Low confidence and no clean text |
| `pdfcoffee.com_bihar-seva-sanhita-pdf-free.pdf` | Teacher Transfer Order | 0.52 | Low confidence; metadata/category may be wrong; no clean text |
| `img_3372b722302a.jpg` | ऑनलाइन अवकाश स्वीकृति के निर्देश | 0.52 | Low confidence; missing core metadata; no clean text |

The 51-page `01.pdf` record has had its title, authority, date and summary corrected against the original first page. Its stored full OCR remains unreliable and must not be treated as a verified transcription.

## Failed processing jobs

| File | Failure | Required action |
|---|---|---|
| `cs-education-bihar-vidhan-sabha.jpg` | `unsupported storage provider: local` | Resolve the legacy `local` storage reference / restore supported original access before retrying. This is not an OCR failure. |
| `Let-MIS-1653 Dt-15-07-2025.pdf` | `OCRmyPDF timed out` | Retry after the 40-minute OCR limit and worker-session refresh are deployed; inspect OCR output quality. |

## Processing job at snapshot

`01.pdf` had a reprocessing job left in `processing` after OCR exceeded the former 15-minute limit and the worker's subsequent failure-report request received HTTP 401 (`JWT expired`). The job had not yet reached the 45-minute stale threshold at the time of this snapshot. It must be safely requeued after the refreshed worker code is deployed.

## Advisory metadata flags

The archive also has flags that are not automatically OCR failures:

- `missing_reference_and_date`: 14 records. Forms, manuals and general guidance may legitimately have no memo number or issue date.
- `missing_core_metadata`: 9 records. Check whether the issuer/type is actually absent or simply not captured.
- `low_context_confidence`: 12 records. Verify against the original even when the value is above the new 0.60 delivery threshold only if another quality flag exists.
- `no_clean_document_text`: 9 records. Review text layer/OCR; a high AI confidence must not override this flag.

## Review policy

Use eLetters → Admin → Operations → Quality review. Reprocess extraction problems; only use Confirm reviewed after checking the original. Do not fabricate reference numbers, dates or amounts to clear advisory flags. Use `scripts/audit_document_pipeline.py` to regenerate this snapshot; it is read-only and reports the current queue, OCR versions, review flags, failed jobs and delivery states.
