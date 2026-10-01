# Decisions

## Accepted product decisions

1. **Context-first retrieval:** the product is primarily a searchable memory, not a file browser.
2. **Original is authoritative:** source PDF/image is immutable; OCR/AI output is assistive.
3. **Perfect OCR is unnecessary:** enough extraction to infer/search context is sufficient.
4. **Hindi-first intelligence:** government Hindi vocabulary and document structure are core capabilities.
5. **Smart rename is mandatory:** every successfully understood document gets a normalized human-searchable archive filename while retaining its original filename.
6. **Three-layer search:** filename/title + full text/metadata + semantic/context.
7. **Simple mobile UX:** one main search box with optional filters.
8. **Validity is explicit:** support Current / Expired / Historical / Superseded / Unknown.
9. **Recursive upgrades:** historical documents must benefit from future processors, models, dictionaries, and filename rules.
10. **AI is replaceable:** one active provider/model at a time through an adapter; no model lock-in.
11. **Public Git is code/docs only:** no actual archive content or secrets.
12. **No production deployment yet:** deployment requires explicit authorization.

## Open decisions

- durable private original-file storage provider
- initial AI provider/model
- exact authentication mechanism for the web UI
- final queue implementation
- exact embedding model/provider
