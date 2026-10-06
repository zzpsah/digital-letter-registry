-- Persist user-visible processing progress for intake/reprocess jobs.
alter table public.processing_jobs
  add column if not exists progress_stage text not null default 'queued',
  add column if not exists progress_percent integer not null default 0,
  add column if not exists progress_detail text;
alter table public.processing_jobs drop constraint if exists processing_jobs_progress_percent_check;
alter table public.processing_jobs add constraint processing_jobs_progress_percent_check check (progress_percent between 0 and 100);
