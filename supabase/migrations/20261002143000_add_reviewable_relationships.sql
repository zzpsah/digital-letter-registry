-- Reviewable relationship intelligence.
create type public.letter_relationship_review_status as enum (
  'suggested',
  'confirmed',
  'rejected'
);

alter table public.letter_relationships
  add column if not exists review_status public.letter_relationship_review_status not null default 'suggested',
  add column if not exists inference_version text not null default 'unversioned',
  add column if not exists rationale text,
  add column if not exists reviewed_at timestamptz;

create index if not exists letter_relationships_review_idx
  on public.letter_relationships (owner_id, review_status, relationship_type);

create or replace function public.confirm_letter_relationship(relationship_id uuid)
returns table (success boolean)
language plpgsql
volatile
security invoker
set search_path = public
as $$
declare
  rel public.letter_relationships%rowtype;
begin
  update public.letter_relationships r
  set review_status = 'confirmed',
      reviewed_at = now()
  where r.id = relationship_id
    and r.owner_id = auth.uid()
  returning * into rel;

  if not found then
    return query select false;
    return;
  end if;

  if rel.relationship_type = 'supersedes' then
    update public.letters l
    set status = 'superseded',
        updated_at = now()
    where l.id = rel.target_letter_id
      and l.owner_id = auth.uid();
  end if;

  return query select true;
end;
$$;

create or replace function public.reject_letter_relationship(relationship_id uuid)
returns table (success boolean)
language sql
volatile
security invoker
set search_path = public
as $$
  with updated as (
    update public.letter_relationships r
    set review_status = 'rejected',
        reviewed_at = now()
    where r.id = relationship_id
      and r.owner_id = auth.uid()
    returning r.id
  )
  select exists(select 1 from updated) as success;
$$;

grant execute on function public.confirm_letter_relationship(uuid) to authenticated;
grant execute on function public.reject_letter_relationship(uuid) to authenticated;
