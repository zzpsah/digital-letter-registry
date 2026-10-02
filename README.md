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


## Preferred login experience

DLR prefers **Google Sign-In** for the archive user when the Supabase Google provider is configured. Passwordless email/Magic Link remains a fallback and recovery path.

A successful sign-in establishes the same server-managed Supabase session/RLS identity used by the existing application. The refresh session persists for 30 days by default (subject to Supabase revocation/session policy), so normal browser restarts should not require a fresh email link every time.

Google Sign-In credentials are separate from Google Drive OAuth credentials. Browser login requires its own Google **Web application** OAuth client.


## DLR accounts and roles

DLR authorization is archive-membership based, not Gmail/provider based.

- Any valid email provider can be used for a DLR account (Gmail is not required).
- Primary native login is email + password.
- Magic Link remains a passwordless/recovery option.
- Google Sign-In is optional and maps into the same Supabase user/membership model when enabled.
- Registration is **invite-only**. Creating a Supabase Auth user does not by itself grant archive access.
- Roles are:
  - `admin`: manage members/invites and administrative archive operations;
  - `editor`: read/search and add/update archive content;
  - `viewer`: read/search only.
- The initial archive owner is the bootstrap admin. Additional dedicated admins can be invited using any valid email address.
- Database RLS enforces archive membership and role boundaries; authorization is not based on email domain or user-editable metadata.
- The database prevents disabling/demoting/removing the final active admin.
- Invite links keep the invite code in the URL fragment (`#invite=...`) so the code is not sent in normal HTTP request URLs/referrers; the browser clears it after prefill.

Google Drive OAuth remains a separate backend storage authorization system and is not tied to the user's login provider.


## Password setup and recovery

Authenticated archive members can set or change their DLR password from the Account section. The password is sent directly to Supabase Auth over the authenticated session; DLR does not persist or log it.

Practical flow:
1. Sign in using an existing valid method (for the bootstrap admin, Magic Link works now).
2. Open the Account section.
3. Set a new password (minimum 8 characters enforced by DLR).
4. Future logins can use email + password from any computer that can reach the private DLR app.
5. Magic Link remains available as passwordless recovery.

This does not change archive roles or Google Drive permissions.


## Vercel deployment

The DLR web/auth/search control plane is now deployed on Vercel:

`https://digital-letter-registry.vercel.app`

Verified production behavior:
- home page returns HTTP 200;
- `/api/v1/health` returns HTTP 200;
- auth provider discovery returns password + Magic Link with invite-only registration;
- Vercel Authentication protection is disabled so DLR's own Supabase authentication is the user-facing gate;
- real intake remains disabled on the Vercel deployment.

The current Vercel deployment does not receive the private Google Drive OAuth credentials. Original-file streaming, Drive writes, OCR/system-binary processing, and other private-worker responsibilities remain on the Oracle deployment until explicitly migrated.

Supabase's Auth redirect allow-list still needs the Vercel origin before Magic Link callbacks should be treated as fully portable to the public Vercel URL.
