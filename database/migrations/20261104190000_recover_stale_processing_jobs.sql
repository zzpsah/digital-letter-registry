-- Recover worker jobs stranded in `processing` after a process crash, timeout,
-- host restart, or expired auth session. The worker refreshes updated_at at each
-- progress boundary; OCR's configured hard timeout is 40 minutes, so 45
-- minutes without a heartbeat is treated as a stale lease.
-- Retry at most three total claims; exhausted stale jobs become visible failed
-- items instead of remaining permanently invisible in `processing`.

create index if not exists processing_jobs_processing_updated_idx
  on public.processing_jobs (updated_at)
  where status = 'processing';

create or replace function public.claim_processing_job()
returns table (
  id uuid,
  letter_id uuid,
  owner_id uuid,
  reason text,
  attempts integer,
  created_at timestamptz
)
language sql
volatile
security invoker
set search_path = public
as $$
  with stale_requeued as (
    update public.processing_jobs j
    set
      status = 'pending',
      claimed_by = null,
      available_at = now(),
      progress_stage = 'queued',
      progress_percent = 0,
      progress_detail = 'Recovered stale worker lease; retry queued',
      last_error = coalesce(j.last_error, 'Recovered stale processing lease after worker timeout/crash'),
      updated_at = now()
    where j.status = 'processing'
      and j.updated_at < now() - interval '45 minutes'
      and j.attempts < 3
      and (select private.archive_member_role(j.archive_id)) in ('admin','editor')
    returning j.id
  ),
  stale_exhausted as (
    update public.processing_jobs j
    set
      status = 'failed',
      claimed_by = null,
      progress_stage = 'failed',
      progress_detail = 'Automatic retries exhausted after stale worker lease',
      last_error = coalesce(j.last_error, 'Worker lease expired three times; administrator review required'),
      updated_at = now()
    where j.status = 'processing'
      and j.updated_at < now() - interval '45 minutes'
      and j.attempts >= 3
      and (select private.archive_member_role(j.archive_id)) in ('admin','editor')
    returning j.id
  ),
  candidate as (
    select j.id
    from public.processing_jobs j
    where (select private.archive_member_role(j.archive_id)) in ('admin','editor')
      and j.status = 'pending'
      and j.available_at <= now()
    order by j.created_at
    for update skip locked
    limit 1
  ),
  claimed as (
    update public.processing_jobs j
    set
      status = 'processing',
      claimed_by = auth.uid(),
      attempts = j.attempts + 1,
      started_at = now(),
      updated_at = now(),
      last_error = null
    where j.id = (select id from candidate)
    returning
      j.id,
      j.letter_id,
      j.owner_id,
      j.reason,
      j.attempts,
      j.created_at
  )
  select * from claimed;
$$;
