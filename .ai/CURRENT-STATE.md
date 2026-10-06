# Current State

Last reconciled: 2026-10-06
Canonical repository: `zzpsah/digital-letter-registry`

## Repository/runtime evidence

- GitHub and Oracle live working copies were reconciled on 2026-10-06. Always verify the current HEAD from Git before runtime work; semantic context must not pin itself to a commit hash that becomes stale after documentation commits.
- GitHub is the durable source repository.
- Oracle VPS is the private live worker/runtime and must be verified separately through Desktop Commander before runtime changes.
- Canonical remote-access procedure: `docs/REMOTE-ACCESS.md`.

## Current product state

DLR/eLetters is an operational Official Letter Intelligence Archive with:
- public Vercel web/auth/search/admin control plane;
- password-first Supabase authentication;
- archive membership roles (admin/editor/viewer) enforced by RLS/API checks;
- private Google Drive original storage;
- private Oracle processing worker;
- PDF/image text extraction and Hindi+English OCR;
- source-grounded document intelligence;
- searchable structured metadata;
- email and WhatsApp delivery/update workflows;
- manual document reprocessing;
- admin operations, authorities, recipients, categories, audit, backup/restore, and failed-job recovery.

The public Vercel app does not carry private Drive upload credentials. A controlled approved WhatsApp real-document pilot runs through the private Oracle side. Older synthetic-cleanup statements must not be interpreted as proof that the current archive has zero real records.

## Canonical processing rules

- Original PDF/image is authoritative.
- Derived OCR, title, summary, authority mapping, category, actions, audience, embeddings, importance, relationships, and delivery copy are reprocessable.
- Category/subcategory is secondary taxonomy and must never override stronger document evidence.
- User-facing meaning is source-first.
- Reprocess targets the same logical archived original and must not create a duplicate letter.
- Reprocess is single-flight for an already pending/processing document.
- Stronger existing facts are preserved when a new pass is weaker.
- Wording-only paraphrases must not trigger duplicate delivery.
- Material corrections use existing correction/replacement delivery paths.
- WhatsApp corrected output replaces the previous generated reply when applicable.

## Delivery/UI rules

- Default portal order: latest upload first.
- Important flag and authenticated internal note are supported.
- Internal notes/comments do not belong in public Drive index output.
- WhatsApp uses English headings such as **What this is** and **Action items**, with Hindi/Devanagari content and useful official English terms preserved.
- Accepted UI baseline is governed by `docs/UI-DESIGN-CONTRACT.md` and `brain/ui-governance/`; do not wholesale redesign it.

## Admin rules

Admin Console includes account approval/roles, recipients, allowed-recipient summary, WhatsApp controls, categories, canonical authorities, failed-job Retry, Audit, backup/restore preview, bulk reversible actions, and explicit destructive actions.

Normal Remove is reversible first. Permanent delete remains explicit and confirmed.

## Authority rules

Raw extracted authority remains preserved. Canonical mapping supplies clean short names and aliases. Uncertain/null mappings remain reviewable. Merge/delete operations must preserve or deliberately release linked mappings according to the guarded admin action.

## Security/privacy boundary

Never commit:
- real letters;
- private Drive IDs/URLs;
- Supabase private credentials/project secrets;
- OAuth tokens;
- passwords/cookies/sessions;
- SSH keys;
- private runtime identifiers or personal-data logs.

## Context precedence

For current behavior, use this order:
1. current source/tests and live runtime evidence when relevant;
2. `.ai/STATE-INDEX.md`;
3. this file;
4. `brain/CURRENT_STATE.md`;
5. enhancement-specific brain;
6. README/docs;
7. chronological history.

Historical test counts, 2026-10-02 blockers, “no real intake” statements, and earlier synthetic-only milestones are history rather than current truth.

## Next-agent starting point

Read `AGENTS.md`, `RULES.md`, `.ai/STATE-INDEX.md`, this file, `brain/CURRENT_STATE.md`, and the relevant enhancement brain. For Oracle work, discover/ping `oracle-server` and compare its Git state before acting.

## Last automated change
- Commit: d5fe8ea2b1568c6d6b6adfcf04739854a9bbb0a1
- Change: Trigger production deployment
- Date: 2026-10-06
- Durable context synchronization: completed
