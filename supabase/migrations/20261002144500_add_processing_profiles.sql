-- Owner-scoped target processing profile and non-destructive reprocessing preview.

create table if not exists public.processing_profiles (
  owner_id uuid primary key references auth.users(id) on delete cascade,
  extraction_version text not null,
  context_version text not null,
  dictionary_version text not null,
  filename_rule_version text not null,
  category_schema_version text not null,
  embedding_version text not null,
  status_rule_version text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.processing_profiles enable row level security;

drop policy if exists "owners manage processing profiles"
  on public.processing_profiles;

create policy "owners manage processing profiles"
on public.processing_profiles
for all
to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);

create or replace function public.preview_reprocessing(
  result_limit integer default 100
)
returns table (
  letter_id uuid,
  title text,
  smart_filename text,
  differences text[]
)
language sql
stable
security invoker
set search_path = public
as $$
  with profile as (
    select *
    from public.processing_profiles
    where owner_id = auth.uid()
    limit 1
  ),
  compared as (
    select
      l.id as letter_id,
      l.title,
      l.smart_filename,
      array_remove(array[
        case when p.ocr_version <> pr.extraction_version then 'extraction' end,
        case when p.context_version <> pr.context_version then 'context' end,
        case when p.dictionary_version <> pr.dictionary_version then 'dictionary' end,
        case when p.filename_rule_version <> pr.filename_rule_version then 'filename_rule' end,
        case when p.category_schema_version <> pr.category_schema_version then 'category_schema' end,
        case when p.embedding_version <> pr.embedding_version then 'embedding' end,
        case when p.status_rule_version <> pr.status_rule_version then 'status_rule' end
      ], null) as differences
    from public.letters l
    join public.letter_processing p
      on p.letter_id = l.id
    cross join profile pr
    where l.owner_id = auth.uid()
  )
  select
    letter_id,
    title,
    smart_filename,
    differences
  from compared
  where cardinality(differences) > 0
  order by letter_id
  limit greatest(1, least(coalesce(result_limit, 100), 500));
$$;

grant execute on function public.preview_reprocessing(integer) to authenticated;
