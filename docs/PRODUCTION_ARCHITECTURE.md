# DLR Production Architecture

Status: Canonical
Scope: Digital Letter Registry (DLR)
Design horizon: multi-year / long-lived school archive

## 1. Purpose

DLR is a durable official-document intelligence registry for school administration. It must remain searchable, auditable, and upgradeable for many years even when OCR engines, AI providers, filenames, categories, search models, delivery channels, or storage implementations change.

The system is not merely an email bot or file organizer. It is a document system of record with immutable originals and regenerable intelligence.

## 2. Non-negotiable invariants

1. The original document bytes are immutable.
2. A cryptographic content hash is the canonical identity for exact duplicate detection.
3. Every external intake event has independent provenance.
4. Derived OCR, AI interpretation, tags, embeddings, titles, filenames, summaries, and delivery messages are versioned and replaceable.
5. The original document is always authoritative for exact wording, amounts, dates, signatures, reference numbers, and legal/administrative meaning.
6. No AI-generated field may silently overwrite source evidence.
7. Reprocessing must never duplicate the original document.
8. Reprocessing must be idempotent and auditable.
9. Delivery is downstream of the registry; email/WhatsApp must never become the only record of a document.
10. Search metadata must remain useful even if a later AI/provider is unavailable.
11. All secrets remain outside repository content and user-visible metadata.
12. Schema evolution happens through migrations only. No ad-hoc live-table changes.

## 3. Stable domain identity

### Document
A logical official document represented by one immutable original file.

Stable identity:
- letter_id (UUID)
- owner/archive scope
- original_sha256
- original_filename
- durable private storage reference
- original MIME type and byte size
- first-seen timestamp

### Source / provenance
One occurrence of the document entering the system.

Examples:
- WhatsApp message
- email attachment
- manual upload
- watched folder
- historical import

A single document may have many source events.

### Revision / related document
A changed official file is a new Document, not a mutation of the old Document.

Relationships:
- duplicate_of
- supersedes
- corrects
- extends
- related_to

## 4. Data layers

### Layer A — Immutable source

Tables/entities contain facts that must never be regenerated:
- document ID
- SHA-256
- original filename
- MIME type
- byte size
- storage provider/object reference
- first received time
- source events
- source channel/message ID
- original sender/channel metadata when permitted

### Layer B — Extraction artifacts

OCR/native text extraction must be append-versioned rather than treated as permanent truth.

Each extraction artifact should capture:
- artifact ID
- letter ID
- extraction method: native_pdf / tesseract / vision_ocr / other
- engine/provider
- engine version
- language configuration
- raw extracted text
- page count
- page-level text when available
- extraction quality/confidence
- created_at
- processing run ID

Never delete a prior extraction solely because a newer extraction is better.

### Layer C — Interpretation artifacts

AI/context interpretation is derived from a specific extraction or direct document vision pass.

Each interpretation should capture:
- interpretation ID
- letter ID
- source extraction artifact ID when applicable
- provider
- model
- prompt/schema version
- output language
- structured JSON result
- confidence
- created_at
- processing run ID
- whether current/preferred

Structured result includes, where supported:
- title
- document type/category/subcategory
- authority/issuer
- subject
- reference/memo number
- issue date
- effective date
- deadline
- action required
- human-readable summary
- key points
- important dates
- concepts
- search aliases
- uncertainty flags

### Layer D — Current projection

The existing `letters` and `letter_processing` records serve as fast current projections for search/UI.

They are not the historical truth of processing.

A projection can be rebuilt from immutable source + versioned artifacts.

### Layer E — Search index

Search should combine:
1. human title / smart filename
2. authoritative metadata
3. aliases/tags
4. full OCR/native text
5. semantic chunks/embeddings
6. source/provenance metadata
7. relationship graph

Search index content is disposable and rebuildable.

### Layer F — Delivery

Email and WhatsApp are delivery records, not document identity.

Every outbound delivery should have a normalized record:
- delivery ID
- letter ID
- source ID
- channel
- destination
- template/version
- content version / interpretation ID
- status
- provider message ID
- attempts
- error
- created/sent timestamps
- supersedes/corrects delivery ID when applicable

This replaces long-term dependence on nested JSON flags inside source metadata.

## 5. Processing run model

Every processing attempt should have a first-class run identity.

A processing run records:
- run_id
- letter_id
- trigger/reason
- processor profile
- extraction target/version
- interpretation provider/model
- dictionary/taxonomy versions
- started/completed timestamps
- status
- failure stage/error
- input artifact IDs
- output artifact IDs

Reasons may include:
- initial_processing
- manual_reprocess
- ocr_upgrade
- ai_upgrade
- taxonomy_upgrade
- filename_rule_upgrade
- embedding_upgrade
- correction

A run must never destroy prior run outputs.

## 6. Provider architecture

### Primary document understanding
Supabase `gemini-ai-gateway` is the current primary Gemini path.

Benefits:
- Gemini secret stays server-side
- Oracle VPS does not need the primary Gemini key
- provider can change without changing domain records

### Future provider order

1. Supabase Gemini gateway
2. Oracle-side direct Gemini fallback key in secure secret storage
3. deterministic extraction/category fallback

Local Hermes/Ollama may be used for optional enrichment or offline experiments, but is not a synchronous production dependency on the current Oracle A1 VPS.

Provider selection is runtime configuration, never embedded into document identity.

## 7. PDF/image understanding policy

For scanned government documents:

1. Preserve original file.
2. Try native embedded text.
3. Run Hindi/English OCR for searchable archival text.
4. For interpretation quality, use document/image vision when OCR confidence is poor or layout is table-heavy.
5. AI receives either:
   - original PDF/image directly, or
   - rendered page images, plus OCR text as supporting evidence.
6. Human-readable summary is generated from document understanding, not by simply truncating raw OCR.
7. Full OCR remains stored and searchable even when imperfect.

## 8. Email contract

Email is an archival human-readable delivery.

Subject:
- DLR marker
- meaningful category
- human-readable title
- reference number/date when known
- never raw generated filename as the primary subject

Body order:
1. document identity
2. human-readable summary
3. key points / required action
4. reference/date/authority
5. archive references
6. searchable tags
7. full OCR transcript clearly marked as archival/search copy
8. original attachment

Hindi is preferred for Hindi official documents.
The full OCR may be imperfect; it must not be presented as the human-readable summary.

## 9. WhatsApp contract

WhatsApp is a compact search/retrieval receipt.

Include:
- short human title
- Roman-English/Hinglish summary
- reference/date/authority when known
- searchable tags
- Drive/DLR link
- explicit email-delivery confirmation

Do not paste the full OCR into WhatsApp.

## 10. Metadata taxonomy

Free-text categories are not sufficient long-term.

Canonical category codes should be stable and language-neutral, for example:
- fee
- admission
- registration
- examination
- scholarship
- udise
- apar
- eshikshakosh
- finance
- service
- infrastructure
- training
- legal
- affidavit
- declaration
- notice
- circular
- order
- other

Display labels can be Hindi/English and may change without changing the category code.

Tags are additive search helpers, not schema.

Important identifiers should use dedicated fields rather than only hashtags:
- memo/reference number
- issue date
- issuer
- department
- academic session
- class/grade when relevant
- scheme/system identifier
- deadline/action state

## 11. Duplicate and version policy

### Exact duplicate
Same SHA-256:
- reuse existing document
- add a new source/provenance event
- do not resend duplicate archival email unless policy explicitly requests it
- return existing DLR/Drive reference

### Near duplicate
Different hash but strong metadata similarity:
- create candidate relationship
- do not silently merge
- ask/record Same document vs New version where interaction is possible

### Revised/corrected official document
New bytes = new document ID.
Link with `supersedes` or `corrects`.

## 12. Auditability

Long-lived systems need an append-only audit trail for significant actions:
- intake accepted/rejected
- exact duplicate linked
- processing run started/completed/failed
- preferred artifact changed
- metadata manually edited
- relationship approved/rejected
- document status changed
- email/WhatsApp sent/failed
- reprocessing requested

Audit events must not contain secrets.

## 13. Retention and deletion

Default:
- originals retained indefinitely
- provenance retained indefinitely
- processing artifacts retained unless an explicit retention policy is later adopted
- search indexes/embeddings may be regenerated
- temporary staging files may be deleted after verified archival

Deletion must be explicit, auditable, and separate from ordinary reprocessing.

## 14. Backup and recovery

Minimum long-term recovery requirement:
- original documents exist in durable private storage
- database schema/migrations are in Git
- Supabase metadata has scheduled backup/export strategy
- secrets have independent recovery path
- a disaster-recovery document explains how to rebuild current projections/search indexes from originals + metadata

Oracle VPS must never be the sole durable copy.

## 15. Schema evolution strategy

No destructive redesign in one migration.

Phase 1 — preserve current live behavior
- keep current `letters`, `letter_processing`, jobs, sources and relationships
- introduce versioned artifact/run/delivery/audit tables alongside them

Phase 2 — dual write
- processing writes current projection + immutable artifacts
- delivery writes normalized delivery rows + existing compatibility metadata

Phase 3 — backfill
- create historical artifact/run records for existing documents where possible

Phase 4 — switch reads
- UI/search uses current projection backed by version history

Phase 5 — retire compatibility fields only after verified migration

## 16. Required future tables

Recommended additive tables:
- document_files or immutable_file_metadata extension
- processing_runs
- extraction_artifacts
- interpretation_artifacts
- document_tags / tag_dictionary
- deliveries
- audit_events
- optional manual_reviews

These should be owner/archive scoped, indexed, RLS protected, and created by migrations.

## 17. Operational SLOs

Targets, not guarantees:
- intake acknowledgement should not depend on AI completion
- original archival should complete before derived delivery
- AI failure must not lose the original
- repeated jobs must be safe
- a failed delivery can be retried without reprocessing the document
- an AI/model upgrade can reprocess historical documents without changing original identity

## 18. Definition of production-grade

A feature is production-grade only when:
- its data ownership and lifecycle are defined
- retries are idempotent
- failure state is persisted
- secrets are isolated
- schema changes are migrated
- behavior is versioned
- logs are useful but do not expose sensitive values
- tests cover normal, duplicate, retry, provider-failure and reprocessing cases
- documentation states how it can evolve without breaking old records

## Near-duplicate and revised-document detection

- Exact SHA-256 matches remain the only automatic duplicate identity rule.
- Processed documents are also compared conservatively using reference number, authority, category, title and summary similarity.
- Same reference + very high similarity creates a reviewable `duplicate_of` suggestion.
- Same reference + meaningful content differences creates a reviewable `related_to` suggestion labelled as a possible revised/versioned document.
- Without a reference number, a duplicate suggestion requires the same authority/category plus very high title and summary similarity.
- Explicit corrigendum/extension/superseding language continues to take priority over fuzzy similarity rules.
- Near-duplicate/version suggestions never delete, merge, supersede, or alter originals automatically. Human review is required.

## Autonomous OCR correction learning

- The OCR layer maintains a private runtime correction memory outside Git.
- High-confidence AI-cleaned text can create correction candidates automatically; users are not prompted for verification.
- Known education/government vocabulary corrections auto-promote after 3 independent documents; unknown general terms require 5 independent documents.
- Learning requires context confidence >= 0.90.
- Numbers, dates, amounts, codes and reference-number tokens are excluded from automatic correction learning.
- Promoted corrections are applied only to derived analysis text. Raw OCR and immutable originals are never rewritten.
- The memory is reversible and versioned by an internal revision counter; deleting/resetting the runtime memory restores baseline behavior.

### Autonomous learning operational contract

Implementation: `src/letter_registry/autonomous_learning.py`, class `AutonomousCorrectionMemory`.

The learning loop is:

`raw OCR -> promoted correction application -> document analysis -> high-confidence clean text -> correction observation -> candidate accumulation -> automatic promotion`

Promotion policy:
- minimum context confidence: 0.90;
- known vocabulary target: 3 independent documents;
- other target: 5 independent documents;
- one document can contribute at most once to one candidate;
- token similarity must be sufficiently close to represent an OCR-style correction rather than semantic rewriting;
- any source or target token containing digits is rejected from autonomous learning.

Persistence:
- default file: `/home/prashant/.hermes/state/dlr-learning/ocr-corrections.json`;
- override: `DLR_OCR_LEARNING_FILE`;
- permissions: private runtime directory/file;
- data: schema version, internal revision, candidates, promoted rules, document evidence and average confidence;
- this file is intentionally excluded from Git.

Application boundary:
- promoted corrections are applied to analysis text before context extraction;
- original file bytes remain authoritative;
- stored raw OCR remains untouched;
- learned corrections must not silently alter dates, money, percentages, IDs, codes or reference numbers;
- deleting/resetting the correction-memory file is a complete rollback of learned behavior.

Dictionary/version registry uses `gov-education-hi-en-auto-v2` so historical documents can later be selected for controlled reprocessing when dictionary behavior changes.

## Automatic document quality scoring

- Every processed document receives a non-blocking quality score from OCR readability, context confidence, core metadata completeness, reference/date presence and availability of cleaned text.
- Scores below 0.72 set needs_reprocessing=true with quality flags; delivery still proceeds.
- Quality metadata is stored inside structured_context to avoid a schema migration during trial.
- Current quality engine version: document-quality-v1.
- Low-quality results are eligible for later better-provider reprocessing; originals/raw OCR remain unchanged.

## Automatic quality recovery

Low-quality processing results are eligible for automatic reprocessing without user intervention.

Implementation:
- scanner: `src/letter_registry/self_healing.py`;
- worker hook: `scripts/run_worker_once.py`;
- source flag: `structured_context.needs_reprocessing=true`;
- quality engine: `document-quality-v1`.

Scheduling policy:
- if the currently configured context provider is higher-tier than the provider that produced the stored result, the document is eligible for recovery;
- provider order is Gemini > Hermes > deterministic/unknown;
- a real context-model version change, dictionary-version change, or quality-engine version change creates a stable one-time upgrade job;
- when a higher-tier provider is configured but temporarily unavailable and processing falls back to a lower tier, the same low-quality document receives at most one recovery attempt per UTC day;
- job reasons are deterministic and use target-version hashes so repeated worker ticks remain idempotent;
- the normal durable processing queue is reused; originals are never duplicated.

Delivery behavior:
- low-quality results are still archived and delivered;
- a later successful reprocessing pass updates only derived projections/artifacts;
- if delivery content materially improves, the existing same-thread revision mechanism handles the follow-up;
- unchanged derived content does not generate another email.

This is trial/staging behavior. It is designed to recover automatically from temporary model quota/outage conditions without creating a reprocessing storm.

## Google Drive visible smart filenames

- Archived Drive objects may have their visible filename updated to the contextual smart filename after successful processing.
- The Drive file ID and file bytes remain unchanged.
- `letters.original_filename` remains immutable provenance and is never replaced by the Drive display name.
- Rename is idempotent and uses the existing private Drive OAuth transport.


## Controlled automatic self-healing reprocessing

- Low-quality results marked with `needs_reprocessing=true` are eligible for automatic recovery when a better/current AI provider is configured.
- Provider quality tiers are ordered conservatively: Gemini > Hermes > deterministic.
- A lower-tier low-quality result can receive a daily recovery job targeting the preferred provider.
- Same-target low-quality results are not retried continuously; they wait for a provider/model, dictionary, or quality-engine version change.
- Automatic reprocessing is gated to AI-enabled runtime (Gemini gateway or direct Gemini key).
- Daily automatic enqueue volume is capped by `DLR_AUTO_REPROCESS_DAILY_LIMIT` (default 5) to prevent quota stampedes.
- Job reasons include the target signature and, for provider recovery, a UTC day bucket, preserving idempotency and auditability.
- Reprocessing never mutates immutable originals; only derived projections/artifacts may improve.

## Bounded self-healing reprocessing

- Low-quality documents marked `needs_reprocessing=true` are eligible for automatic reprocessing only when an AI/Gemini path is configured.
- Reprocessing is provider/version aware: a document is retried when a higher provider tier, a new model/context version, a new dictionary version, or a new quality-engine version becomes available.
- A result already produced by the current target context/dictionary/quality versions is not requeued, preventing infinite loops.
- Recovery retries against a higher provider are day-bucketed and globally bounded by `DLR_AUTO_REPROCESS_DAILY_LIMIT` (default 5).
- Existing same-day recovery jobs count toward the cap; repeated worker scans cannot enqueue another batch every minute.
- Version-upgrade jobs are also pressure-bounded by the same configured limit while matching upgrade jobs are pending/processing.
- Reprocessing changes only derived artifacts/projections. Immutable originals and source provenance remain unchanged.
