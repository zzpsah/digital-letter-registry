-- Additive processing lineage. Existing projections remain unchanged.
create type public.processing_run_status as enum ('pending','running','completed','failed','cancelled');

create table public.processing_runs (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  letter_id uuid not null references public.letters(id) on delete cascade,
  job_id uuid references public.processing_jobs(id) on delete set null,
  reason text not null,
  processor_profile jsonb not null default '{}'::jsonb,
  status public.processing_run_status not null default 'pending',
  started_at timestamptz,
  completed_at timestamptz,
  failure_stage text,
  last_error text,
  created_at timestamptz not null default now()
);

create table public.extraction_artifacts (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  letter_id uuid not null references public.letters(id) on delete cascade,
  run_id uuid references public.processing_runs(id) on delete set null,
  method text not null,
  provider text not null,
  engine_version text not null,
  languages text[] not null default '{}'::text[],
  extracted_text text not null,
  page_count integer,
  page_data jsonb not null default '[]'::jsonb,
  quality_score numeric,
  is_preferred boolean not null default false,
  created_at timestamptz not null default now(),
  check (page_count is null or page_count > 0),
  check (quality_score is null or (quality_score >= 0 and quality_score <= 1))
);

create unique index extraction_artifacts_one_preferred
  on public.extraction_artifacts(letter_id) where is_preferred;

create table public.interpretation_artifacts (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  letter_id uuid not null references public.letters(id) on delete cascade,
  run_id uuid references public.processing_runs(id) on delete set null,
  extraction_artifact_id uuid references public.extraction_artifacts(id) on delete set null,
  provider text not null,
  model text not null,
  schema_version text not null,
  prompt_version text not null,
  output_language text,
  structured_context jsonb not null,
  confidence numeric,
  is_preferred boolean not null default false,
  created_at timestamptz not null default now(),
  check (confidence is null or (confidence >= 0 and confidence <= 1))
);

create unique index interpretation_artifacts_one_preferred
  on public.interpretation_artifacts(letter_id) where is_preferred;

create index processing_runs_owner_letter_created_idx on public.processing_runs(owner_id, letter_id, created_at desc);
create index extraction_artifacts_letter_created_idx on public.extraction_artifacts(letter_id, created_at desc);
create index interpretation_artifacts_letter_created_idx on public.interpretation_artifacts(letter_id, created_at desc);

alter table public.processing_runs enable row level security;
alter table public.extraction_artifacts enable row level security;
alter table public.interpretation_artifacts enable row level security;

create policy "owners manage processing runs" on public.processing_runs
for all to authenticated using ((select auth.uid()) = owner_id) with check ((select auth.uid()) = owner_id);
create policy "owners manage extraction artifacts" on public.extraction_artifacts
for all to authenticated using ((select auth.uid()) = owner_id) with check ((select auth.uid()) = owner_id);
create policy "owners manage interpretation artifacts" on public.interpretation_artifacts
for all to authenticated using ((select auth.uid()) = owner_id) with check ((select auth.uid()) = owner_id);
