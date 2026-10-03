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
- The canonical user-facing control plane is now the public Vercel URL with password-first auth. The private Oracle HTTPS origin remains an operational/private-worker endpoint rather than the normal user entrypoint.
- Magic-link email throttling is now surfaced safely as HTTP 429 instead of an internal 500.
- Public Vercel control-plane deployment is live; no real archive-letter ingestion has occurred and real intake remains disabled.
- On 2026-10-03, the bootstrap admin successfully updated the DLR password through the live Account flow. This completes the real password-setup milestone; no password value is stored or logged in repository state.
- Live Supabase membership verification on 2026-10-03 shows two active admins and one active viewer. The earlier second-admin invite is accepted. Archive letters and processing jobs remain at zero.

## Next step

1. Provision a dedicated non-human Supabase worker account with the minimum archive role required for processing.
2. Store only that worker email/password in Bitwarden as `DLR_SUPABASE_WORKER_EMAIL` and `DLR_SUPABASE_WORKER_PASSWORD`; never reuse a human admin password/session.
3. Enable the already-installed Oracle `dlr-worker.timer` only after those secrets exist and a one-shot worker login/idle test passes.
4. Complete the synthetic upload → Drive → queue → Oracle worker → Vercel search/open-original vertical slice.
5. Keep `ENABLE_REAL_INTAKE=false` throughout synthetic verification.
6. Gemini remains optional; add it later for richer structured context and semantic embeddings, then reprocess historical items.

Public Vercel hosting is authorized and live. Real-letter ingestion, historical adoption, Drive rename/delete operations, and real connector intake remain disabled unless explicitly enabled later.

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
- Scoped Oracle runtime readiness now passes fully in synthetic-only mode.
- Gemini runtime key remains unavailable, but this is no longer a baseline blocker because deterministic OCR/full-text context fallback is active.
- Drive write verification is complete with synthetic data; semantic embeddings remain a later optional enhancement.

## Last automated change
- Commit: cd40cfcb5269e5e7d788f405938f3be9cf72d533
- Change: feat: support dedicated password-authenticated worker transport
- Date: 2026-10-03
- Durable context synchronization: completed


## Dedicated worker authentication readiness

The worker no longer requires a manually copied human `SUPABASE_ACCESS_TOKEN` as its only option. `SupabasePostgrestTransport.from_worker_environment()` now supports:

- direct `SUPABASE_ACCESS_TOKEN` only for one-shot/manual integration tests;
- preferred background mode: `SUPABASE_WORKER_EMAIL` + `SUPABASE_WORKER_PASSWORD`, which signs in a dedicated non-human account and obtains a fresh short-lived user access token each run.

This preserves normal Supabase RLS rather than using service-role credentials in the Oracle worker.

Oracle has the Bitwarden-scoped worker wrapper and systemd service/timer files installed, but the timer is deliberately disabled/inactive until the dedicated worker account and Bitwarden secret pair are provisioned.

Latest synthetic suite: 264/264 PASS.
