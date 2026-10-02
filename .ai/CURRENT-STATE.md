# Current State

- Canonical repository: `zzpsah/digital-letter-registry`.
- Formal archive name: **Official Letter Intelligence Archive**.
- Public-repository privacy boundary is established: code/docs/synthetic fixtures/schema only.
- Existing private UMV Google Drive is the selected original-file storage.
- Private archive structure exists with `originals/`, `quarantine/`, and `exports/`; all three are currently empty.
- A separate Supabase archive project exists, isolated from the existing UMV database.
- Core tables exist: `letters`, `letter_processing`, `letter_relationships`, and `letter_chunks`.
- RLS is enabled on all public archive tables; security advisor is clean.
- The archive database currently contains no auth user and no real archive rows.
- The public-safe core schema is captured under `supabase/migrations/`.
- Domain code includes immutable source identity, SHA-256 fingerprints, processing versions, statuses/relationships, and smart filenames.
- Official filename pattern is `short-title__issuer__date__reference-number.ext`.
- Naming now preserves Hindi/English/Hinglish Unicode and uses `undated` / `no-ref` placeholders.
- Rename functionality is preview-only; no Drive rename executor is authorized yet.
- Persistence ports, Supabase row mapping, an injected-transport Supabase repository adapter, synthetic/local ingestion preparation, storage ports, and an injected Google Drive storage adapter are implemented.
- GitHub CI runs the synthetic unit-test suite on pushes/PRs.
- No live document ingestion, OCR/AI processing, or production deployment has occurred.

## Next step

Establish an authenticated archive owner for RLS-backed writes, then wire the live Google Drive transport and real authenticated Supabase transport using synthetic fixtures before any live-letter ingestion.


## 2026-10-02 — Live synthetic integration checkpoint

- Live private Drive upload was verified with a synthetic PDF in `originals/`.
- The synthetic PDF uses the approved smart-filename pattern and remains private.
- A Supabase archive-owner Auth identity was created through passwordless email signup.
- Supabase archive-owner email is confirmed.
- Runtime authenticated Supabase PostgREST transport and a guarded synthetic integration command are implemented; the final live insert/RLS-denial execution remains pending.
- No real archive letter was ingested or renamed.


## Runtime Supabase integration

- `src/letter_registry/supabase_runtime.py` provides environment-only authenticated PostgREST transport.
- `scripts/run_synthetic_supabase_integration.py` refuses non-synthetic filenames and performs no Drive upload.
- No project URL, publishable key, access token, owner UUID, or Drive object ID is stored in Git.


## Phase 2 extraction/context foundation

- Provider-neutral native PDF extraction contract is implemented.
- Native-text usability heuristic prefers embedded text and requests OCR only when needed.
- Hindi + English OCR fallback contract is implemented and versioned, but no concrete OCR engine is wired yet.
- Hindi/English/Hinglish government and education vocabulary is implemented.
- Deterministic pre-AI context hints detect concepts such as registration, exam form, deadline/extension, UDISE, PEN, scholarship, correction, verification, training, and government letter structure markers.


## Concrete extraction backends

- `PypdfTextBackend` provides native embedded PDF text extraction.
- `OcrmypdfTesseractBackend` provides local Hindi+English OCR via OCRmyPDF/Tesseract and sidecar text.
- OCR binaries/language packs are runtime dependencies, not bundled into the repo.
- Extraction results now map into `letter_processing.extracted_text` and `ocr_version`.


## Structured AI analysis

- Provider-neutral structured document context schema is implemented.
- Extracted text flows through deterministic Hindi/education hints before provider analysis.
- Gemini is the first configurable adapter, using structured JSON output.
- AI provider/model/key are runtime configuration only; database schema remains vendor-neutral.
- Structured context persists full JSON + concepts + context version, while searchable metadata is projected into `letters`.
