# Architecture

Original file in private Drive remains authoritative. Complete OCR output is stored in `letter_processing.extracted_text`. The GIN index expression and active `search_letter_cards_v7` haystack use `left(extracted_text, 50000)`, avoiding the PostgreSQL ~1 MiB tsvector limit. This intentionally bounds full-text ranking, not the stored text or source document. Context snippets remain separately bounded to 360 characters.
