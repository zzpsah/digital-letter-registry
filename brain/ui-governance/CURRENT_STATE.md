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
