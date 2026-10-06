-- Public / private / personal visibility for eLetters documents.
-- Existing documents remain public for backward compatibility.

alter table public.letters
  add column if not exists visibility text not null default 'public',
  add column if not exists personal_owner_id uuid references auth.users(id) on delete set null,
  add column if not exists visibility_changed_at timestamptz,
  add column if not exists visibility_changed_by uuid references auth.users(id) on delete set null;

alter table public.letters
  drop constraint if exists letters_visibility_check;
alter table public.letters
  add constraint letters_visibility_check
  check (visibility in ('public','private','personal'));

alter table public.letters
  drop constraint if exists letters_personal_owner_check;
alter table public.letters
  add constraint letters_personal_owner_check
  check (visibility <> 'personal' or personal_owner_id is not null);

create index if not exists letters_archive_visibility_uploaded_idx
  on public.letters (archive_id, visibility, uploaded_at desc);

-- Admins can always recover/manage a document. Personal documents are otherwise
-- visible only to the user who marked them personal and the original ingest owner
-- (the background worker identity needs this to keep processing/reprocessing working).
drop policy if exists "archive members read letters" on public.letters;
create policy "archive members read letters"
on public.letters for select to authenticated
using (
  (select private.archive_member_role(archive_id)) = 'admin'
  or (
    (select private.archive_member_role(archive_id)) in ('editor','viewer')
    and (
      visibility <> 'personal'
      or personal_owner_id = (select auth.uid())
      or owner_id = (select auth.uid())
    )
  )
);

-- Editors can update visible documents, but may only create a Personal scope for
-- themselves. Admins retain recovery authority.
drop policy if exists "archive editors update letters" on public.letters;
create policy "archive editors update letters"
on public.letters for update to authenticated
using (
  (select private.archive_member_role(archive_id)) in ('admin','editor')
  and (
    (select private.archive_member_role(archive_id)) = 'admin'
    or visibility <> 'personal'
    or personal_owner_id = (select auth.uid())
    or owner_id = (select auth.uid())
  )
)
with check (
  (select private.archive_member_role(archive_id)) in ('admin','editor')
  and (
    visibility <> 'personal'
    or (select private.archive_member_role(archive_id)) = 'admin'
    or personal_owner_id = (select auth.uid())
  )
);

-- Derived content must follow the parent letter's visibility rather than exposing
-- a Personal document through direct REST access or semantic search.
drop policy if exists "archive members read letter processing" on public.letter_processing;
create policy "archive members read letter processing"
on public.letter_processing for select to authenticated
using (
  exists (
    select 1 from public.letters l
    where l.id = public.letter_processing.letter_id
      and l.archive_id = public.letter_processing.archive_id
  )
);

drop policy if exists "archive members read letter chunks" on public.letter_chunks;
create policy "archive members read letter chunks"
on public.letter_chunks for select to authenticated
using (
  exists (
    select 1 from public.letters l
    where l.id = public.letter_chunks.letter_id
      and l.archive_id = public.letter_chunks.archive_id
  )
);

drop policy if exists "archive members read letter relationships" on public.letter_relationships;
create policy "archive members read letter relationships"
on public.letter_relationships for select to authenticated
using (
  exists (
    select 1 from public.letters source_letter
    where source_letter.id = public.letter_relationships.source_letter_id
      and source_letter.archive_id = public.letter_relationships.archive_id
  )
  and exists (
    select 1 from public.letters target_letter
    where target_letter.id = public.letter_relationships.target_letter_id
      and target_letter.archive_id = public.letter_relationships.archive_id
  )
);
