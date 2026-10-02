-- Explicitly enqueue reprocessing after preview/approval.
-- Each target-version profile gets a stable reason hash so the same upgrade
-- is idempotent while future profile changes can enqueue again.

create or replace function public.enqueue_reprocessing_jobs(
  result_limit integer default 500
)
returns table (enqueued integer)
language plpgsql
volatile
security invoker
set search_path = public
as $$
declare
  inserted_count integer := 0;
  profile_hash text;
begin
  select md5(concat_ws(
    '|',
    extraction_version,
    context_version,
    dictionary_version,
    filename_rule_version,
    category_schema_version,
    embedding_version,
    status_rule_version
  ))
  into profile_hash
  from public.processing_profiles
  where owner_id = auth.uid();

  if profile_hash is null then
    return query select 0;
    return;
  end if;

  insert into public.processing_jobs (
    owner_id,
    letter_id,
    status,
    reason
  )
  select
    auth.uid(),
    preview.letter_id,
    'pending',
    'reprocess:' || profile_hash
  from public.preview_reprocessing(
    greatest(1, least(coalesce(result_limit, 500), 500))
  ) preview
  on conflict (letter_id, reason) do nothing;

  get diagnostics inserted_count = row_count;
  return query select inserted_count;
end;
$$;

grant execute on function public.enqueue_reprocessing_jobs(integer)
to authenticated;
