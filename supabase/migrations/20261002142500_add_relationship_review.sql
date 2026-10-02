-- Reviewable relationship intelligence and conservative status recalculation.

create type public.relationship_review_status as enum (
  'suggested',
  'confirmed',
  'rejected'
);

alter table public.letter_relationships
  add column if not exists review_status public.relationship_review_status
    not null default 'suggested',
  add column if not exists relationship_version text
    not null default 'unversioned',
  add column if not exists rationale text,
  add column if not exists reviewed_at timestamptz;

create index if not exists letter_relationships_source_idx
  on public.letter_relationships (source_letter_id);

create index if not exists letter_relationships_review_idx
  on public.letter_relationships (owner_id, review_status, relationship_type);

create or replace function public.recalculate_letter_statuses(
  status_rule_version text default 'relationships-v1'
)
returns table (
  updated_superseded integer,
  updated_current integer
)
language plpgsql
volatile
security invoker
set search_path = public
as $$
declare
  superseded_count integer := 0;
  current_count integer := 0;
begin
  update public.letters l
  set
    status = 'superseded',
    updated_at = now()
  where l.owner_id = auth.uid()
    and exists (
      select 1
      from public.letter_relationships r
      where r.owner_id = l.owner_id
        and r.target_letter_id = l.id
        and r.relationship_type = 'supersedes'
        and r.review_status = 'confirmed'
    )
    and l.status <> 'superseded';

  get diagnostics superseded_count = row_count;

  update public.letters l
  set
    status = 'current',
    updated_at = now()
  where l.owner_id = auth.uid()
    and l.status = 'superseded'
    and not exists (
      select 1
      from public.letter_relationships r
      where r.owner_id = l.owner_id
        and r.target_letter_id = l.id
        and r.relationship_type = 'supersedes'
        and r.review_status = 'confirmed'
    );

  get diagnostics current_count = row_count;

  update public.letter_processing p
  set
    status_rule_version = recalculate_letter_statuses.status_rule_version,
    updated_at = now()
  where p.owner_id = auth.uid();

  return query
    select superseded_count, current_count;
end;
$$;

grant execute on function public.recalculate_letter_statuses(text) to authenticated;
