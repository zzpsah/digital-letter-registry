# Worker Session Reuse — 2026-10-12

## Problem

Supabase Auth logs for 11–12 Oct 2026 showed, for the single worker identity
`umvtetahali+dlrworker@gmail.com` (user-agent `Python-urllib/3.12`):

- 7,979 successful `POST /auth/v1/token?grant_type=password` requests in 24h
- ~56,500 sessions associated with the worker account

## Root cause

Every DLR background service is a `Type=oneshot` systemd unit on a one-minute
timer, so a fresh process authenticates on every cycle. Four of those services
call `SupabasePostgrestTransport.from_worker_environment()`, which performed a
`grant_type=password` sign-in on each start:

| Service | Script | Calls worker auth |
|---|---|---|
| `dlr-worker` | `scripts/run_worker_once.py` | yes |
| `dlr-postprocess-delivery` | `scripts/dlr-postprocess-delivery.py` | yes |
| `dlr-account-access-mailer` | `scripts/dlr-account-access-mailer.py` | yes |
| `dlr-index-refresh` | `scripts/dlr-index-publish.py` | yes |
| `dlr-gmail-outbox` | `scripts/dlr-gmail-outbox-send.py` | no (Gmail only) |
| `dlr-whatsapp-intake` | intake consumer | only when an item is pending |

Measured over 24h: each of the four services started 1,333–1,339 times
(~5,336 runs/day), plus intake runs and manual invocations — matching the 7,979
observed grants.

There was **no duplicate worker instance**. `ps` showed no long-lived DLR
process, and `dlr-worker.service` is `oneshot`. The volume was one password
grant per process start, multiplied by timer frequency.

## Fix

New `src/letter_registry/worker_session.py` caches one worker session on disk
and reuses it:

1. A cached access token that is still comfortably valid (>300s to expiry) is
   reused as-is — no network auth at all.
2. Otherwise the rotating refresh token is used to refresh.
3. A password grant is the last resort (cold cache, or a rejected refresh).

Concurrency: several timers fire on the same minute, and Supabase rotates the
refresh token on every use, so two concurrent refreshes would invalidate each
other. A `flock`-protected lock serialises the read-refresh-write cycle, and the
cache is re-read **after** acquiring the lock so a loser reuses the winner's
session instead of rotating again.

Safety properties:

- Cache file `0600`, state dir `0700`, written atomically via `os.replace`.
- A `written_at` trust ceiling means an edited/stale cache cannot pin a dead
  token beyond the real token lifetime.
- `refresh_only=True` (used by the health probe) can never perform a password
  grant, so the probe cannot mask the regression it detects.
- Auth failures raise `WorkerSessionError` from a single bounded attempt; no
  message contains credential material.
- `from_worker_environment()` keeps its signature and still returns a transport
  carrying a user access token, so RLS scoping and job/notification semantics
  are unchanged.

## Verification

- Full suite: 353 tests, `OK` (before and after rebase).
- Concurrency: 8 parallel loads produce exactly 1 password grant.
- Live reuse: 24 service runs over a 360s window produced **0** auth events.
- Refresh under contention: 4 services started simultaneously refreshed once,
  all returned `success`, no lock timeout.
- Live authenticated reads through the cached session: 44 letters, 64
  processing_jobs, 48 letter_sources.
- Semantics intact: worker `status=idle`, account mailer
  `{"status":"ok","request_notifications":0,...}`, pipeline
  `{"complete":38,"failed":2,"partial":4}`, index publisher
  `{"status":"ok","documents":41,...}`.
- Health watchdog: silent when healthy; alerting when the cache is removed.

## Polling vs duplicate processing

The 2,658 `dlr_claim_account_notifications` calls and 2,652 job-insert requests
are legitimate polling, not duplicate processing:

- `enqueue` uses `on_conflict="letter_id,reason"` with
  `resolution=ignore-duplicates`, so a repeated insert is a no-op.
- 64 jobs across 44 distinct letters; 8 letters have >1 job, and every one has
  a **distinct reason** (`initial_processing`, `quality-upgrade:<hash>`,
  `manual_retry:<ts>`, `manual_reprocess:<ts>`) — legitimate re-processing, no
  duplicate `(letter_id, reason)` pairs.
- 44 letters, 44 distinct `original_sha256` — no duplicate content.
- 44 `letter_processing` rows, zero letters with more than one.

No jobs, records, or sessions were deleted.

## Remaining failures (pre-existing, not caused by this change)

3 `processing_jobs` rows are `failed`, all created 2026-10-06/08:

- `643761fc` (letter `636c7afc`) — Supabase HTTP 403, RLS policy violation
- `a3fbca8d` (letter `0564404b`) — Supabase HTTP 403, RLS policy violation
- `c0113edd` (letter `67bfaab2`) — `OCRmyPDF timed out`

The two 403s predate this work and point at an RLS/insert path for
`manual_reprocess`, unrelated to authentication volume. Not addressed here.

## Independent Supabase log follow-up — 2026-10-12

A separate read-only check of the project's Supabase edge logs was performed
after the deployment report. This verifies observed Auth API traffic; it does
not independently verify the worker filesystem or source revision.

Window checked: **2026-10-12 06:00–08:15 UTC**.

- `POST /auth/v1/token?grant_type=password`: **0** requests.
- `POST /auth/v1/token?grant_type=refresh_token`: **3** requests, all HTTP
  200.
- In an earlier transition window (04:00–06:00 UTC), password-grant requests
  were still present. This may reflect pre-fix/older invocations or another
  caller; the logs alone do not identify the process responsible.
- Therefore the latest window supports that session reuse is operating, but
  a full 24-hour post-deployment observation is still needed before declaring
  the regression permanently resolved.

No database rows, sessions, users, or Auth settings were modified during this
check. The two pre-existing manual-reprocess HTTP 403/RLS failures and the
OCRmyPDF timeout remain separate unresolved items.
