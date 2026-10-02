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
- Archive-owner magic-link delivery is working. The hosted project uses Supabase's default direct-confirmation email because the Dashboard requires custom SMTP before editing template subject/body. The application now supports that default flow with a hardened fragment bridge at `/auth/confirm`: browser fragment tokens are posted same-origin, the server validates the authenticated owner, stores only HttpOnly cookies, and clears the URL. The checked-in token-hash template remains an optional future path if custom SMTP is enabled.
- VPS auth/API suite passes 29/29 tests after default-flow and rate-limit handling; the full synthetic unit suite passes 209/209 tests. The Supabase Management Auth-config helper focused suite passes 4/4.
- VPS project runtime has Supabase runtime/publishable configuration but no Supabase Management API token or CLI login; hosted Auth settings therefore cannot currently be changed from the VPS through the existing credential set. A guarded Management API helper is now implemented and ready once a scoped runtime management token is supplied.
- The connected remote execution layer correctly blocked forwarding a one-time auth token into a VPS command. No bypass was used and no one-time token was persisted.
- The retained synthetic RLS verification row was removed through a controlled exact-match cleanup; `letters` now contains zero rows.
- Supabase archive-owner Auth identity exists and is confirmed.
- The public-safe core schema is captured under `supabase/migrations/`.
- Domain code includes immutable source identity, SHA-256 fingerprints, processing versions, statuses/relationships, and smart filenames.
- Official filename pattern is `short-title__issuer__date__reference-number.ext`.
- Naming preserves Hindi/English/Hinglish Unicode and uses `undated` / `no-ref` placeholders.
- VPS OCR runtime has working Hindi/English Tesseract and OCRmyPDF through the configured commands.
- Connected Drive access can see the private archive and synthetic original, but the VPS `phone_drive` rclone credential cannot enumerate the archive contents even when given the archive/originals folder IDs directly; it is not suitable as the registry's runtime credential.
- Refreshable Drive OAuth/runtime wiring therefore remains pending.
- Gemini runtime remains unconfigured; an apparent Hermes reference was only example/commented configuration and no live key was available to reuse.
- A dedicated Google OAuth client exists in a private vault from the earlier OAuth attempt, but Bitwarden CLI is unavailable on both connected Windows and VPS paths, so the credential cannot be programmatically retrieved through the current tool path.
- DLR runtime is isolated on its own tailnet-only HTTPS endpoint; it no longer shares the localhost/shared origin previously used during testing. The exact private endpoint is runtime-only and is not recorded in public Git.
- Supabase Site URL and redirect allow-list are aligned to that dedicated private HTTPS origin. A device opening a magic link must be connected to the authorized tailnet; no public-internet exposure is enabled.
- Magic-link email throttling is now surfaced safely as HTTP 429 instead of an internal 500.
- No real archive-letter ingestion or production deployment has occurred.

## Next step

1. Complete the authenticated owner-session HTTP/PostgREST synthetic vertical slice with a real short-lived session using the dedicated tailnet-only HTTPS callback. Current blocker is Supabase email-send throttling, not routing or application health.
2. Configure and verify refreshable Google Drive OAuth runtime credentials using synthetic data only.
3. Verify private original streaming and the synthetic upload path end-to-end.
4. Configure and verify Gemini runtime credentials using synthetic data only.
5. Retained synthetic DB verification row cleanup is complete; no rows remain in `letters`.
6. Re-check readiness before considering any real-letter intake.
7. Optional later: enable custom SMTP and apply the checked-in token-hash email template.

No real-letter ingestion, historical adoption, Drive rename, connector activation, or production deployment is authorized by this state record.

## 2026-10-02 — RLS verification checkpoint

- Confirmed all public archive RLS policies are owner-scoped for the authenticated role.
- Synthetic owner insert/read succeeded.
- Synthetic wrong-user read returned zero rows.
- Synthetic cross-owner insert was denied by the RLS policy.
- This is DB-level claim simulation only; it does not replace the pending real user bearer-session/PostgREST test.
- The synthetic verification row was removed after the RLS test; `letters` now contains zero rows.

## 2026-10-02 — Runtime connectivity checkpoint

- Magic-link delivery to the authorized archive-owner mailbox was verified.
- Checked-in magic-link template is correct for server-side `token_hash` verification, while the hosted Supabase project uses default direct-confirmation behavior because custom SMTP is required to edit email templates.
- Default hosted callback compatibility is implemented and hardened (`no-store`, `no-referrer`, CSP, owner validation, HttpOnly cookies, URL cleanup).
- VPS auth/API tests: 29/29 passed.
- Full VPS synthetic unit suite: 209/209 passed.
- Dedicated tailnet-only HTTPS routing verified from an authorized tailnet client.
- Supabase Management Auth-config helper focused suite: 4/4 passed.
- Existing Supabase runtime credentials are sufficient for application access but not for Management API Auth-template changes.
- Connected Google Drive access verified the private archive folder structure and existing synthetic-only original.
- VPS `phone_drive` rclone can resolve the supplied folder IDs without a hard error but returns empty listings and cannot enumerate the archive contents; it cannot be used as the registry runtime credential.
- Gemini runtime key remains unavailable.
- Refreshable Drive OAuth, original streaming, live Gemini verification, and the real owner bearer-session vertical slice remain pending.

## Last automated change
- Commit: 687eb7c48a7595f6a3b07b8b817d3768884cc5d5
- Change: feat: support file-based Google Drive OAuth
- Date: 2026-10-02
- Durable context synchronization: completed
