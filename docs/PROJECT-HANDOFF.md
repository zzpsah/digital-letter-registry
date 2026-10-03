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

A production DLR control plane is live at `https://digital-letter-registry.vercel.app`.

Architecture at this checkpoint:
- Vercel: browser UI, auth/session endpoints, search/admin control plane;
- Supabase: Auth, RLS and archive data authorization;
- Oracle/private runtime: Google Drive OAuth/original access, OCR/system binaries, and private-worker responsibilities;
- real intake remains disabled on Vercel.

Production verification passed for the home page, health endpoint, and auth provider discovery. Vercel Authentication was disabled because DLR already enforces its own Supabase-backed identity and archive membership.

Remaining portability tasks:
1. add the Vercel production origin to the Supabase Auth redirect allow-list;
2. grant Vercel GitHub integration access if automatic `main` deployments are desired;
3. explicitly decide which Drive/original-access operations, if any, should migrate from Oracle to Vercel.


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
