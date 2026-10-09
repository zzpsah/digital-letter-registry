# Project Handoff — Digital Letter Registry

## Mission

Build a private, mobile-first searchable memory for official school/government PDFs, scans, and images. The user should be able to find the correct historical letter from remembered meaning even when the memo number, exact date, original filename, and exact wording are forgotten.

## User problem

Incoming files commonly have meaningless names such as `DOC10086.pdf`. WhatsApp/file search becomes poor as the archive grows. The user remembers context like:
- “inter exam last date”
- “BSEB form extension”
- “UDISE PEN correction”
- “11th registration”
- “board ne exam form bharne ka date badhaya tha”

## Required experience

```text
Receive PDF/Image
      ↓
Forward or upload
      ↓
Original saved privately
      ↓
Embedded text extraction or rough Hindi/English OCR
      ↓
Government-letter vocabulary + structure
      ↓
One replaceable AI model derives context
      ↓
Smart human-readable filename generated
      ↓
Metadata/full text/semantic indexes updated
      ↓
Later: search by normal language or filters
      ↓
See short context and open/download original
```

## Accuracy philosophy

Perfect OCR is not the goal. OCR needs to recover enough signal for search/context. AI may infer likely meaning from broken OCR using surrounding language, repeated administrative phrases, and known education terminology. Exact dates, memo numbers, amounts, names, and legal wording must be verified from the original document.

## Hindi/government understanding

Maintain a configurable domain vocabulary linking variants such as:
- पंजीयन / पंजीकरण / registration
- परीक्षा प्रपत्र / exam form
- अंतिम तिथि / deadline / last date
- तिथि विस्तार / अवधि विस्तार / extension
- अनुपालन / required action
- आदेशानुसार, उपर्युक्त विषयक, आवश्यक कार्रवाई, तत्काल प्रभाव से

Include BSEB, UDISE+, PEN, APAAR, eShikshaKosh, Matric, Intermediate, registration, examination, practical, fee, scholarship, correction, verification, DEO/DPO/headmaster, etc.

## Smart filename

Official derived filename pattern:

`short-title__issuer__date__reference-number.ext`

Rules:
- keep original filename in metadata,
- preserve the original extension,
- keep generated title/issuer short and normalized,
- use `YYYY-MM-DD` for a confident date, otherwise `undated`,
- use the official memo/reference number when confidently present, otherwise `no-ref`,
- separate the four fields with double underscores,
- preserve Hindi/English/Hinglish Unicode,
- keep the original immutable,
- treat the smart filename as derived/versioned data that can be regenerated,
- never bulk-rename existing Drive files without preview + explicit approval.

See `docs/NAMING-SPEC.md` for the canonical filename contract.

## Search

Combine:
1. smart filename/title,
2. metadata + full extracted/OCR text,
3. semantic/context similarity,
4. optional filters: date/year, authority/department, category, file type, validity/status.

## Validity

Support: `Current`, `Expired`, `Historical`, `Superseded`, `Unknown`.

Later corrections/extensions/cancellations should link to earlier letters. Old records are retained.

## Recursive upgrade requirement

Every derived layer must record versions:
- OCR/text extractor
- context prompt/schema/model
- Hindi dictionary
- filename rules
- category schema
- embedding model
- status/relationship rules

A future admin job must support preview + reprocessing of selected/all historical records without duplicating or replacing originals.

## Recommended initial stack

- FastAPI/Python
- PostgreSQL + full-text search
- pgvector
- Redis + queue worker
- PyMuPDF/pypdf
- Tesseract/OCRmyPDF
- replaceable AI adapter
- durable private object/file storage
- responsive web/PWA

## AI strategy

Use one primary model/provider at a time. The application speaks only to an internal adapter. If a free provider disappears, change the adapter/model and reprocess historical derived data. The archive must continue working even while AI processing is temporarily unavailable.

## Security

Public Git contains only code/docs/synthetic fixtures. Real letters, extracted private text, identifiers, keys, tokens, and storage credentials never enter Git.

## Server path already available

The broader environment already has an authorized private administration path through Desktop Commander on Windows and a local Python/Paramiko SSH helper to the Oracle VPS over Tailscale/private VPN. Do not copy private host/key details into this repository.

## Development order

1. Storage + immutable original + hash/record ID.
2. Text extraction/OCR.
3. Structured context + domain dictionary.
4. Smart filename.
5. Full-text + semantic search.
6. Mobile web/PWA with filters and original link.
7. Related/superseded logic.
8. Recursive reprocessing.
9. Historical bulk migration.
10. Extra intake channels.

## Current boundary

The public Vercel control plane is deployed and reachable. Real archive import/intake remains disabled. Synthetic/private test fixtures are still required before enabling real archive ingestion.


## 2026-10-02 runtime verification checkpoint

- Dedicated refreshable Google Drive OAuth is configured through runtime secret-manager injection; no refresh token/client secret is stored in Git, and the persistent authorized-user runtime file was retired after verification.
- Current private-runtime Drive grant is write-capable; disposable synthetic upload/stream/delete verification passed.
- Live token refresh, originals listing, and server-side streaming of the existing synthetic original are verified.
- Full synthetic test suite passes 212/212.
- Runtime readiness has Supabase, auth callback, Drive credentials/folder, OCR tooling/languages, and synthetic-only safety ready; Gemini is the only failing readiness check.
- Real Supabase owner-session/PostgREST vertical-slice verification remains blocked by the hosted email-send throttle.
- Runtime Drive write/upload verification is complete with a disposable synthetic object; real archive mutation remains separately approval-gated.


## Drive account portability

The codebase is Google-account portable. A deployment uses the Google account that explicitly completes OAuth consent plus that deployment's configured archive-folder references. The current private deployment is single-owner/single-archive configured. A different account requires separate OAuth consent, secret-manager credentials and folder configuration; do not silently reuse or repoint another deployment's credentials.


## Authentication scope

DLR uses Supabase Auth to establish an authenticated archive-user session and supply RLS with the user's identity. Primary login is email + password; self-registration creates a disabled viewer membership until an active DLR admin approves the account. Magic Link remains legacy/recovery backend compatibility rather than the primary user flow.

Scope:
- authenticate the browser user;
- create/refresh the private DLR session using HttpOnly cookies;
- allow Supabase RLS to enforce owner-scoped database access;
- support future multi-user or multi-school isolation without redesigning the auth layer.

Out of scope:
- Google Drive authorization (handled by backend Google OAuth);
- Tailscale/private-network transport;
- automatic approval of real uploads, renames, deletes, historical imports, or other consequential archive mutations.

Authentication proves identity; it does not itself authorize every action.


## Preferred login UX

Primary target: **Sign in with Google** through Supabase Auth. Magic Link remains a fallback. The existing archive-owner email identity should be automatically linked to the verified Google identity with the same email, preserving the existing Supabase user id and RLS ownership. After authentication, DLR uses HttpOnly access/refresh cookies; the refresh cookie persists for 30 days by default.

This user-auth OAuth client is separate from the backend Google Drive OAuth client.


## DLR account / role model

DLR is no longer a Gmail-specific or single-owner authorization design. Authentication provider and archive authorization are separate.

- A user may authenticate using email/password, Magic Link, optional Google Sign-In, or future compatible providers.
- Archive access requires an active row in `archive_members`.
- Roles: `admin`, `editor`, `viewer`.
- New-account registration is invite-only.
- A raw Supabase Auth account without membership has no archive access.
- The current bootstrap owner remains the initial active admin.
- Additional dedicated admins can use any valid email provider.
- Database RLS is archive/role-aware and the final active admin is protected against removal/demotion/disablement.
- Invite codes are carried in URL fragments rather than query strings and are cleared after client-side prefill.
- Backend Google Drive OAuth is separate from user authentication.

Hosted state was verified on 2026-10-02: one active admin, no disabled members, no pending invites, no real archive-letter rows. Full synthetic suite: 249/249.


## Multi-role runtime verification

Hosted Supabase role behavior was verified on 2026-10-02 using synthetic JWT-claim simulation:
- viewer read-only;
- editor read/insert/update but not delete;
- non-member no archive read/insert;
- admin delete allowed.

Synthetic users/rows/memberships were removed and zero residue was confirmed. Pending invites can now be onboarded with one click by sending the existing invite-validated registration Magic Link, while copy links retain invite codes only in URL fragments.

The remaining auth proof is a real short-lived browser/email owner session against PostgREST; Magic Link delivery is working, but that final bearer-session completion is not yet marked complete.


## Password setup handoff

The private DLR runtime now supports member-controlled password setup/change. A currently authenticated archive member may set a password through the Account UI; the backend forwards it to the authenticated Supabase Auth user endpoint and does not store it.

This allows the bootstrap admin to use one Magic Link once, set a password, and then use ordinary email/password login on future computers. Magic Link remains recovery.

Live verification:
- Account UI deployed;
- unauthenticated password-change request returns 401;
- full synthetic suite 255/255;
- on 2026-10-03, the bootstrap admin successfully updated the password through the live DLR Account flow. The password itself is not stored in project documentation.


## Vercel hosting checkpoint

Canonical production URL: `https://eletters.vercel.app`.

As of 2026-10-10, production routes were verified over HTTPS:
- `/` — public UMV Storage Automation / eLetters product-information homepage;
- `/app` — eLetters sign-in/application UI;
- `/privacy-policy` — public privacy policy;
- `/api/v1/health` — health endpoint.

All four routes returned HTTP 200. The public homepage was introduced in commit `025c752c0726992c0c3d4bef67c561a1c4d2b614` to make the service purpose, document use, privacy link, and app sign-in link publicly discoverable for OAuth homepage-information review. This does not by itself mean Google has approved the OAuth app.

Architecture:
- Vercel: public product homepage, browser UI, auth/session endpoints, search/admin control plane;
- Supabase: Auth, RLS and archive data authorization;
- Oracle/private runtime: Google Drive OAuth/original access, OCR/system binaries, and private-worker responsibilities;
- the Vercel deployment does not hold private Drive upload credentials; preserve its real-intake safety gate.

Vercel Authentication is disabled because DLR enforces Supabase-backed identity and archive membership itself.

Portability follow-ups to verify before enabling or relying on them:
- optional Magic Link or Google Sign-In flows need the Vercel origin configured in Supabase Auth redirects;
- verify Vercel automatic-deployment status independently before assuming a Git push has deployed;
- any proposal to move Drive/original-access operations off Oracle requires an explicit architecture and security decision.


## Deterministic processing fallback

Oracle processing no longer depends on Gemini availability for baseline functionality.

When `GEMINI_API_KEY` is absent:
- OCR/native text extraction still runs;
- checked-in vocabulary produces conservative structured hints;
- full-text/metadata search remains available;
- semantic embeddings are skipped and remain eligible for later reprocessing;
- exact dates, reference numbers, deadlines and actions are never invented by the fallback.

The scoped Oracle runtime currently reports ready with Supabase, auth callback, Drive OAuth, originals folder, Tesseract, OCRmyPDF, Hindi/English OCR languages, and synthetic-only safety all available. Gemini is optional. Full tests: 261/261.


## 2026-10-03 baseline completion

Core DLR baseline is verified live. Password-first multi-user auth is live on the canonical Vercel control plane; the dedicated Bitwarden-backed Oracle worker is active; real short-lived bearer/PostgREST insert/read + RLS denial passed; authenticated HTTP synthetic intake → private Drive → durable queue → worker → search → original streaming passed; original bytes matched; and cleanup returned the archive to zero letters/jobs/processing rows. The pending-membership signup trigger is now captured in a repository migration. Full Oracle synthetic suite: 269/269. Real archive intake remains disabled.

Remaining items are future enhancements or external hardening, not baseline blockers: Google Sign-In, Supabase leaked-password protection, optional Vercel Auth redirect/auto-deploy portability, Gemini semantic enrichment, and live messaging/watched-folder connectors.


## 2026-10-03 controlled real-letter pilot

Private Oracle DLR is now pilot-enabled for manual real official-letter intake with a hard two-letter cap. Public Vercel remains synthetic-only for intake and holds no Drive upload credentials. Authenticated capability checks verified 2/2 private pilot slots remaining; worker is healthy and timer active; archive is empty before first real upload. Full suite passes 275/275. Next action is user-side manual upload of the first selected real official letter through the private Oracle UI, followed by review before the second slot is used.

Pilot safety update: the second slot is locked by default. After the first real letter is ingested, the API rejects another real-looking upload until review is complete and the runtime slot-two unlock is explicitly enabled. Current zero-letter capability state: pilot active, 2 remaining, not review-locked yet.


## 2026-10-03 first real-letter pilot verification

The first real official PDF was ingested through the private Oracle pilot and successfully processed after live fixes to dedicated-worker job claiming and OCR fallback. Human document ownership is preserved while the dedicated worker is recorded separately as the claimant. PDFs with garbled private-use embedded-font text now fall back to forced OCR; the configured user-local Tesseract path is propagated to OCRmyPDF. The first real document now has deterministic structured metadata/smart filename, is searchable, and its private original streams successfully. The second pilot slot is review-locked with one slot remaining. Full suite: 280/280. Do not copy real OCR text or private identifiers into Git/docs.


## 2026-10-03 two-letter pilot completion

The private Oracle real-intake pilot has successfully processed two distinct real official PDFs. Both completed through the dedicated worker, were searchable, and streamed from private original storage. The two files exercised different extraction paths (forced OCR for broken embedded-font text and native PDF extraction). The configured hard cap is now reached with zero remaining real-intake slots, so no further real upload should be accepted until the next phase is explicitly chosen. Real content/identifiers remain excluded from Git/docs.


## 2026-10-03 WhatsApp EDU- Letters connector

A private dedicated WhatsApp archive group is live on the existing Hermes session and is bound to the DLR connector. Only supported document/image attachments from that exact group are staged; ordinary text is silently skipped and other groups are ignored. A protected local queue and one-minute systemd consumer feed the canonical DLR WhatsApp intake using the dedicated worker identity and Bitwarden-backed credentials. WhatsApp message provenance is retained for deduplication. The connector has a separate real-intake cap of 20 documents; the completed manual two-letter pilot cap remains unchanged. Synthetic E2E verification passed and disposable test data was cleaned. Exact group/member identifiers remain private runtime state.


## 2026-10-03 WhatsApp → DLR connector

A private Oracle WhatsApp-to-DLR connector is active using the existing Hermes WhatsApp session. One exact private source group is bound at runtime; only PDF/JPG/JPEG/PNG attachments are staged. The bridge writes a protected message-ID keyed inbox, and an active 60-second systemd timer invokes the existing Bitwarden-backed WhatsApp intake wrapper. Provenance/deduplication are retained in DLR. A synthetic end-to-end connector test passed queue, worker, search, original streaming, duplicate-message rejection and cleanup. Connector real intake is bounded to 100 WhatsApp source messages. Public Git intentionally omits group IDs, phone numbers and session details. First genuine inbound member-post remains to be observed.


The WhatsApp connector has now also passed a genuine WhatsApp-source official circular proof using a public CBSE PDF. The document processed successfully, and a real classification-quality issue discovered during review was fixed: explicit CBSE affiliation evidence now outranks generic UDISE mentions. Search and private original streaming passed after reprocessing. Full suite: 281/281.
## Canonical architecture reference

For all future DLR development, schema changes, AI integration, reprocessing, delivery, duplicate handling, and retention decisions, treat docs/PRODUCTION_ARCHITECTURE.md as the canonical long-term design contract. Do not introduce a new persistent field/table/workflow that conflicts with that document without updating the architecture decision first.

## 2026-10-04 autonomous OCR correction learning

DLR now has an autonomous, reversible OCR correction-memory layer. It does not ask the user to approve individual spelling corrections. The engine compares raw OCR with high-confidence AI-cleaned document text and learns repeated token-level OCR corrections across independent documents.

Operational rules:
- learning requires structured-context confidence >= 0.90;
- a correction targeting known Bihar/education/government vocabulary auto-promotes after 3 independent documents;
- an unknown/general correction auto-promotes after 5 independent documents;
- repeated observations from the same document do not count as independent evidence;
- tokens containing digits are excluded, so dates, amounts, codes and reference-number values are not learned/replaced automatically;
- learned corrections affect only derived analysis input; raw OCR and immutable Drive originals are never rewritten;
- learning memory is private runtime state, not Git content;
- default runtime state file: /home/prashant/.hermes/state/dlr-learning/ocr-corrections.json;
- the state keeps candidate corrections, promoted corrections, independent-document evidence, average confidence, and an internal revision counter;
- removing/resetting the runtime learning file restores baseline behavior without touching archived originals.

Current dictionary version: gov-education-hi-en-auto-v2.

The worker is wired with AutonomousCorrectionMemory.from_environment(). The path may be overridden with DLR_OCR_LEARNING_FILE. The feature is active for subsequent worker jobs in the current trial/staging flow. Learned document-specific values must never be committed to Git.

## 2026-10-05 control-plane and mobile update

The current eLetters web control plane includes admin-managed account requests and roles, delivery recipients, WhatsApp allowed-user management, and dynamic document categories. The narrow-screen UI was explicitly optimized for compact navigation, single-column filters, mobile-safe 16px form inputs, stacked admin records, horizontally scrollable admin tabs, and thumb-friendly document actions. Desktop behavior remains unchanged.

## Admin dashboard, audit and WhatsApp group control — 2026-10-05

The Admin Console now includes Overview and Audit panes. Mutating account/member/recipient/WhatsApp/category/group operations append archive-scoped audit events where applicable. The audit table is protected by admin-only RLS and grants only SELECT/INSERT to authenticated users subject to that policy. WhatsApp group presentation is managed through the existing Vercel-to-Oracle admin proxy: description is plain text, guide send/pin creates a new message and pins it for 30 days, and the canonical group image can be re-applied.

## Failure and retry control — 2026-10-05

The Admin Operations pane is the supported manual recovery path for failed processing jobs. It reads failed rows from the archive-scoped processing_jobs queue and exposes an explicit Retry action. Retry is guarded to status=failed only, resets claimed/runtime timestamps needed for a fresh worker claim, preserves attempts, and appends an admin audit event including bounded previous-error context. Do not auto-retry all failures from the UI.

## Soft delete and restore — 2026-10-05

Normal Admin removal must remain reversible. Members are disabled/restored through membership status. Recipients carry an is_active state in the private Oracle registry; soft removal disables Email/WhatsApp delivery, clears default-recipient selection when applicable, and keeps the record for restore. Categories use is_active=false for removal and true for restore. Permanent recipient/category deletion remains an explicit secondary action with a stronger confirmation.

## Backup/restore and bulk administration — 2026-10-05

Admin > Backup is the supported configuration portability/recovery path. Export is admin-only and contains no authentication secrets. Restore validates backup format and archive identity, previews intended differences, and writes a private pre-restore snapshot under the Oracle Hermes state backup directory before mutation.

Restore behavior is deliberately conservative for Supabase-managed state: existing members found by user_id have role/status restored; missing historical users are skipped rather than recreated; categories present in the backup are updated or created, while unrelated newer categories are left untouched. The private recipient registry is restored exactly from the backup after validation, the WhatsApp allowlist is replaced with the backed-up allowlist, and the backed-up group description is re-applied when the bridge is available.

Bulk account, recipient, and category actions use the existing guarded per-item APIs so last-admin protection, reversible removal semantics, and audit logging continue to apply.

## Intelligence/category separation — 2026-10-05

Do not let category drive document meaning. Category/subcategory and deterministic hints are routing/search taxonomy; title, summary, action_required, applies_to and whatsapp_summary must be derived from the document's operative content, annexures and repeated evidence. If taxonomy conflicts with the source, the source wins. Delivery formatting also treats category only as a final fallback.

## WhatsApp language contract — 2026-10-05

For every document, keep WhatsApp presentation labels in English. What this is must contain a concise Hindi explanation of the actual document context. Action items must contain concise Hindi instructions grounded in the document; preserve official English terms such as ICT Lab, Smart Class, e-ShikshaKosh, Mark On Duty, portal names and official designations when useful. Do not convert headings themselves to Hindi.

The intelligence providers generate summary_hi and action_required_hi for this purpose. Category/subcategory remains secondary taxonomy.

## Sorting / important-note policy — 2026-10-05

Portal default order is latest-added first (`letters.uploaded_at desc`), not document issue date. Available sort modes are latest, important, issue_date, title and relevance.

Shared letter metadata:
- `letters.is_important`
- `letters.user_comment`
- `letters.important_at`
- `letters.important_by`

Only archive editors/admins may update importance/comment through `PATCH /api/v1/letters/{record_id}/highlight`; existing archive RLS remains the database authorization boundary. The authenticated portal displays the note. Public Drive index may display the `★ Important` highlight but must not expose `user_comment`, because the comment is an internal archive note.


## UI/behavior governance baseline

Before changing eLetters UI or workflows, read `docs/UI-DESIGN-CONTRACT.md` and `brain/ui-governance/`. This is a locked accepted baseline. Preserve the purple compact/mobile design, Hinglish default, Smart Search hybrid fallback, Remember me, admin/recipient controls, file Trash/Restore, Operations Retry/Retire/Delete, and source-grounded display behavior unless the user explicitly asks to change them.
- Search Authority filter is a dynamic dropdown populated from distinct active/non-trashed letter authorities; new authorities appear automatically.

## Authority intelligence contract

Authority is exactly one actual issuing/signing authority, never a concatenation of issuer + recipient + cited offices. The classification hierarchy is **Headmaster/School → BEO (Block Education Officer / प्रखंड शिक्षा पदाधिकारी) → DPO (functional district programme authority such as Establishment) → DEO (one canonical DEO per district) → RDDE (division) → Education Department (state)**.

Canonical authority records store designation, jurisdiction and level. DPO posts may be distinct by function, for example DPO Establishment vs another DPO branch. Raw document authority text stays preserved on the letter, while `canonical_authority_id` links it to the clean authority master. Admin-confirmed aliases are learned permanently; future matching issuer strings auto-map through normalized aliases. Uncertain or multi-office strings remain unmatched for review rather than being force-mapped. Search authority dropdown shows canonical authorities, not every raw spelling variant.

## Delivery quality recovery / duplicate suppression
- Quality engine v2 marks low-context-confidence + no-clean-document-text results for bounded reprocessing even when the aggregate score is above the old threshold.
- Low-quality first-pass results may still be delivered; they are not permanently held.
- Later corrected context should use the existing same-thread correction path.
- Reprocessing must not resend mail merely because AI paraphrased summary/action wording.

## Manual document reprocessing
- Editor/Admin users can request Reprocess from each letter card.
- Reprocess always targets the existing archived original and updates derived OCR/context/summary/authority/action; it must not create a duplicate letter or replace the original file.
- Weak or inaccurate processing output must not be described as a poor PDF unless the source file itself is actually poor.
- Delivery remains idempotent: wording-only changes do not resend; material corrections or real poor-context-to-usable-context improvements use the same Gmail thread / WhatsApp replacement path.

## Manual reprocessing
- Editor/Admin document cards expose a Reprocess action for missing or incorrect derived output even when the original PDF/image is clear.
- Reprocess updates the existing letter's derived processing; it must not create a duplicate letter/original.
- If a processing job for the same letter is already pending or running, another reprocess request is not queued.

## Authority display and editing
- User-facing search/recent/detail views prefer the canonical authority short name (for example `DEO Siwan`, `DPO Establishment, Siwan`) when a canonical mapping exists; raw extracted authority remains preserved in the letter record.
- Admin → Authorities lists active and removed authorities with editable short name, English/Hindi names, hierarchy level, jurisdiction and aliases.
- Remove is soft/deactivate and preserves existing mappings; Restore reactivates it.
- Letter cards show a compact 8-character ID with Copy ID for troubleshooting; normal portal reprocessing does not require the user to know the ID.
- Reprocess requests are single-flight: if the same letter already has a pending/processing job, another active job is not created.
- Direct Gemini extraction uses temperature 0.0; canonical normalization and confidence-preserving identity merge stabilize factual fields. Free-text summaries can still vary slightly, so delivery idempotency ignores wording-only paraphrases.

## Stable document identity and authority display
- Letter cards expose a compact 8-character Document ID pill; tapping/clicking it copies the full UUID for explicit reprocess commands. Portal Reprocess and WhatsApp reply-based Reprocess do not require manually typing the ID.
- User-facing authority uses the canonical `short_name` when a letter is mapped, e.g. `DEO Siwan` or `DPO Establishment, Siwan`; raw issuer text remains preserved in `letters.authority`.
- Admin → Authorities lists active and removed authorities and supports editing short/full names, Hindi name, hierarchy level, jurisdiction and aliases. Remove is soft (`is_active=false`) so existing letter mappings are preserved; Restore re-enables it.
- AI generation temperature is fixed at 0 where supported. During reprocessing, existing title/authority/reference/date are preserved unless incoming evidence is materially stronger, reducing factual drift between runs.

- Admin → Authorities unmatched list is computed null-safely from active letters; records with no `canonical_authority_id` must appear for review instead of being hidden by an invalid equality-to-NULL filter.

## Authority merge and permanent deletion
- Admin → Authorities supports Save/Edit, Remove/Restore, Merge into another canonical authority, and Delete permanently.
- Merge moves all linked letter mappings and aliases to the selected target, updates child-parent references, then deletes the duplicate source authority.
- Permanent Delete removes the authority master; linked letters keep their raw authority text but become unmatched for later review/remapping.
- Authority rows show linked-letter counts before destructive actions.
