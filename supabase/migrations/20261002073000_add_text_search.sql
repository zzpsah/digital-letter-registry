-- First search layer: metadata/full-text/fuzzy ranking.
-- Public-safe: contains no project IDs, user IDs, Drive IDs, URLs, or credentials.

create index if not exists letters_smart_filename_trgm_idx
  on public.letters using gin (smart_filename gin_trgm_ops);

create index if not exists letters_authority_trgm_idx
  on public.letters using gin (authority gin_trgm_ops);

create index if not exists letter_processing_extracted_text_fts_idx
  on public.letter_processing
  using gin (to_tsvector('simple', coalesce(extracted_text, '')));

create or replace function public.search_letters(
  search_query text,
  result_limit integer default 25
)
returns table (
  id uuid,
  smart_filename text,
  title text,
  authority text,
  category text,
  issue_date date,
  status public.letter_status,
  action_required text,
  concepts text[],
  context_snippet text,
  text_rank real,
  fuzzy_rank real,
  combined_rank real
)
language sql
stable
security invoker
set search_path = public, extensions
as $$
  with normalized as (
    select nullif(btrim(search_query), '') as q
  ),
  ranked as (
    select
      l.id,
      l.smart_filename,
      l.title,
      l.authority,
      l.category,
      l.issue_date,
      l.status,
      l.action_required,
      p.concepts,
      case
        when p.extracted_text is null then null
        else left(p.extracted_text, 360)
      end as context_snippet,
      ts_rank_cd(
        to_tsvector(
          'simple',
          concat_ws(
            ' ',
            l.smart_filename,
            l.title,
            l.authority,
            l.category,
            l.subcategory,
            l.action_required,
            array_to_string(p.concepts, ' '),
            p.extracted_text
          )
        ),
        websearch_to_tsquery('simple', n.q)
      )::real as text_rank,
      greatest(
        similarity(coalesce(l.smart_filename, ''), n.q),
        similarity(coalesce(l.title, ''), n.q),
        similarity(coalesce(l.authority, ''), n.q)
      )::real as fuzzy_rank
    from public.letters l
    left join public.letter_processing p on p.letter_id = l.id
    cross join normalized n
    where n.q is not null
      and (
        to_tsvector(
          'simple',
          concat_ws(
            ' ',
            l.smart_filename,
            l.title,
            l.authority,
            l.category,
            l.subcategory,
            l.action_required,
            array_to_string(p.concepts, ' '),
            p.extracted_text
          )
        ) @@ websearch_to_tsquery('simple', n.q)
        or coalesce(l.smart_filename, '') % n.q
        or coalesce(l.title, '') % n.q
        or coalesce(l.authority, '') % n.q
      )
  )
  select
    r.id,
    r.smart_filename,
    r.title,
    r.authority,
    r.category,
    r.issue_date,
    r.status,
    r.action_required,
    r.concepts,
    r.context_snippet,
    r.text_rank,
    r.fuzzy_rank,
    (r.text_rank * 0.75 + r.fuzzy_rank * 0.25)::real as combined_rank
  from ranked r
  order by combined_rank desc, issue_date desc nulls last
  limit greatest(1, least(coalesce(result_limit, 25), 100));
$$;

grant execute on function public.search_letters(text, integer) to authenticated;
