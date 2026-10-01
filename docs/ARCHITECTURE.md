# Architecture

## Proposed flow

Private intake -> immutable private originals -> metadata registry and search -> extraction/OCR -> optional analysis adapter

## Boundaries

- Git contains code, synthetic fixtures, and non-sensitive documentation only.
- Originals, personal metadata, extracted text, and logs remain private.
- Derived output includes source record ID, processor/provider, version, timestamp, and review status.
- The framework, database, storage provider, OCR engine, AI provider, authentication model, and deployment platform are intentionally undecided.
