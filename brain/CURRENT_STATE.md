# Project Brain — Current State

Last reconciled: 2026-10-06
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

## Current live architecture

- Public user-facing control plane: Vercel eLetters web app.
- Primary authentication: email + password through Supabase Auth.
- Authorization: archive membership with admin/editor/viewer roles plus RLS/API checks.
- Private runtime/worker: Oracle VPS.
- Private original storage: explicitly authorized Google Drive archive.
- Structured archive/search metadata: Supabase.
- OCR: native PDF text first, then Hindi/English OCR fallback.
- Private Drive credentials, runtime secrets, private identifiers, and real documents must never be committed to public Git.
- GitHub is the durable source repository; Oracle is the live private runtime.

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
