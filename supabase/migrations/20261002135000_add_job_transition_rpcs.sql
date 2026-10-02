-- RLS-aware worker job transitions.

create or replace function public.complete_processing_job(job_id uuid)
returns table (success boolean)
language sql
volatile
security invoker
set search_path = public
as $$
  with updated as (
    update public.processing_jobs j
    set
      status = 'completed',
      completed_at = now(),
      updated_at = now(),
      last_error = null
    where j.id = job_id
      and j.owner_id = auth.uid()
      and j.status = 'processing'
    returning j.id
  )
  select exists(select 1 from updated) as success;
$$;

create or replace function public.fail_processing_job(
  job_id uuid,
  error_message text
)
returns table (success boolean)
language sql
volatile
security invoker
set search_path = public
as $$
  with updated as (
    update public.processing_jobs j
    set
      status = 'failed',
      updated_at = now(),
      last_error = left(coalesce(error_message, 'unknown processing error'), 2000)
    where j.id = job_id
      and j.owner_id = auth.uid()
      and j.status = 'processing'
    returning j.id
  )
  select exists(select 1 from updated) as success;
$$;

grant execute on function public.complete_processing_job(uuid) to authenticated;
grant execute on function public.fail_processing_job(uuid, text) to authenticated;
