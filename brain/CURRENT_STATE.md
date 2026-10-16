# Project Brain — Current State

Last reconciled: 2026-10-10
Canonical repository: `zzpsah/digital-letter-registry`
GitHub and Oracle were reconciled on 2026-10-06. Always verify the current HEAD from Git/`.ai/STATE-INDEX.md` before acting; do not hard-code a semantic handoff to one commit hash.

> This file describes the **current truth only**. Historical checkpoints belong in `docs/HISTORY.md`, `.ai/CHANGELOG.md`, Git history, and enhancement-specific brain folders. Do not treat old synthetic-only checkpoints as current state.

## Product baseline

DLR / eLetters is the Official Letter Intelligence Archive for school/government PDF and image letters.

Canonical document flow:

```text
WhatsApp / approved intake
        ↓
Preserve original document
        ↓
Extract native text or Hindi+English OCR
        ↓
Understand the document from source evidence
        ↓
Derive title / authority / reference / date / actions / audience
        ↓
Store searchable structured metadata
        ↓
Deliver/update email + WhatsApp summary
        ↓
Search / open original / reprocess when needed
```

The original PDF/image is authoritative and immutable as the logical source. OCR, category, title, summary, authority mapping, actions, embeddings, importance, relationships, and delivery text are derived data and may be reprocessed.

## Technical flow references

- `docs/TECHNICAL-FLOWCHART.html`: visual algorithm flowchart plus deployment URLs, port/exposure map, service/timer inventory, tools/integrations, and failure conditions.
- `docs/INFORMATION-FLOW-AND-DEPLOYMENT.md`: detailed evidence-labelled information-flow and deployment inventory.
- Update both files in the same change whenever architecture/runtime routes, ports, services, integrations, processing branches, translation, storage, security exposure, or failure handling changes. The HTML is a documentation snapshot, not proof every logical branch is deployed.

## Current live architecture

- Public user-facing control plane: Vercel eLetters web app.
- Primary authentication: email + password through Supabase Auth.
- Authorization: archive membership with admin/editor/viewer roles plus RLS/API checks.
- Private runtime/worker: Oracle VPS.
- Private original storage: explicitly authorized Google Drive archive.
- Structured archive/search metadata for the migrated workload: Oracle PostgreSQL `dlr_primary` through the local Supabase-compatible API bridge; hosted Supabase is not a verified replica.
- OCR: native PDF text first, then Hindi/English OCR fallback.
- Private Drive credentials, runtime secrets, private identifiers, and real documents must never be committed to public Git.
- GitHub is the durable source repository; Oracle is the live private runtime.

## Public Vercel entry points — 2026-10-10

- `https://eletters.vercel.app/` is a public product-information homepage for UMV Storage Automation / eLetters, added to support OAuth consent-screen website-information requirements.
- `https://eletters.vercel.app/app` serves the existing eLetters sign-in/application UI.
- `https://eletters.vercel.app/privacy-policy` serves the public privacy policy.
- `https://eletters.vercel.app/api/v1/health` is the health endpoint.
- All four routes returned HTTP 200 in a live HTTPS check on 2026-10-10. This is route availability evidence, not proof that Google OAuth verification is approved.

## Intake status

- Public Vercel intake does not hold private Drive upload credentials.
- A controlled real-document WhatsApp pilot is active on the private Oracle runtime for the dedicated approved official-letter group.
- WhatsApp PDF/JPG/JPEG/PNG attachments use the same immutable Drive + Supabase + processing pipeline.
- Exact duplicate content is detected before creating a second archive object.
- Destructive or replacement choices remain explicit and guarded.
- Do **not** infer that the live archive has zero real records from older synthetic cleanup checkpoints.

## Intelligence contract

Document meaning is **source-first**.

- Category/subcategory is secondary taxonomy only.
- A wrong category must never force a wrong title, summary, authority, action, audience, email subject, or WhatsApp explanation.
- User-facing intelligence must be independently grounded in the current document.
- Existing stronger structured facts should not be replaced by weaker reprocessing output.
- Authority display prefers canonical short names when mapped, while raw extracted authority stays preserved.
- Uncertain authority should remain unmatched for review rather than being force-mapped.

## Reprocess contract

Editor/Admin can reprocess an existing archived document when OCR/context/summary/authority/action output is missing or wrong.

Reprocess must:
- target the same archived original;
- update derived data instead of creating a duplicate letter;
- avoid a second active processing job for the same letter;
- preserve stronger prior facts when new evidence is weaker;
- update the same logical document across search/index/portal and delivery surfaces;
- avoid resending mail for wording-only paraphrases;
- use the existing correction/replacement delivery path for material corrections;
- replace the prior generated WhatsApp reply when applicable.

A weak derived result must not be blamed on a “poor PDF” unless the source itself is actually poor.

## Delivery presentation

Global WhatsApp presentation:
- Headings remain in English, including **What this is** and **Action items**.
- Their content is Hindi/Devanagari with useful official English terms preserved where helpful.
- Email may contain fuller OCR/document context.
- Delivery is idempotent: wording-only AI variation must not create duplicate notifications.

## Search and document UI

- Default document order: latest uploaded first.
- Available sorting includes Important first, Issue date, Title A–Z, and Relevance.
- Editor/Admin can mark a document Important and add an internal note.
- Important state is shared in the authenticated archive.
- Internal user comments/notes must not leak to public Drive index output.
- Letter cards expose a compact document ID for troubleshooting, but normal portal actions do not require typing it.

## Admin baseline

Admin Console includes:
- Overview/dashboard
- Users and access approval
- Roles/status management
- Recipients and allowed-recipient summary
- WhatsApp allowlist/group controls
- Dynamic categories
- Canonical authorities, aliases, merge/remove/restore/permanent-delete controls
- Failed processing jobs and explicit Retry
- Audit log
- Configuration backup/restore preview
- Bulk reversible actions

Normal removal is reversible first. Permanent deletion is secondary, explicit, and confirmed.

## Authority baseline

Authority represents the actual issuing/signing authority, not issuer + recipient + cited offices concatenated together.

Canonical hierarchy may include school/headmaster, BEO, functional DPO, DEO, RDDE, and state Education Department. Canonical records retain aliases and jurisdiction. Admin-confirmed mappings may be reused later. Raw issuer text remains on the letter.

## UI governance

The accepted eLetters interface is protected by:
- `docs/UI-DESIGN-CONTRACT.md`
- `brain/ui-governance/`

Before UI/auth/search/admin/recipient/delete/restore changes, read those files. Do not wholesale redesign, recolor, or replace navigation unless explicitly requested.

## Delivery credential — 2026-10-09

Gmail outbox delivery authenticates with a Gmail app password over `smtp.gmail.com:465`, injected from
Bitwarden Secrets Manager as `DLR_GMAIL_APP_PASSWORD`. The previous OAuth refresh token expired 2026-10-09
14:29 UTC under the OAuth client's 7-day Testing-mode lifetime and silently halted outbox draining.

The OAuth app was published from Testing to In production and the archive-owner Drive token was re-consented and
rotated into the secret manager, so the Drive path no longer carries a 7-day expiry. Details live in
`brain/post-processing-delivery/` and `brain/drive-oauth-secret-manager/`.

## Search index state — 2026-10-16

Keyword search is live and covers `extracted_text` in full plus title, summary, reference, authority, concepts,
related terms, a Hindi/English alias dictionary and trigram fuzzy matching. Vector/semantic search is **not**
active: `letter_chunks` remains empty because embedding generation is separately gated by
`DLR_GEMINI_EMBEDDINGS_ENABLED`, which is intentionally not enabled. Direct Gemini document understanding is
live from the Oracle worker; the Supabase `gemini-ai-gateway` remains quota-blocked and is only a fallback.

## Gemini processing recovery — 2026-10-16

- The Supabase `gemini-ai-gateway` still returns HTTP 402 `exceed_egress_quota`; this remains an external gateway/project restriction.
- `DLR_GEMINI_API_KEY` is present in Bitwarden Secrets Manager. The Oracle worker wrapper maps it to `GEMINI_API_KEY` without printing the value.
- A live synthetic text-analysis request and a live synthetic original-file request both succeeded against Google's Gemini API using the production-configured `gemini-3.5-flash-lite` model. Both returned structured document fields including title, authority, reference number and summary.
- The direct provider's previous `responseFormat.text.mimeType/schema` payload was rejected by Gemini. It now uses `generationConfig.responseMimeType` and Gemini REST-compatible `responseSchema`; JSON-schema nullable unions are translated into Gemini `type` plus `nullable` fields.
- The worker selects direct Gemini whenever the injected key is present, before considering the Supabase gateway. Its runtime wrapper loads `.env`, so `AI_MODEL=gemini-3.5-flash-lite` is the configured production model.
- Full unit suite: 365 tests passed. Existing `ResourceWarning`s in worker-session tests are unrelated.
- Vector embeddings remain disabled unless `DLR_GEMINI_EMBEDDINGS_ENABLED` is explicitly enabled. Do not enable embeddings/backfill as part of document-analysis recovery.

## Remote access

Canonical instructions: `docs/REMOTE-ACCESS.md`.

For Oracle work:
1. discover Desktop Commander devices;
2. select online `oracle-server`;
3. ping it;
4. inspect `/home/prashant/projects/digital-letter-registry`;
5. check Git status and repository context before changes.

GitHub access alone is not live Oracle access.

## Current operational rule

Before meaningful work:
1. read `AGENTS.md`, `RULES.md`, `.ai/STATE-INDEX.md`, `.ai/CURRENT-STATE.md`, this file, and relevant enhancement brain;
2. inspect current source/Git state;
3. for live-runtime work, verify Oracle separately;
4. make the smallest scoped change;
5. test;
6. synchronize current-state/handoff documentation when behavior materially changes.

## Historical checkpoint warning

Statements such as “no real letters”, “real intake disabled everywhere”, “short-lived bearer slice pending”, old test totals such as 188/188 or 212/212, or 2026-10-02 runtime blockers are **historical**, not current operational truth. Consult Git history and `docs/HISTORY.md` when those milestones matter.

## Information-flow inventory — 2026-10-10

Use [docs/INFORMATION-FLOW-AND-DEPLOYMENT.md](../docs/INFORMATION-FLOW-AND-DEPLOYMENT.md) as the canonical site, port, component and data-flow inventory. It distinguishes observed live mappings from unresolved service ownership. Tailscale Funnel ports 10000, 10001 and 8443 were publicly reachable at audit time; port 10001 routes to the DLR API on loopback 8877. The Oracle working tree was clean but behind GitHub main during that historical audit. The subsequent 2026-10-16 guarded deployment is recorded below; unresolved port ownerships remain a separate infrastructure review item.

## eLetters archive visibility recovery — 2026-10-15

- The primary local archive has 68 letter records: 67 not trashed, 1 already in Trash. All 68 Drive object references returned metadata successfully; a read-only Drive original download succeeded. No files were deleted, restored, or re-uploaded during diagnosis.
- Search's `403 Forbidden` was caused by missing authenticated `SELECT` grants on `public.authorities` and `public.authority_aliases`, which the search RPC joins. Both grants are now applied in the live database and persisted in migration `supabase/migrations/20261015181000_grant_archive_authority_read.sql`; RLS policies remain enabled.
- Frontend Home list was hardened to reset stale pagination on login/empty pages and show explicit errors instead of silently returning on failed list requests. Service worker cache version bumped to v3. Focused web-shell tests: 24 passed. Awaiting live user confirmation after refresh.


## PostgreSQL primary integration checkpoint — 2026-10-16

Oracle PostgreSQL 16 + pgvector `dlr_primary` is the primary data plane for the migrated DLR workload. Local GoTrue/PostgREST remain behind the FastAPI compatibility bridge; PostgreSQL is loopback-only. Canonical database operations are in `zzpsah/postgresql-services/projects/official-letter-intelligence/database-operations/`; the former standalone database repository was consolidated/deleted.

Live snapshot: 19 public tables, 28 public functions, 18 RLS-enabled tables, 53 public RLS policies; 68 letters, 68 processing rows and 103 jobs (99 completed, 4 failed, 0 active). Queue integrity checks passed: no missing `archive_id`, orphan job, archive mismatch or duplicate letter/reason pair. Four historical failed jobs remain (two prior RLS/archive-scope failures, two network/timeout failures); no bulk retry was performed.

Full DLR suite: **377 tests passed, 0 failures**. Direct Gemini synthetic text/file checks passed. Live authenticated login/search/detail/original checks passed; private storage references stayed out of detail JSON and unauthenticated search/original access was rejected. Fresh encrypted local/off-site backups both restored to disposable databases with 19 public tables and 28 public functions. Ansible syntax and validation passed without deployment/restart.

One low-confidence source-conflict result (0.45) and a second record remain flagged for review; processing completion is not semantic acceptance. Embeddings remain disabled. Hosted Supabase is not a verified replica; schema drift and DR sync/failover remain separate work.

Reviewed implementation commit `aa2c54d` is deployed on Oracle as revision `b16c899`; DLR main is synchronized and clean. The guarded Ansible deployment and post-deploy API/Auth/REST, authenticated search/detail/original, unauthenticated rejection, queue-integrity and synthetic Gemini checks passed. One worker timer run failed transiently during API restart with connection refused; the next scheduled run returned idle and the timer remains active. Preserve the unrelated untracked OSINT migration in PostgreSQL Services.

Read `brain/postgres-primary-integration/` and PostgreSQL Services `docs/DLR-POSTGRES-INTEGRATION-STATUS-2026-10-16.md` before database or worker changes.
