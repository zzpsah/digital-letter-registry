-- Promote common structured metadata into searchable letter columns.

alter table public.letters
  add column if not exists reference_number text,
  add column if not exists summary text;

create index if not exists letters_reference_number_trgm_idx
  on public.letters using gin (reference_number gin_trgm_ops);
