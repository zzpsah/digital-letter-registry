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

The DLR baseline is complete and live. The database and Drive archive contain no real archive records. Password-first multi-user auth, role-aware RLS, private Drive storage, OCR/context processing, search, original streaming, and the dedicated Oracle worker have all been verified with disposable synthetic data. A real short-lived Supabase bearer session passed insert/read + RLS-denial verification, and the live HTTP intake → Drive → queue → worker → search → original-stream path passed end-to-end. All disposable artifacts were removed afterward. Real document intake/migration remains disabled until explicitly approved.

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

DLR uses Supabase Auth for identity and archive membership for authorization.

- **Primary login:** email + password.
- **Account creation:** self-service email/password registration creates a disabled viewer membership.
- **Approval:** an active DLR admin chooses the role and activates the account.
- **Recovery/legacy:** Magic Link backend compatibility remains, but it is not part of the primary UI.
- **Database authorization:** Supabase RLS and archive membership decide what the signed-in user may read or modify.
- **Google Drive authorization:** separate server-side OAuth; never derived from the user's DLR login.

Authentication proves identity; archive membership grants access; Google Drive OAuth controls storage access. These are separate boundaries.


## Preferred login experience

The normal experience is **email + password**. New users create an account in DLR, remain disabled until an admin approves them, and then sign in directly with the password they chose. Google Sign-In may be added later as an optional provider. Magic Link is retained only as legacy/recovery backend compatibility and is not shown in the primary UI.


## DLR accounts and roles

DLR authorization is archive-membership based, not Gmail/provider based.

- Any valid email provider can be used for a DLR account (Gmail is not required).
- Primary native login is email + password.
- Magic Link remains a passwordless/recovery option.
- Google Sign-In is optional and maps into the same Supabase user/membership model when enabled.
- Registration is self-service, but a new account starts with archive role `viewer` and status `disabled`; creating a Supabase Auth user does not grant usable archive access until an admin activates it.
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
1. Create an account or sign in with an existing approved email/password account.
2. New accounts wait for admin approval.
3. Once active, sign in directly with email + password.
4. An authenticated member can change the password from the Account section.
5. DLR does not persist or log the password.

This does not change archive roles or Google Drive permissions.


## Vercel deployment

The DLR web/auth/search control plane is now deployed on Vercel:

`https://umv-dlr.vercel.app`

Verified production behavior:
- home page returns HTTP 200;
- `/api/v1/health` returns HTTP 200;
- password-first sign-in and self-service account creation are available; new memberships start disabled until admin approval;
- Vercel Authentication protection is disabled so DLR's own Supabase authentication is the user-facing gate;
- real intake remains disabled on the Vercel deployment.

The current Vercel deployment does not receive the private Google Drive OAuth credentials. Original-file streaming, Drive writes, OCR/system-binary processing, and other private-worker responsibilities remain on the Oracle deployment until explicitly migrated.

Password-first login does not depend on the Supabase redirect allow-list. Adding the Vercel origin remains a future hardening/portability task only for optional Magic Link or Google Sign-In flows.


## Account creation

DLR uses a password-first account workflow:

1. Open `https://umv-dlr.vercel.app`.
2. Choose **Create Account** and enter email + password.
3. The account is created with archive access disabled.
4. A DLR admin chooses the role and changes the account to Active.
5. The user signs in directly with email + password.

The normal UI does not require a Magic Link. New accounts do not receive archive access until an admin explicitly activates them.


## Baseline verification

Verified 2026-10-03:
- canonical Vercel home and health endpoints return HTTP 200;
- dedicated Bitwarden-backed Oracle worker identity is active as editor and the systemd timer is active;
- real short-lived authenticated bearer insert/read and RLS denial passed;
- authenticated HTTP synthetic intake → Drive → queue → worker → search → original streaming passed;
- private original bytes matched the uploaded source exactly;
- cleanup returned the live archive to zero letters, zero processing jobs, and zero processing rows;
- full Oracle synthetic suite passes 275/275;
- real intake remains disabled.

Optional future enhancements include Google Sign-In, Gemini semantic enrichment, live messaging/watched-folder connectors, leaked-password protection, and Vercel auto-deploy/redirect portability.


## Controlled real-letter pilot

As of 2026-10-03, the private Oracle DLR runtime is in a bounded manual pilot: real intake is enabled there with a hard cap of 2 real letters. The public Vercel deployment remains synthetic-only for intake and does not hold private Drive upload credentials. The UI reports `PILOT MODE` and remaining slots to authenticated editors/admins. After the first real letter is ingested, the second real-letter slot is automatically blocked until the first letter is reviewed and slot two is explicitly unlocked. No real letter has been ingested yet at this checkpoint. Live connectors, bulk import, rename execution, and automated delete remain outside the pilot.


## WhatsApp intake

The private Oracle runtime can ingest official PDF/JPG/JPEG/PNG attachments from a dedicated WhatsApp archive group through the existing Hermes session. The connector is group-allowlisted, stages media into a protected local queue, preserves WhatsApp message provenance for deduplication, and processes it through the same immutable Drive + Supabase + worker pipeline as manual intake. The initial WhatsApp rollout is separately capped at 20 documents. Runtime group/member identifiers and credentials are never stored in this public repository.
