# Current State

- Canonical repository: `zzpsah/digital-letter-registry`.
- Formal archive name: **Official Letter Intelligence Archive**.
- Public-repository privacy boundary is established: code/docs/synthetic fixtures/schema only.
- Existing private UMV Google Drive is the selected original-file storage.
- Private archive structure exists with `originals/`, `quarantine/`, and `exports/`; connected Drive access on 2026-10-02 re-verified the structure and confirmed only the previously used synthetic integration PDF in `originals/`. No real archive letters have been ingested.
- A separate Supabase archive project exists, isolated from the existing UMV database.
- Public archive tables use owner-scoped RLS with `auth.uid() = owner_id`.
- DB-level synthetic verification on 2026-10-02 confirmed: owner-context insert succeeds, owner-context read succeeds, a different synthetic user sees zero rows, and cross-owner insert is rejected by RLS.
- That verification used simulated request JWT claims inside the database, not a real browser/PostgREST bearer session, so the real short-lived owner-session HTTP/PostgREST vertical slice remains pending.
- Repository auth/template implementation is ready: `supabase/templates/magic-link.html` already targets the server-side `/auth/confirm?token_hash=...` callback.
- Archive-owner magic-link delivery is working, but hosted Supabase Auth still sends the default direct-confirmation URL, so the checked-in template/Site URL has not yet been applied to the live project.
- VPS focused auth/session/API suite passes 35/35 tests; the full synthetic unit suite passes 201/201 tests.
- VPS project runtime has Supabase runtime/publishable configuration but no Supabase Management API token or CLI login; hosted Auth settings therefore cannot currently be changed from the VPS through the existing credential set.
- The connected remote execution layer correctly blocked forwarding a one-time auth token into a VPS command. No bypass was used and no one-time token was persisted.
- One synthetic RLS verification row currently remains in `letters`; no real archive-letter row exists.
- Supabase archive-owner Auth identity exists and is confirmed.
- The public-safe core schema is captured under `supabase/migrations/`.
- Domain code includes immutable source identity, SHA-256 fingerprints, processing versions, statuses/relationships, and smart filenames.
- Official filename pattern is `short-title__issuer__date__reference-number.ext`.
- Naming preserves Hindi/English/Hinglish Unicode and uses `undated` / `no-ref` placeholders.
- VPS OCR runtime has working Hindi/English Tesseract and OCRmyPDF through the configured commands.
- Connected Drive access can see the private archive and synthetic original, but the VPS `phone_drive` rclone credential cannot enumerate the archive contents even when given the archive/originals folder IDs directly; it is not suitable as the registry's runtime credential.
- Refreshable Drive OAuth/runtime wiring therefore remains pending.
- Gemini runtime remains unconfigured; an apparent Hermes reference was only example/commented configuration and no live key was available to reuse.
- No real archive-letter ingestion or production deployment has occurred.

## Next step

1. Apply the hosted Supabase magic-link template/Site URL for the server-readable token-hash callback flow.
2. Complete the authenticated owner-session HTTP/PostgREST synthetic vertical slice with a real short-lived session.
3. Configure and verify refreshable Google Drive OAuth runtime credentials using synthetic data only.
4. Verify private original streaming and the synthetic upload path end-to-end.
5. Configure and verify Gemini runtime credentials using synthetic data only.
6. Remove the retained synthetic DB verification row when an authorized cleanup path is available.
7. Re-check readiness before considering any real-letter intake.

No real-letter ingestion, historical adoption, Drive rename, connector activation, or production deployment is authorized by this state record.

## 2026-10-02 — RLS verification checkpoint

- Confirmed all public archive RLS policies are owner-scoped for the authenticated role.
- Synthetic owner insert/read succeeded.
- Synthetic wrong-user read returned zero rows.
- Synthetic cross-owner insert was denied by the RLS policy.
- This is DB-level claim simulation only; it does not replace the pending real user bearer-session/PostgREST test.
- Exactly one synthetic verification row remains in `letters`; no real archive record exists.

## 2026-10-02 — Runtime connectivity checkpoint

- Magic-link delivery to the authorized archive-owner mailbox was verified.
- Checked-in magic-link template is correct for server-side `token_hash` verification, but the hosted Supabase project still uses its default direct-confirmation template behavior.
- VPS auth/session/API tests: 35/35 passed.
- Full VPS synthetic unit suite: 201/201 passed.
- Existing Supabase runtime credentials are sufficient for application access but not for Management API Auth-template changes.
- Connected Google Drive access verified the private archive folder structure and existing synthetic-only original.
- VPS `phone_drive` rclone can resolve the supplied folder IDs without a hard error but returns empty listings and cannot enumerate the archive contents; it cannot be used as the registry runtime credential.
- Gemini runtime key remains unavailable.
- Refreshable Drive OAuth, original streaming, live Gemini verification, and the real owner bearer-session vertical slice remain pending.

## Last automated change
- Change: synchronize VPS runtime verification, credential findings, and canonical filename handoff
- Date: 2026-10-02
- Durable context synchronization: completed
