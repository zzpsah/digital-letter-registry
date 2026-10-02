-- Candidate discovery for reviewable letter relationships.
-- Returns older same-owner letters with a deterministic similarity score.

create or replace function public.find_relationship_candidates(
  source_letter_id uuid,
  result_limit integer default 12
)
returns table (
  target_letter_id uuid,
  target_title text,
  target_authority text,
  target_category text,
  target_reference_number text,
  target_issue_date date,
  target_concepts text[],
  candidate_score real
)
language sql
stable
security invoker
set search_path = public, extensions
as $$
  with source as (
    select
      l.id,
      l.owner_id,
      l.title,
      l.authority,
      l.category,
      l.reference_number,
      l.issue_date,
      coalesce(p.concepts, '{}'::text[]) as concepts
    from public.letters l
    left join public.letter_processing p on p.letter_id = l.id
    where l.id = source_letter_id
      and l.owner_id = auth.uid()
  )
  select
    t.id as target_letter_id,
    t.title as target_title,
    t.authority as target_authority,
    t.category as target_category,
    t.reference_number as target_reference_number,
    t.issue_date as target_issue_date,
    coalesce(tp.concepts, '{}'::text[]) as target_concepts,
    (
      case
        when lower(coalesce(t.authority, '')) = lower(coalesce(s.authority, ''))
             and coalesce(s.authority, '') <> ''
        then 0.25 else 0
      end
      +
      case
        when lower(coalesce(t.category, '')) = lower(coalesce(s.category, ''))
             and coalesce(s.category, '') <> ''
        then 0.15 else 0
      end
      +
      case
        when lower(coalesce(t.reference_number, '')) =
             lower(coalesce(s.reference_number, ''))
             and coalesce(s.reference_number, '') <> ''
        then 0.25 else 0
      end
      +
      greatest(
        similarity(coalesce(t.title, ''), coalesce(s.title, '')),
        0
      ) * 0.25
      +
      case
        when coalesce(tp.concepts, '{}'::text[]) && s.concepts
        then 0.10 else 0
      end
    )::real as candidate_score
  from source s
  join public.letters t
    on t.owner_id = s.owner_id
   and t.id <> s.id
  left join public.letter_processing tp on tp.letter_id = t.id
  where
    (
      s.issue_date is null
      or t.issue_date is null
      or t.issue_date <= s.issue_date
    )
    and (
      lower(coalesce(t.authority, '')) = lower(coalesce(s.authority, ''))
      or lower(coalesce(t.category, '')) = lower(coalesce(s.category, ''))
      or lower(coalesce(t.reference_number, '')) =
         lower(coalesce(s.reference_number, ''))
      or similarity(coalesce(t.title, ''), coalesce(s.title, '')) >= 0.20
      or coalesce(tp.concepts, '{}'::text[]) && s.concepts
    )
  order by candidate_score desc, t.issue_date desc nulls last
  limit greatest(1, least(coalesce(result_limit, 12), 50));
$$;

grant execute on function public.find_relationship_candidates(uuid, integer)
to authenticated;
