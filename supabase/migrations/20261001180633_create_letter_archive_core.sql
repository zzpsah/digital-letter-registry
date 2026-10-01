-- Public-safe schema baseline for the separate Digital Letter Registry Supabase project.
-- Contains no project IDs, URLs, API keys, Drive IDs, credentials, or real document data.

create extension if not exists pgcrypto with schema extensions;
create extension if not exists vector with schema extensions;
create extension if not exists pg_trgm with schema extensions;

create type public.letter_status as enum (
  'current',
  'expired',
  'historical',
  'superseded',
  'unknown'
);

create type public.letter_relationship_type as enum (
  'duplicate_of',
  'extends',
  'supersedes',
  'corrects',
  'related_to'
);

create table public.letters (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  original_filename text not null check (length(btrim(original_filename)) > 0),
  original_sha256 text not null check (original_sha256 ~ '^[0-9a-f]{64}$'),
  storage_provider text not null default 'gdrive',
  storage_object_id text not null check (length(btrim(storage_object_id)) > 0),
  smart_filename text,
  authority text,
  category text,
  subcategory text,
  title text,
  issue_date date,
  received_at timestamptz not null default now(),
  uploaded_at timestamptz not null default now(),
  status public.letter_status not null default 'unknown',
  action_required text,
  deadline_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, original_sha256)
);

create table public.letter_processing (
  letter_id uuid primary key references public.letters(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  extracted_text text,
  structured_context jsonb not null default '{}'::jsonb,
  concepts text[] not null default '{}'::text[],
  ocr_version text not null default 'unprocessed',
  context_version text not null default 'unprocessed',
  dictionary_version text not null default 'unprocessed',
  filename_rule_version text not null default 'unprocessed',
  category_schema_version text not null default 'unprocessed',
  embedding_version text not null default 'unprocessed',
  status_rule_version text not null default 'unprocessed',
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.letter_relationships (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  source_letter_id uuid not null references public.letters(id) on delete cascade,
  target_letter_id uuid not null references public.letters(id) on delete cascade,
  relationship_type public.letter_relationship_type not null,
  confidence numeric,
  created_at timestamptz not null default now(),
  check (source_letter_id <> target_letter_id),
  unique (source_letter_id, target_letter_id, relationship_type)
);

create table public.letter_chunks (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  letter_id uuid not null references public.letters(id) on delete cascade,
  chunk_index integer not null check (chunk_index >= 0),
  content text not null check (length(btrim(content)) > 0),
  embedding extensions.vector,
  embedding_version text not null default 'unprocessed',
  created_at timestamptz not null default now(),
  unique (letter_id, chunk_index, embedding_version)
);

create index letters_owner_received_idx
  on public.letters (owner_id, received_at desc);

create index letters_owner_status_idx
  on public.letters (owner_id, status);

create index letters_title_trgm_idx
  on public.letters using gin (title gin_trgm_ops);

create index letter_processing_concepts_idx
  on public.letter_processing using gin (concepts);

create index letter_chunks_owner_letter_idx
  on public.letter_chunks (owner_id, letter_id);

alter table public.letters enable row level security;
alter table public.letter_processing enable row level security;
alter table public.letter_relationships enable row level security;
alter table public.letter_chunks enable row level security;

create policy "owners manage letters"
on public.letters
for all
to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);

create policy "owners manage letter processing"
on public.letter_processing
for all
to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);

create policy "owners manage letter relationships"
on public.letter_relationships
for all
to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);

create policy "owners manage letter chunks"
on public.letter_chunks
for all
to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);
