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
12. **Production evolution is migration-led:** live behavior may evolve only through documented, additive, verified migrations and versioned runtime changes.
13. **Version history is first-class:** OCR and AI/context outputs must evolve toward append-versioned artifacts; current rows are projections, not processing history.
14. **Delivery is downstream:** email/WhatsApp delivery state must not define document identity and will move to normalized delivery records.
15. **Primary AI path:** the existing Supabase Gemini gateway is the primary production AI integration; Oracle-side direct Gemini is a future fallback, not the primary secret location.

## Current implementation choices

- durable original storage: private Google Drive archive
- metadata/search database: dedicated Supabase DLR project
- processing host: Oracle VPS
- intake: WhatsApp bridge plus API/import adapters
- outbound archive delivery: Gmail OAuth sender + WhatsApp receipt
- primary AI integration: Supabase Gemini gateway
- current OCR: Hindi/English Tesseract/OCRmyPDF fallback
- current queue: durable Supabase processing jobs

## Still-evolving choices

- final vision/document-understanding model and schema version
- final embedding model/provider
- long-term backup/export cadence
- normalized historical processing/delivery/audit migration schedule
