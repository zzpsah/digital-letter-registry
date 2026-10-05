# Current State

- Canonical repository: `zzpsah/digital-letter-registry`.
- Formal archive name: **Official Letter Intelligence Archive**.
- Public-repository privacy boundary is established: code/docs/synthetic fixtures/schema only.
- Existing private UMV Google Drive is the selected original-file storage.
- Private archive structure exists with `originals/`, `quarantine/`, and `exports/`; connected Drive access on 2026-10-02 re-verified the structure and confirmed only the previously used synthetic integration PDF in `originals/`. No real archive letters have been ingested.
- A separate Supabase archive project exists, isolated from the existing UMV database.
- Public archive tables use owner-scoped RLS with `auth.uid() = owner_id`.
- DB-level synthetic verification on 2026-10-02 confirmed: owner-context insert succeeds, owner-context read succeeds, a different synthetic user sees zero rows, and cross-owner insert is rejected by RLS.
- In addition to the earlier DB-level claim simulation, a real short-lived Supabase Auth bearer session now passed live PostgREST insert/read verification and anonymous RLS denial using disposable synthetic data.
- Repository auth/template implementation is ready: `supabase/templates/magic-link.html` already targets the server-side `/auth/confirm?token_hash=...` callback.
- Archive-owner magic-link delivery is working. The hosted project uses Supabase's default direct-confirmation email because the Dashboard requires custom SMTP before editing template subject/body. The application now supports that default flow with a hardened fragment bridge at `/auth/confirm`: browser fragment tokens are posted same-origin, the server validates the authenticated owner, stores only HttpOnly cookies, and clears the URL. The checked-in token-hash template remains an optional future path if custom SMTP is enabled.
- VPS auth/API suite passes 29/29 tests after default-flow and rate-limit handling; the full synthetic unit suite passes 212/212 tests after adding file-based Drive OAuth support. The Supabase Management Auth-config helper focused suite passes 4/4.
- VPS project runtime has Supabase runtime/publishable configuration but no Supabase Management API token or CLI login; hosted Auth settings therefore cannot currently be changed from the VPS through the existing credential set. A guarded Management API helper is now implemented and ready once a scoped runtime management token is supplied.
- The connected remote execution layer correctly blocked forwarding a one-time auth token into a VPS command. No bypass was used and no one-time token was persisted.
- The retained synthetic RLS verification row was removed through a controlled exact-match cleanup; `letters` now contains zero rows.
- Supabase archive-owner Auth identity exists and is confirmed.
- The public-safe core schema is captured under `supabase/migrations/`.
- Domain code includes immutable source identity, SHA-256 fingerprints, processing versions, statuses/relationships, and smart filenames.
- Official filename pattern is `short-title__issuer__date__reference-number.ext`.
- Naming preserves Hindi/English/Hinglish Unicode and uses `undated` / `no-ref` placeholders.
- VPS OCR runtime has working Hindi/English Tesseract and OCRmyPDF through the configured commands.
- The legacy VPS `phone_drive` rclone credential remains unsuitable for registry access and is not used by DLR.
- A dedicated Google desktop OAuth client for DLR is authorized for the archive owner. The verified Oracle runtime now injects client id/client secret/refresh token from its approved secret manager; the protected authorized-user file was retired after successful secret-manager-only refresh/list/stream verification.
- Live DLR Drive verification passed: refresh exchange succeeded, originals listing returned the single synthetic integration file, and `GoogleDrivePrivateTransport` streamed the synthetic original successfully (24,668 bytes).
- Gemini runtime remains unconfigured; an apparent Hermes reference was only example/commented configuration and no live key was available to reuse.
- The dedicated Google OAuth client has been used successfully; temporary OAuth handoff files are removed after secret-manager rotation and the runtime no longer depends on a persistent authorized-user credentials file.
- DLR runtime is isolated on its own tailnet-only HTTPS endpoint; it no longer shares the localhost/shared origin previously used during testing. The exact private endpoint is runtime-only and is not recorded in public Git.
- The canonical user-facing control plane is now the public Vercel URL with password-first auth. The private Oracle HTTPS origin remains an operational/private-worker endpoint rather than the normal user entrypoint.
- Magic-link email throttling is now surfaced safely as HTTP 429 instead of an internal 500.
- Public Vercel control-plane deployment is live; no real archive-letter ingestion has occurred and real intake remains disabled.
- On 2026-10-03, the bootstrap admin successfully updated the DLR password through the live Account flow. This completes the real password-setup milestone; no password value is stored or logged in repository state.
- Live Supabase membership verification on 2026-10-03 shows two active admins and one active viewer. The earlier second-admin invite is accepted. Archive letters and processing jobs remain at zero.

## Baseline completion

The core DLR baseline is complete. Keep `ENABLE_REAL_INTAKE=false` until real archive ingestion is explicitly authorized. Remaining work is optional/external hardening: Google Sign-In, leaked-password protection, Vercel redirect/auto-deploy portability, Gemini semantic enrichment, and live messaging/watched-folder connectors.

Public Vercel hosting is authorized and live. Real-letter ingestion, historical adoption, Drive rename/delete operations, and real connector intake remain disabled unless explicitly enabled later.

## 2026-10-02 — RLS verification checkpoint

- Confirmed all public archive RLS policies are owner-scoped for the authenticated role.
- Synthetic owner insert/read succeeded.
- Synthetic wrong-user read returned zero rows.
- Synthetic cross-owner insert was denied by the RLS policy.
- The DB-level claim simulation is now complemented by a real short-lived bearer/PostgREST insert/read + RLS-denial test.
- The synthetic verification row was removed after the RLS test; `letters` now contains zero rows.

## 2026-10-02 — Runtime connectivity checkpoint

- Magic-link delivery to the authorized archive-owner mailbox was verified.
- Checked-in magic-link template is correct for server-side `token_hash` verification, while the hosted Supabase project uses default direct-confirmation behavior because custom SMTP is required to edit email templates.
- Default hosted callback compatibility is implemented and hardened (`no-store`, `no-referrer`, CSP, owner validation, HttpOnly cookies, URL cleanup).
- VPS auth/API tests: 29/29 passed.
- Full VPS synthetic unit suite: 212/212 passed.
- Dedicated tailnet-only HTTPS routing verified from an authorized tailnet client.
- Supabase Management Auth-config helper focused suite: 4/4 passed.
- Existing Supabase runtime credentials are sufficient for application access but not for Management API Auth-template changes.
- Secret-manager-backed Google Drive OAuth runtime is configured and verified with a write-capable grant; refresh/list/stream and disposable synthetic upload/stream/delete cleanup all passed.
- The older `phone_drive` rclone path remains separate and unused by DLR.
- Scoped Oracle runtime readiness now passes fully in synthetic-only mode.
- Gemini runtime key remains unavailable, but this is no longer a baseline blocker because deterministic OCR/full-text context fallback is active.
- Drive write verification is complete with synthetic data; semantic embeddings remain a later optional enhancement.

## Last automated change
- Commit: ee5560624e4e3791b63e308caf144c68a899c963
- Change: Fix unmatched authority review list
- Date: 2026-10-05
- Durable context synchronization: completed
## Delivery quality recovery / duplicate suppression
- Quality engine v2 marks low-context-confidence + no-clean-document-text results for bounded reprocessing even when the aggregate score is above the old threshold.
- Low-quality first-pass results may still be delivered; they are not permanently held.
- Later corrected context should use the existing same-thread correction path.
- Reprocessing must not resend mail merely because AI paraphrased summary/action wording.

## Manual document reprocessing
- Editor/Admin users can request Reprocess from each letter card when derived output is missing or wrong, even when the source PDF/image is clear.
- Reprocess always targets the existing archived original and updates derived OCR/context/summary/authority/action; it must not create a duplicate letter or replace the original file.
- If the same letter already has a pending/processing job, another reprocess request is not queued.
- Weak or inaccurate processing output must not be described as a poor PDF unless the source file itself is actually poor.
- Delivery remains idempotent: wording-only changes do not resend; material corrections or real poor-context-to-usable-context improvements use the same Gmail thread / WhatsApp replacement path.

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

## Authority merge and permanent deletion
- Admin → Authorities supports Save/Edit, Remove/Restore, Merge into another canonical authority, and Delete permanently.
- Merge moves all linked letter mappings and aliases to the selected target, updates child-parent references, then deletes the duplicate source authority.
- Permanent Delete removes the authority master; linked letters keep their raw authority text but become unmatched for later review/remapping.
- Authority rows show linked-letter counts before destructive actions.
