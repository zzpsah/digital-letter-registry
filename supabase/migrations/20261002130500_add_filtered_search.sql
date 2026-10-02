-- Filtered archive search for the mobile/API layer.
-- Security invoker preserves RLS. No private identifiers are exposed by the function.

create or replace function public.search_letters_filtered(
  search_query text default null,
  authority_filter text default null,
  category_filter text default null,
  status_filter public.letter_status default null,
  year_filter integer default null,
  file_type_filter text default null,
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
  file_type text,
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
      lower(nullif(regexp_replace(coalesce(l.original_filename, ''), '^.*\.', ''), coalesce(l.original_filename, ''))) as file_type,
      case
        when n.q is null then 0::real
        else ts_rank_cd(
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
        )::real
      end as text_rank,
      case
        when n.q is null then 0::real
        else greatest(
          similarity(coalesce(l.smart_filename, ''), n.q),
          similarity(coalesce(l.title, ''), n.q),
          similarity(coalesce(l.authority, ''), n.q)
        )::real
      end as fuzzy_rank
    from public.letters l
    left join public.letter_processing p on p.letter_id = l.id
    cross join normalized n
    where
      (authority_filter is null or lower(coalesce(l.authority, '')) = lower(authority_filter))
      and (category_filter is null or lower(coalesce(l.category, '')) = lower(category_filter))
      and (status_filter is null or l.status = status_filter)
      and (year_filter is null or extract(year from l.issue_date)::integer = year_filter)
      and (
        file_type_filter is null
        or lower(nullif(regexp_replace(coalesce(l.original_filename, ''), '^.*\.', ''), coalesce(l.original_filename, ''))) = lower(file_type_filter)
      )
      and (
        n.q is null
        or to_tsvector(
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
    r.file_type,
    r.text_rank,
    r.fuzzy_rank,
    (r.text_rank * 0.75 + r.fuzzy_rank * 0.25)::real as combined_rank
  from ranked r
  order by
    case when (select q from normalized) is null then 0 else combined_rank end desc,
    issue_date desc nulls last
  limit greatest(1, least(coalesce(result_limit, 25), 100));
$$;

grant execute on function public.search_letters_filtered(
  text, text, text, public.letter_status, integer, text, integer
) to authenticated;
