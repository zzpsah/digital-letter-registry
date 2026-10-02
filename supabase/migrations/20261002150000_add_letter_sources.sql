-- Provenance for normalized intake channels.
-- Stores source identity/labels only; message bodies and attachment bytes remain outside this table.

create table public.letter_sources (
  id uuid primary key default extensions.gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  letter_id uuid not null references public.letters(id) on delete cascade,
  channel text not null check (
    channel in ('watched_folder', 'email', 'telegram', 'whatsapp', 'web_upload')
  ),
  source_id text not null,
  sender_label text,
  conversation_label text,
  received_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (owner_id, channel, source_id)
);

create index letter_sources_letter_idx
  on public.letter_sources (letter_id);

create index letter_sources_owner_channel_idx
  on public.letter_sources (owner_id, channel);

alter table public.letter_sources enable row level security;

create policy "owners manage letter sources"
on public.letter_sources
for all
to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);
