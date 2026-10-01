# Product Requirements Document

## Problem

Paper letters and unstructured scans are difficult to preserve, locate, and understand. This project will provide a private system for an authorized archive owner without putting sensitive records in public source control.

## Initial outcome

An authorized user can privately ingest a PDF or image, preserve its original, record validated metadata, search extracted text, and review assisted output with provenance.

## Planned scope

- Private PDF/image intake and immutable original storage.
- Metadata: date, sender, recipient, subject, category, tags, and processing status.
- Full-text search over extracted text.
- Hindi-first content with English navigation where useful.
- Local extraction/OCR by default and a provider-independent analysis adapter.

## Foundation exclusions

No public letter hosting, bulk import, live deployment, provider choice, database choice, authentication choice, or production data handling is implemented or approved.

## First vertical-slice acceptance criteria

1. An authorized synthetic fixture can be ingested without entering Git.
2. The original has an opaque record ID and private storage reference.
3. Metadata is validated and retrievable.
4. Extracted text is searchable with extraction provenance.
5. Tests cover the flow and privacy boundary.
