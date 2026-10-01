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
- No live document ingestion, OCR/AI processing, or production deployment has occurred.

## Next step

Establish an authenticated archive owner for RLS-backed writes, then implement the private storage/database repository adapter using synthetic fixtures before any live-letter ingestion.
