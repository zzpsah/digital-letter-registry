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
- Supabase Site URL and redirect allow-list are aligned to that dedicated private HTTPS origin. A device opening a magic link must be connected to the authorized tailnet; no public-internet exposure is enabled.
- Magic-link email throttling is now surfaced safely as HTTP 429 instead of an internal 500.
- No real archive-letter ingestion or production deployment has occurred.

## Next step

1. Complete the authenticated owner-session HTTP/PostgREST synthetic vertical slice with a real short-lived session using the dedicated tailnet-only HTTPS callback. Current blocker is Supabase email-send throttling, not routing or application health.
2. Refreshable Google Drive OAuth is complete with secret-manager-backed write-capable access; read/list/stream plus disposable synthetic upload/delete verification passed.
3. Synthetic upload/write verification is complete; real archive mutations remain separately disabled/approval-gated.
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
- Full VPS synthetic unit suite: 212/212 passed.
- Dedicated tailnet-only HTTPS routing verified from an authorized tailnet client.
- Supabase Management Auth-config helper focused suite: 4/4 passed.
- Existing Supabase runtime credentials are sufficient for application access but not for Management API Auth-template changes.
- Secret-manager-backed Google Drive OAuth runtime is configured and verified with a write-capable grant; refresh/list/stream and disposable synthetic upload/stream/delete cleanup all passed.
- The older `phone_drive` rclone path remains separate and unused by DLR.
- Runtime readiness now reports Drive credentials configured; Gemini is the only failing readiness check.
- Gemini runtime key remains unavailable.
- Live Gemini verification and the real owner bearer-session vertical slice remain pending; Drive write verification is complete with synthetic data.

## Last automated change
- Commit: 59bf8840952237ba060be4210f295c2e319f14f6
- Change: feat: treat Gemini as optional with deterministic fallback
- Date: 2026-10-03
- Durable context synchronization: completed
