# DLR worker operations and document audit

## Live topology

- Intake stores immutable originals in private Google Drive and creates the document/source rows in local PostgreSQL.
- `letters` is the searchable current document projection; `letter_processing` stores current extraction/context; `letter_sources` records intake and delivery state; `processing_jobs` is the durable queue.
- The local compatibility API at `127.0.0.1:8877` routes `/auth/v1` to GoTrue (`127.0.0.1:9999`) and `/rest/v1` to PostgREST (`127.0.0.1:3001`).
- The worker uses a dedicated GoTrue identity, a rotating refresh-token cache under `/home/prashant/.config/dlr/local-platform/worker-session.json`, and a lock beside that file. Never copy tokens into logs, reports, or Git.
- `dlr-worker.timer` invokes `dlr-worker.service` approximately once a minute. The service is `Type=oneshot` and claims one job. `inactive (dead)` after an idle/completed run is expected.
- OCR is serial on this VPS. A long document occupies the one-shot worker and delays later queue items; the timer does not launch a competing worker while the service is active.
- PDFs first use native text only when it passes readability checks. Otherwise OCRmyPDF/Tesseract uses `hin+eng`. OCR/context output is derived data; the Drive original is authoritative.
- Email/WhatsApp delivery is downstream and must be blocked for low OCR readability, `needs_reprocessing`, or context confidence below 0.60 unless a human review explicitly accepts the result.

## Reliability rules

1. Refresh the worker's GoTrue session before every PostgREST request. A job can outlive the access token loaded when the worker starts.
2. OCR hard timeout defaults to 2,400 seconds. Set `TimeoutStartSec=2700` on the systemd oneshot unit so systemd does not kill the worker before OCR's own timeout and error handling complete.
3. Each progress-stage update must refresh `processing_jobs.updated_at` (the worker lease heartbeat).
4. The worker runs a conditional stale-job recovery before claiming work: processing rows with a heartbeat older than 45 minutes are requeued while attempts are below three; exhausted jobs become failed and require review. The database migration 20261104190000_recover_stale_processing_jobs.sql adds the atomic claim-side equivalent and should be applied to the local PostgreSQL primary.
5. If the worker cannot write its failure status because the database/auth service is unavailable, it returns `failure_report_pending`; the stale-lease migration is the durable recovery path.
6. Do not add parallel OCR workers without a measured CPU/RAM/load test. Do not auto-send low-confidence results.

## Run a read-only full archive audit

Run from the repository with the protected worker identity injected by the scoped secret runner. Do not export or print credentials.

```bash
cd /home/prashant/projects/digital-letter-registry
secret-run-scoped \
  SUPABASE_WORKER_EMAIL=DLR_SUPABASE_WORKER_EMAIL \
  SUPABASE_WORKER_PASSWORD=DLR_SUPABASE_WORKER_PASSWORD \
  -- .venv/bin/python scripts/audit_document_pipeline.py
```

For machine-readable output, append `--format json`. The report is read-only and includes:
- all letters and processing rows in the configured archive;
- missing processing rows;
- OCR method/version counts;
- quality flags and documents needing human review;
- failed, pending, processing and stale jobs;
- email/WhatsApp delivery-state counts.

The script does not reprocess, approve, delete, resend, or change any document. The worker invokes the same stale-job recovery automatically before claiming a job; the audit reports current stale jobs without modifying them.

## Review documents in the UI

1. Open eLetters → Admin → Operations → Quality review.
2. Inspect the original PDF/image for every flagged item. Compare title, issuer, category, reference number, dates, amounts and summary.
3. Use Reprocess for OCR/extraction problems; wait for the job to complete and refresh the queue.
4. Use Confirm reviewed only when the displayed metadata is actually correct against the original. Missing reference/date can be legitimate for forms/manuals; do not invent values just to clear a flag.
5. Failed jobs require diagnosis before retry. A failed job caused by missing storage support is not an OCR problem.
6. Check pending/processing jobs separately from the quality-review queue. A document can have completed processing and still need review, or have no failed job while remaining stuck in `processing`.

## Versioned systemd units

The deployed unit definitions are versioned in `deploy/systemd/`. Keep the VPS copies in `/home/prashant/.config/systemd/user/` synchronized with these files. After changing them, run `systemctl --user daemon-reload`; verify the timer remains disabled while n8n is the primary scheduler and the service has a 45-minute start ceiling.

## Operational commands

```bash
systemctl --user is-enabled dlr-worker.timer  # expected: disabled
systemctl --user status dlr-worker.service --no-pager
systemctl --user status dlr-n8n-job-bridge.service --no-pager
journalctl --user -u dlr-worker.service --since '24 hours ago' --no-pager
ps -eo pid,etime,%cpu,%mem,args | grep -E '[o]crmypdf|[t]esseract'
```

Never interpret `dlr-worker.service: inactive (dead)` alone as an outage. Confirm the n8n worker workflow and private bridge are active, inspect the queue, and check whether a long OCR invocation is currently occupying the service. The systemd timer is expected to be disabled.

## Incident recorded 2026-11-04

A 51-page Hindi PDF had a corrupt legacy-font native text layer. The native extraction check accepted Latin-looking gibberish; low-confidence AI metadata was delivered. During manual reprocessing, OCRmyPDF hit the 900-second timeout. The worker then attempted to mark the job failed, but the worker's access JWT had expired; the `fail_processing_job` request returned HTTP 401 (`JWT expired`). The job remained `processing`, and the one-shot worker occupied the timer until OCR exited.

Corrective code now detects this legacy-font pattern, re-extracts unusable text on manual reprocess, refreshes the worker session before every database request, raises the OCR timeout to 2,400 seconds, updates the job heartbeat, and catches failure-report errors. The worker-level stale-job recovery is active in the deployed code. The SQL migration adds an atomic database-side guard and should also be applied to the local PostgreSQL primary.
