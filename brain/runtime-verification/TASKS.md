# Runtime Verification — Tasks

- [x] Inspect public archive RLS policies.
- [x] Verify synthetic owner-context insert/read at DB level.
- [x] Verify wrong-user invisibility at DB level.
- [x] Verify cross-owner insert denial at DB level.
- [ ] Complete real short-lived authenticated HTTP/PostgREST synthetic vertical slice.
- [ ] Verify refreshable Drive OAuth with synthetic data.
- [ ] Verify original streaming end-to-end.
- [ ] Verify Gemini with synthetic data.
- [ ] Configure hosted magic-link template/Site URL.
- [ ] Remove retained synthetic RLS verification row through an authorized cleanup path.
- [ ] Re-run readiness and sync all affected docs/context.

- [x] Verify Bitwarden worker secret injection path reaches Supabase Auth.
- [x] Create dedicated worker signup using the existing Bitwarden-backed credentials.
- [x] Complete worker email confirmation.
- [x] Assign/verify minimum editor membership for the worker.
- [x] Run one-shot worker login/idle verification before enabling the timer.
- [x] Enable and verify `dlr-worker.timer` with real intake still disabled.

- [x] Complete synthetic upload → Drive → queue → worker → search/open-original vertical slice.
