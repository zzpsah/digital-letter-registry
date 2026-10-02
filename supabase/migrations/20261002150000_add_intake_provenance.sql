-- Intake provenance for Telegram/WhatsApp/email/watched-folder sources.
-- Stores private runtime provenance in Supabase, never in public Git.

create table public.letter_sources (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  letter_id uuid not null references public.letters(id) on delete cascade,
  source_channel text not null check (
    source_channel in ('web','telegram','whatsapp','email','watched_folder','historical_import')
  ),
  external_message_id text,
  source_label text,
  received_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create unique index letter_sources_external_id_unique
  on public.letter_sources (owner_id, source_channel, external_message_id)
  where external_message_id is not null;

create index letter_sources_letter_idx
  on public.letter_sources (letter_id);

create index letter_sources_owner_received_idx
  on public.letter_sources (owner_id, received_at desc);

alter table public.letter_sources enable row level security;

create policy "owners manage letter sources"
on public.letter_sources
for all
to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);
