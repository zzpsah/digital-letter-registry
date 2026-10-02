-- Atomic RLS-aware job claiming for derived processing workers.

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
  with candidate as (
    select j.id
    from public.processing_jobs j
    where j.owner_id = auth.uid()
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

grant execute on function public.claim_processing_job() to authenticated;
