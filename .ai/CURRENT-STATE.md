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
- Archive-owner magic-link delivery is working. The hosted email template still uses the default direct confirmation URL, while the application server callback expects a server-readable token-hash flow; this mismatch must be configured before browser/server auth is considered complete.
- The connected remote execution layer correctly blocked forwarding a one-time auth token into a VPS command. No bypass was used and no one-time token was persisted.
- One synthetic RLS verification row currently remains in `letters`; no real archive-letter row exists.
- Supabase archive-owner Auth identity exists and is confirmed.
- The public-safe core schema is captured under `supabase/migrations/`.
- Domain code includes immutable source identity, SHA-256 fingerprints, processing versions, statuses/relationships, and smart filenames.
- Official filename pattern is `short-title__issuer__date__reference-number.ext`.
- Naming preserves Hindi/English/Hinglish Unicode and uses `undated` / `no-ref` placeholders.
- GitHub CI runs the synthetic unit-test suite on pushes/PRs.
- VPS OCR runtime has working Hindi/English Tesseract and OCRmyPDF through the configured commands.
- The VPS's existing read-only rclone remote does not expose the private archive path, so refreshable Drive OAuth/runtime wiring remains pending.
- No real archive-letter ingestion or production deployment has occurred.

## Next step

1. Configure the hosted Supabase magic-link template/Site URL for the server-readable token-hash callback flow.
2. Complete the authenticated owner-session HTTP/PostgREST synthetic vertical slice with a real short-lived session.
3. Configure and verify refreshable Google Drive OAuth runtime credentials using synthetic data only.
4. Verify private original streaming and the synthetic upload path end-to-end.
5. Configure and verify Gemini runtime credentials using synthetic data only.
6. Remove the retained synthetic DB verification row when an authorized cleanup path is available.
7. Re-check readiness before considering any real-letter intake.

No real-letter ingestion, historical adoption, Drive rename, connector activation, or production deployment is authorized by this state record.

## 2026-10-02 — RLS verification checkpoint

- Read project rules, AGENTS, `.ai/`, root tasks/docs, and brain context before continuing integration work.
- Confirmed all public archive RLS policies are owner-scoped for the authenticated role.
- Synthetic owner insert/read succeeded.
- Synthetic wrong-user read returned zero rows.
- Synthetic cross-owner insert was denied by the RLS policy.
- This is DB-level claim simulation only; it does not replace the pending real user bearer-session/PostgREST test.
- Exactly one synthetic verification row remains in `letters`; no real archive record exists.
- No private project reference, owner UUID, token, Drive ID, credential, or server detail is recorded in Git.

## 2026-10-02 — Runtime connectivity checkpoint

- Magic-link delivery to the authorized archive-owner mailbox was verified.
- Default hosted Supabase email-template behavior was observed; it does not yet match the app's server callback token-hash flow.
- One-time auth-token forwarding into a remote VPS command was blocked by the connected execution safety boundary and was not bypassed.
- Connected Google Drive access verified the private archive folder structure and the existing synthetic-only original.
- Existing VPS rclone access was checked separately and does not expose the target archive path.
- Refreshable Drive OAuth, original streaming, and the real owner bearer-session vertical slice remain pending.

## Last automated change
- Change: synchronize runtime verification findings and next safe actions
- Date: 2026-10-02
- Durable context synchronization: completed
