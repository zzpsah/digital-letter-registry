-- Owner-scoped target processing versions and safe reprocessing preview.

create table public.processing_profiles (
  owner_id uuid primary key references auth.users(id) on delete cascade,
  extraction_version text not null default 'unprocessed',
  context_version text not null default 'unprocessed',
  dictionary_version text not null default 'unprocessed',
  filename_rule_version text not null default 'unprocessed',
  category_schema_version text not null default 'unprocessed',
  embedding_version text not null default 'unprocessed',
  status_rule_version text not null default 'unprocessed',
  updated_at timestamptz not null default now()
);

alter table public.processing_profiles enable row level security;

create policy "owners manage processing profile"
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
  select
    l.id as letter_id,
    l.title,
    l.smart_filename,
    array_remove(array[
      case when p.ocr_version is distinct from profile.extraction_version
        then 'extraction' end,
      case when p.context_version is distinct from profile.context_version
        then 'context' end,
      case when p.dictionary_version is distinct from profile.dictionary_version
        then 'dictionary' end,
      case when p.filename_rule_version is distinct from profile.filename_rule_version
        then 'filename_rule' end,
      case when p.category_schema_version is distinct from profile.category_schema_version
        then 'category_schema' end,
      case when p.embedding_version is distinct from profile.embedding_version
        then 'embedding' end,
      case when p.status_rule_version is distinct from profile.status_rule_version
        then 'status_rule' end
    ], null) as differences
  from public.letters l
  join public.letter_processing p on p.letter_id = l.id
  join public.processing_profiles profile on profile.owner_id = l.owner_id
  where l.owner_id = auth.uid()
    and (
      p.ocr_version is distinct from profile.extraction_version
      or p.context_version is distinct from profile.context_version
      or p.dictionary_version is distinct from profile.dictionary_version
      or p.filename_rule_version is distinct from profile.filename_rule_version
      or p.category_schema_version is distinct from profile.category_schema_version
      or p.embedding_version is distinct from profile.embedding_version
      or p.status_rule_version is distinct from profile.status_rule_version
    )
  order by l.received_at desc
  limit greatest(1, least(coalesce(result_limit, 100), 500));
$$;

grant execute on function public.preview_reprocessing(integer) to authenticated;
