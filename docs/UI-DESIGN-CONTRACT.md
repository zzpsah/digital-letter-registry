# eLetters UI & Behavior Contract

Status: **LOCKED baseline**. This document is a guardrail for future AI agents, coding tools, and developers.

## Prime rule

Do **not** redesign or rewrite the eLetters portal wholesale. Preserve the existing information architecture, purple visual identity, compact mobile-first layout, current navigation, and established workflows. Make the smallest compatible change necessary for the requested feature.

A new tool must not replace the UI framework, change the whole color scheme, rename major navigation, move controls across pages, or change authentication/data behavior merely because another design seems cleaner.

## Product identity

- Product name: **eLetters**
- Purpose: official school/education document registry, search, delivery and administration.
- Primary deployment: `https://eletters.vercel.app`
- Runtime data source: Supabase.
- GitHub is source/version/deployment input; GitHub is **not** the runtime document database.
- Public Drive index is a separate generated view and must follow the same visibility rules for active/trashed/important documents.

## Locked visual system

The current UI is intentionally simple, compact, mobile friendly and purple themed.

CSS token baseline:
- `--bg: #f3efff`
- `--card: #ffffff`
- `--text: #241b35`
- `--muted: #70687d`
- `--line: #ded6ee`
- `--brand: #6d28d9`
- `--brand2: #5521a8`
- `--soft: #eee7ff`
- `--danger: #b42318`
- Sidebar/top navigation base: `#4c1d95`
- Navigation active/hover: `#6d28d9`
- Important-letter card: `#fff8cf` with `#e2c45f` border.
- User note: `#fff3ad` with `#d7a900` accent.

### Design DON'Ts

Do not:
- replace the purple theme with another palette;
- introduce gradients, glassmorphism, large hero banners, dashboard clutter or decorative illustrations;
- replace the compact navigation system without explicit request;
- show developer jargon, test terminology, infrastructure names, internal IDs or queue internals to normal users;
- expose passwords, API keys, tokens, cookies, internal comments or private runtime data;
- expand advanced/admin sections automatically;
- remove mobile responsiveness;
- change button meanings or destructive-action confirmation semantics;
- remove Restore paths where soft-delete exists;
- rename user-facing labels casually.

## Navigation baseline

Normal authenticated navigation:
- Home
- Search
- Upload (write roles)
- Admin (admin only)
- Account

Admin sub-navigation:
- Overview
- Requests
- Users
- Recipients
- WhatsApp
- Categories
- Operations
- Trash
- Audit
- Backup

Admin-only controls must stay protected server-side, not merely hidden in UI.

## Language display contract

Top-right selector must visibly say **Language**.

User-facing options:
- **Hinglish** — default
- **हिन्दी**
- **English**

Internally the existing compatibility value `mixed` may remain for Hinglish.

Behavior:
- Hinglish: prefer `summary_hi` and `action_required_hi`; English/source terminology may remain naturally mixed.
- हिन्दी: prefer Hindi/Hinglish structured fields, with English fallback when missing.
- English: prefer English structured fields, with Hindi fallback when missing.
- Persist display preference locally on the device/browser.
- Titles remain source/intelligence titles unless a separately verified translated-title field exists.

## Search contract

Visible button label: **Smart Search**.

Current search is hybrid:
- text search;
- fuzzy matching;
- semantic/vector matching when embeddings are available;
- Gemini embedding provider when configured;
- automatic text/fuzzy fallback when AI/embedding service is unavailable.

Do not make ordinary archive search dependent on a generative-model answer.

### Home quick-search behavior

Home quick-search is temporary:
- Home → Smart Search may open Search results.
- Refresh from a Home-origin quick search clears that temporary query and returns to Home.
- Search explicitly started from the Search tab stays on Search and refreshes normally.
- Search-tab input/filter changes convert the state to normal Search-origin behavior.

## Recent-document display

Recent documents must not be English-only.

Default card body priority:
- Hindi/Hinglish structured summary/action first;
- English only when English mode is selected or Hindi/Hinglish fields are unavailable.

Keep official English terms such as UDISE, ICT Lab, Smart Class, Nodal Teacher and e-ShikshaKosh when natural.

## Authentication contract

Primary login is email + password.

Login screen includes **Remember me on this device**, checked by default.

Behavior:
- checked: persistent refresh-cookie session, currently default 30-day maximum;
- unchecked: session cookies only;
- token refresh preserves the chosen persistence mode;
- Sign out clears all session/remember cookies.

### New-account approval

New account requests require administrator approval.

After approval:
- account is activated;
- current first-time/default password is `eletter@1234` unless explicitly changed by project decision;
- approval email contains login URL, email and first-time password;
- user should change password from Account after first login.

Do not commit/store user passwords in repo docs, memory, logs or app tables. Supabase Auth remains the password authority.

Admin Users controls:
- role;
- active/disabled status;
- Set password;
- Delete user.

Safety:
- current admin cannot delete self;
- last active admin cannot be deleted.

## Recipient contract

Recipient requires Name and at least one of Email or WhatsApp/mobile.

Valid combinations:
- Email only → Email auto-enabled; WhatsApp disabled.
- WhatsApp only → WhatsApp auto-enabled; Email disabled.
- Both → both available channels auto-enabled.

Missing-channel controls stay disabled.

Recipient controls:
- View
- Save/Edit
- Make default
- Remove

Remove is soft removal. Removed recipients support Restore and Delete permanently.

## Document Delete / Trash contract

Normal document Delete is **soft Trash**, not permanent deletion.

On normal Delete:
- registry row remains;
- letter is marked trashed;
- Google Drive original moves to Drive Trash;
- trashed letter is hidden from Home/Search;
- trashed letter is excluded from public Drive index.

Admin → Trash:
- Restore — restores Drive original and registry visibility;
- Delete permanently — permanently removes original Drive object and registry row.

Do not reintroduce direct hard-delete from ordinary document cards.


## Document visibility contract

Documents support **Public / Private / Personal** visibility.

- Public: normal authenticated portal visibility and eligible for the public Drive index/original sharing.
- Private: authenticated archive members only; exclude from public Drive index and remove anonymous Drive access.
- Personal: the user who marked it Personal plus admins; the original ingest owner retains backend access so processing/reprocessing can continue.
- Editor/Admin document cards expose a compact visibility control.
- Visibility must be enforced by database RLS and original-file access, not only by UI hiding.
- Private/Personal documents must not publish a generated WhatsApp receipt; previously generated receipts should be removed by the private runtime when possible.
- Existing documents remain Public unless explicitly changed.

## Important/star contract

Important document:
- compact corner `★`/`☆`;
- pale-yellow highlighted card;
- optional internal user note.

Public Drive index may mirror important/star state but must **not** publish internal `user_comment`.

Upload date remains separate from issue date. Default sort is latest uploaded/added first.

## Operations contract

Admin → Operations lists failed processing jobs.

Controls:
- Retry
- Retire
- Delete

Semantics:
- Retry → failed job becomes pending.
- Retire → removes job from active failure queue but retains its record.
- Delete → permanently deletes only the processing-job record, not the letter.

Failed jobs must not continuously retry by themselves. Distinct intentional reprocessing reasons may create multiple historical jobs for one letter.

## User-facing wording

Normal users should not see implementation jargon such as tests, Supabase, Vercel, workers, queue internals or raw IDs.

## Change discipline

Before changing UI/behavior:
1. Read `AGENTS.md`, `RULES.md`, this contract, `.ai/STATE-INDEX.md`, `.ai/CURRENT-STATE.md`, and relevant `brain/` docs.
2. Inspect current source and live behavior.
3. Preserve existing functionality unless explicitly changed.
4. Prefer small patches over rewrites.
5. Add/update regression tests.
6. Run full tests, JavaScript syntax check and `git diff --check`.
7. Update `.ai/`, `brain/`, README/handoff docs when behavior changes.
8. Verify live Vercel UI after deployment for user-visible changes.

## Protected invariants

Require explicit user instruction to change:
- purple visual identity;
- simple compact/mobile-first UI;
- Hinglish default;
- Smart Search hybrid/fallback model;
- Remember-me default checked;
- recipient single-channel support;
- recoverable document Trash;
- recoverable recipient Remove;
- admin-controlled account approval;
- source-grounded document intelligence;
- public index must not expose internal notes;
- GitHub is not runtime document data.

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

- Search Authority filter uses only the canonical short name for display (for example `DEO Siwan`, `DPO Establishment, Siwan`); full English/Hindi canonical names remain metadata and aliases, not dropdown label clutter.

## Authority merge and permanent deletion
- Admin → Authorities supports Save/Edit, Remove/Restore, Merge into another canonical authority, and Delete permanently.
- Merge moves all linked letter mappings and aliases to the selected target, updates child-parent references, then deletes the duplicate source authority.
- Permanent Delete removes the authority master; linked letters keep their raw authority text but become unmatched for later review/remapping.
- Authority rows show linked-letter counts before destructive actions.

- Admin → Recipients shows a separate read-only `Allowed recipients` summary above management, with enabled Email/WhatsApp/Both channels and the current Default recipient clearly visible.
