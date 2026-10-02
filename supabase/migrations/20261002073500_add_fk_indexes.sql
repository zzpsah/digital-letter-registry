-- Cover foreign keys reported by Supabase performance advisor.

create index if not exists letter_processing_owner_idx
  on public.letter_processing (owner_id);

create index if not exists letter_relationships_owner_idx
  on public.letter_relationships (owner_id);

create index if not exists letter_relationships_target_idx
  on public.letter_relationships (target_letter_id);
