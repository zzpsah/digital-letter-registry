# Large Document Search Reliability

Prevent large OCR outputs from failing ingestion because PostgreSQL full-text vectors have a per-vector size ceiling. Preserve immutable originals and complete extracted text; bound only the indexed/ranked search projection.
