-- Explicit review actions for suggested letter relationships.
-- Reuses the canonical relationship_review_status schema added earlier.

create or replace function public.review_letter_relationship(
  relationship_id uuid,
  decision public.relationship_review_status
)
returns table (success boolean)
language plpgsql
volatile
security invoker
set search_path = public
as $$
begin
  if decision not in ('confirmed', 'rejected') then
    return query select false;
    return;
  end if;

  update public.letter_relationships r
  set review_status = decision,
      reviewed_at = now()
  where r.id = relationship_id
    and r.owner_id = auth.uid();

  if not found then
    return query select false;
    return;
  end if;

  perform public.recalculate_letter_statuses('relationships-v1');
  return query select true;
end;
$$;

grant execute on function public.review_letter_relationship(
  uuid,
  public.relationship_review_status
) to authenticated;
