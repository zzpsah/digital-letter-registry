# Current State — UI Governance

The accepted live baseline includes:

- Purple compact visual system; no wholesale redesign.
- Top navigation: Home, Search, Upload, Admin, Account.
- Top-right Language selector: Hinglish (default), हिन्दी, English.
- Smart Search uses text/fuzzy plus semantic embeddings when available, with non-AI fallback.
- Home quick-search is temporary; Search-tab search is persistent in Search.
- Recent cards prefer Hindi/Hinglish summary/action in default mode.
- Login has Remember me on this device, checked by default.
- Approved accounts use admin-controlled approval and the current initial-password policy.
- Admin Users supports role/status, Set password, Delete user.
- Recipient allows Email-only, WhatsApp-only, or both; available channel(s) auto-enable.
- Recipients have View/Save/Make default/Remove and removed Restore/permanent delete.
- Letter Delete means recoverable Trash; Admin Trash provides Restore/permanent delete.
- Failed jobs have Retry/Retire/Delete.
- Important documents use compact star + yellow highlight; internal comments are not public.
- Default document ordering is latest upload first.

Do not change these as cleanup/refactor side effects.
- Search Authority filter is a dynamic dropdown populated from distinct active/non-trashed letter authorities; new authorities appear automatically.

## Authority intelligence contract

Authority is exactly one actual issuing/signing authority, never a concatenation of issuer + recipient + cited offices. The classification hierarchy is **Headmaster/School → BEO (Block Education Officer / प्रखंड शिक्षा पदाधिकारी) → DPO (functional district programme authority such as Establishment) → DEO (one canonical DEO per district) → RDDE (division) → Education Department (state)**.

Canonical authority records store designation, jurisdiction and level. DPO posts may be distinct by function, for example DPO Establishment vs another DPO branch. Raw document authority text stays preserved on the letter, while `canonical_authority_id` links it to the clean authority master. Admin-confirmed aliases are learned permanently; future matching issuer strings auto-map through normalized aliases. Uncertain or multi-office strings remain unmatched for review rather than being force-mapped. Search authority dropdown shows canonical authorities, not every raw spelling variant.

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

- Search Authority filter uses only the canonical short name for display (for example `DEO Siwan`, `DPO Establishment, Siwan`); full English/Hindi canonical names remain metadata and aliases, not dropdown label clutter.
