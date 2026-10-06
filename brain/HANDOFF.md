# Project Brain — Handoff

Last reconciled: 2026-10-06

## Read order

Before meaningful work, read:
1. `AGENTS.md`
2. `RULES.md`
3. `.ai/STATE-INDEX.md`
4. `.ai/CURRENT-STATE.md`
5. `brain/CURRENT_STATE.md`
6. `docs/UI-DESIGN-CONTRACT.md` for UI/auth/search/admin work
7. the relevant enhancement brain folder

Repository evidence is authoritative over chat memory. Current-state files describe present behavior; old checkpoints belong to history and must not override current source/runtime evidence.

## Canonical current handoff

DLR/eLetters is live as a web control plane with a private Oracle worker and private Drive archive. GitHub and Oracle were reconciled on 2026-10-06. Before runtime work, verify the current GitHub and Oracle HEADs rather than relying on a hash copied into this handoff.

The normal document flow is:

```text
approved intake
→ preserve original
→ text extraction / Hindi+English OCR
→ source-grounded intelligence
→ structured archive/search
→ email + WhatsApp delivery
→ search/open/reprocess
```

### Never regress these rules

- Original document remains the logical source of truth.
- Category is secondary taxonomy, never document meaning.
- User-facing title/summary/action/audience/authority must come from document evidence.
- Reprocess updates the same logical document; it must not create a duplicate letter.
- Reprocessing must not resend delivery for wording-only paraphrases.
- Material corrections use the existing email-thread / WhatsApp replacement path.
- A prior generated WhatsApp reply should be replaced when a corrected one is posted.
- Default portal sorting remains latest-uploaded-first.
- Internal notes/comments remain private to authenticated users.
- Normal Remove actions are reversible; permanent delete is explicit and confirmed.
- Preserve the accepted responsive eLetters UI contract.

## Intake boundary

The public Vercel app is the user-facing control plane and does not carry private Drive upload credentials.

The private Oracle runtime supports the controlled approved WhatsApp real-document pilot. Do not use older “zero real letters / no live connector” checkpoints as the current state.

Do not broaden intake, bulk-import historical documents, rename/delete originals, or expose private storage/runtime identifiers without the appropriate explicit authorization and safeguards.

## Reprocess handoff

Use manual Reprocess for wrong or missing derived intelligence.

Reprocess must:
- use the existing original;
- stay single-flight per document;
- preserve stronger prior facts over weaker new output;
- update derived OCR/context/title/summary/authority/action as appropriate;
- keep stable document identity;
- avoid duplicate mail/WhatsApp caused only by AI wording variation.

If output is weak, diagnose extraction/context/provider behavior before claiming the PDF itself is poor.

## Authority handoff

- Keep raw authority text on the letter.
- Prefer canonical short authority names in user-facing UI.
- Unmatched/null authority mappings must remain visible for review.
- Admin can edit aliases/names, merge duplicates, soft-remove/restore, or permanently delete with explicit confirmation.
- Merge must preserve letter mappings and aliases.
- Search authority labels should stay concise.

## Admin/UI handoff

Preserve:
- Overview + Audit
- Operations failed-job review and explicit Retry
- Users/access approval/roles
- recipients + allowed-recipient summary
- WhatsApp allowlist/group controls
- categories
- authorities
- backup/restore preview
- reversible bulk actions
- Important flag and note
- compact mobile layout and existing navigation

Before changing any of these, read `docs/UI-DESIGN-CONTRACT.md` and `brain/ui-governance/`.

## Remote Oracle handoff

Read `docs/REMOTE-ACCESS.md`.

A new AI chat must:
1. call Desktop Commander device discovery;
2. select online `oracle-server`;
3. ping it;
4. inspect `/home/prashant/projects/digital-letter-registry`;
5. run `git status --short` and compare live HEAD with origin before runtime work.

Never pretend GitHub access equals VPS access.

## Documentation discipline

After a meaningful behavior change:
- update source/tests;
- update README when user-facing behavior changed;
- update `brain/CURRENT_STATE.md`;
- update `brain/HANDOFF.md` only when the next-agent handoff changed;
- update `.ai/CURRENT-STATE.md`;
- put chronological milestone detail in `docs/HISTORY.md` or `.ai/CHANGELOG.md`, not in the current-state header.

Do not append stale checkpoints above newer truth. Current files must remain concise and present-tense.
