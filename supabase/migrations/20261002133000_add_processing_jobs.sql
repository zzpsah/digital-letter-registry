-- Durable derived-processing job queue.
-- RLS ownership follows the same auth.uid() model as archive records.

create type public.processing_job_status as enum (
  'pending',
  'processing',
  'completed',
  'failed'
);

create table public.processing_jobs (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  letter_id uuid not null references public.letters(id) on delete cascade,
  status public.processing_job_status not null default 'pending',
  reason text not null default 'initial_processing',
  attempts integer not null default 0 check (attempts >= 0),
  last_error text,
  available_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (letter_id, reason)
);

create index processing_jobs_owner_status_available_idx
  on public.processing_jobs (owner_id, status, available_at);

create index processing_jobs_letter_idx
  on public.processing_jobs (letter_id);

alter table public.processing_jobs enable row level security;

create policy "owners manage processing jobs"
on public.processing_jobs
for all
to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);
