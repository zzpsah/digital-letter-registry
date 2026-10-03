-- Allow a dedicated archive worker to process jobs created by human editors
-- without changing the document/audit owner.

alter table public.processing_jobs
  add column if not exists claimed_by uuid references auth.users(id) on delete set null;

create index if not exists processing_jobs_claimed_by_idx
  on public.processing_jobs (claimed_by)
  where claimed_by is not null;

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
      and j.claimed_by = auth.uid()
      and (select private.archive_member_role(j.archive_id)) in ('admin','editor')
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
      and j.claimed_by = auth.uid()
      and (select private.archive_member_role(j.archive_id)) in ('admin','editor')
      and j.status = 'processing'
    returning j.id
  )
  select exists(select 1 from updated) as success;
$$;

drop policy if exists "archive editors insert letter processing"
  on public.letter_processing;
create policy "archive editors insert letter processing"
on public.letter_processing for insert to authenticated
with check (
  (select private.archive_member_role(archive_id)) in ('admin','editor')
  and exists (
    select 1 from public.letters l
    where l.id = letter_id
      and l.archive_id = archive_id
      and l.owner_id = owner_id
  )
);

drop policy if exists "archive editors insert letter chunks"
  on public.letter_chunks;
create policy "archive editors insert letter chunks"
on public.letter_chunks for insert to authenticated
with check (
  (select private.archive_member_role(archive_id)) in ('admin','editor')
  and exists (
    select 1 from public.letters l
    where l.id = letter_id
      and l.archive_id = archive_id
      and l.owner_id = owner_id
  )
);

drop policy if exists "archive editors insert letter relationships"
  on public.letter_relationships;
create policy "archive editors insert letter relationships"
on public.letter_relationships for insert to authenticated
with check (
  (select private.archive_member_role(archive_id)) in ('admin','editor')
  and exists (
    select 1 from public.letters l
    where l.id = source_letter_id
      and l.archive_id = archive_id
      and l.owner_id = owner_id
  )
);
