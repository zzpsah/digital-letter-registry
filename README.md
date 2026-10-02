# Digital Letter Registry

Formal archive name: **Official Letter Intelligence Archive**

A private, Hindi-first, mobile-friendly searchable memory for official school and government letters.

## Core problem

Important PDFs/images often arrive with useless names such as `DOC10086.pdf`. Months or years later the user usually remembers only the meaning — for example `inter exam last date`, `UDISE PEN correction`, or `registration extension` — not the memo number, exact date, or filename.

## Product goal

```text
Upload / Forward
      ↓
Preserve original
      ↓
Extract text / rough OCR
      ↓
Understand Hindi government-letter context
      ↓
Generate smart filename + structured metadata
      ↓
Index filename + full text + semantic meaning
      ↓
Search later in normal Hindi / English / Hinglish
      ↓
Open or download the original
```

## Official archive filename convention

Derived archive filenames use:

```text
short-title__issuer__date__reference-number.ext
```

Examples:

```text
scholarship-guidelines__education-department__2026-10-01__REF-001.pdf
छात्रवृत्ति-निर्देश__शिक्षा-विभाग__2026-10-01__REF-001.pdf
inter-exam-schedule__education-department__undated__no-ref.pdf
```

Rules:

- `short-title`: short, clear meaning of the letter.
- `issuer`: issuing department/institution.
- `date`: `YYYY-MM-DD`; if unknown use `undated`.
- `reference-number`: official reference/memo number; if unknown use `no-ref`.
- Separate the four fields with double underscores: `__`.
- Preserve the original file extension.
- Hindi, English, and Hinglish titles/issuers are valid.
- The original uploaded file remains immutable; the smart filename is derived presentation metadata.
- Existing Drive files must never be renamed in bulk before a preview mapping is reviewed and explicitly approved.

See `docs/NAMING-SPEC.md` for the detailed contract.

## Non-negotiable architecture

- Original PDF/image is immutable and authoritative.
- OCR, title, filename, category, summary, embeddings, status, and relationships are derived/versioned data.
- Derived data must be recursively reprocessable for the entire archive.
- Search must combine filename, metadata/full text, and semantic/context search.
- Smart filenames should remain useful even outside the custom web app.
- Hindi government/education terminology and document structure must be first-class.
- AI provider must be replaceable; no permanent lock-in to one vendor/model.
- Originals and private archive data stay outside public Git.
- The public repository must not contain real letters, private Drive IDs/URLs, API keys, Supabase credentials, SSH keys, or server details.

## Planned user experience

The main interface is one search box plus optional filters such as date/year, authority, category, file type, and current/historical status. Results show a short context preview and always provide **Open Original** / **Download Original**.

## Status

The private archive folder structure and a separate Supabase archive database are established. The database and Drive archive are currently empty of real archive records. Refreshable Google Drive OAuth is verified with runtime secret-manager injection, including live originals listing, server-side streaming, and a disposable synthetic upload/stream/delete write test; a protected file credential remains supported only as a local/migration fallback. No public production deployment or live document migration is authorized yet.

See:
- `PRD.md`
- `docs/PROJECT-HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/NAMING-SPEC.md`
- `docs/SECURITY.md`
- `TASKS.md`

## Workflow

`READ → UNDERSTAND → PLAN → IMPLEMENT → TEST → REVIEW → FIX → COMMIT → UPDATE DOCUMENTATION`


## Google Drive account model

- DLR source code is not tied to one Google account.
- A deployment connects to an explicitly authorized Google Drive account through OAuth and uses configured private archive folder references.
- The current private deployment is single-archive-owner configured; another account requires its own OAuth consent, secret-manager credentials, and archive-folder configuration. Depending on the Google OAuth consent-screen status, a new account may also need to be an allowed test user before authorization succeeds.
- The verified private runtime uses a write-capable Google Drive OAuth grant for direct Drive API operations. The OAuth permission is broader than the application's intended archive boundary, so DLR must operate only on configured archive objects and preserve separate approval gates for real mutations.
- Do not reuse unrelated Drive/rclone credentials between deployments or projects.


## Authentication scope

DLR uses passwordless email login (commonly called a Magic Link) to establish the identity of the person using the private application.

Its scope is deliberately narrow:

- **Identity/session:** prove which authorized user is using DLR and create the authenticated browser session.
- **Database authorization:** Supabase RLS uses that authenticated user identity to decide which archive rows the user may read or write.
- **Future multi-user isolation:** different authorized users/schools can share the same application while remaining separated by database ownership/policies.

Magic Link authentication does **not**:

- provide Google Drive access — that is handled separately by server-side Google OAuth;
- replace Tailscale/private-network protection;
- authorize real letter ingestion, rename, delete, historical adoption, or bulk mutation;
- grant access to unrelated users merely because they can reach the DLR URL.

In short: **Tailscale protects how the app is reached; Magic Link identifies the user; Supabase RLS controls that user's database access; Google OAuth controls the backend Drive connection.**
