alter table public.letters alter column archive_id set not null;
alter table public.letter_processing alter column archive_id set not null;
alter table public.letter_relationships alter column archive_id set not null;
alter table public.letter_chunks alter column archive_id set not null;
alter table public.processing_jobs alter column archive_id set not null;
alter table public.processing_profiles alter column archive_id set not null;
alter table public.letter_sources alter column archive_id set not null;

alter table public.letters
  drop constraint if exists letters_owner_id_original_sha256_key;
alter table public.letters
  add constraint letters_archive_id_original_sha256_key
  unique (archive_id, original_sha256);

drop index if exists public.letter_sources_external_id_unique;
create unique index letter_sources_external_id_unique
  on public.letter_sources (archive_id, source_channel, external_message_id)
  where external_message_id is not null;

alter table public.processing_profiles
  drop constraint if exists processing_profiles_pkey;
alter table public.processing_profiles
  add constraint processing_profiles_pkey primary key (archive_id);

create index if not exists letters_archive_received_idx
  on public.letters (archive_id, received_at desc);
create index if not exists letters_archive_status_idx
  on public.letters (archive_id, status);
create index if not exists processing_jobs_archive_status_available_idx
  on public.processing_jobs (archive_id, status, available_at);
create index if not exists letter_sources_archive_received_idx
  on public.letter_sources (archive_id, received_at desc);
create index if not exists letter_relationships_archive_review_idx
  on public.letter_relationships (archive_id, review_status, relationship_type);
create index if not exists letter_chunks_archive_letter_idx
  on public.letter_chunks (archive_id, letter_id);

create or replace function private.prevent_archive_reassignment()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.archive_id is distinct from old.archive_id then
    raise exception 'archive_id cannot be changed after insert';
  end if;
  return new;
end
$$;

revoke all on function private.prevent_archive_reassignment() from public;
revoke all on function private.prevent_archive_reassignment() from anon;

drop trigger if exists letters_freeze_archive_id on public.letters;
create trigger letters_freeze_archive_id
before update on public.letters
for each row execute function private.prevent_archive_reassignment();

drop trigger if exists letter_processing_freeze_archive_id on public.letter_processing;
create trigger letter_processing_freeze_archive_id
before update on public.letter_processing
for each row execute function private.prevent_archive_reassignment();

drop trigger if exists letter_relationships_freeze_archive_id on public.letter_relationships;
create trigger letter_relationships_freeze_archive_id
before update on public.letter_relationships
for each row execute function private.prevent_archive_reassignment();

drop trigger if exists letter_chunks_freeze_archive_id on public.letter_chunks;
create trigger letter_chunks_freeze_archive_id
before update on public.letter_chunks
for each row execute function private.prevent_archive_reassignment();

drop trigger if exists processing_jobs_freeze_archive_id on public.processing_jobs;
create trigger processing_jobs_freeze_archive_id
before update on public.processing_jobs
for each row execute function private.prevent_archive_reassignment();

drop trigger if exists processing_profiles_freeze_archive_id on public.processing_profiles;
create trigger processing_profiles_freeze_archive_id
before update on public.processing_profiles
for each row execute function private.prevent_archive_reassignment();

drop trigger if exists letter_sources_freeze_archive_id on public.letter_sources;
create trigger letter_sources_freeze_archive_id
before update on public.letter_sources
for each row execute function private.prevent_archive_reassignment();

revoke all on table public.letters from anon;
revoke all on table public.letter_processing from anon;
revoke all on table public.letter_relationships from anon;
revoke all on table public.letter_chunks from anon;
revoke all on table public.processing_jobs from anon;
revoke all on table public.processing_profiles from anon;
revoke all on table public.letter_sources from anon;

grant select, insert, update, delete on table public.letters to authenticated;
grant select, insert, update, delete on table public.letter_processing to authenticated;
grant select, insert, update, delete on table public.letter_relationships to authenticated;
grant select, insert, update, delete on table public.letter_chunks to authenticated;
grant select, insert, update, delete on table public.processing_jobs to authenticated;
grant select, insert, update, delete on table public.processing_profiles to authenticated;
grant select, insert, update, delete on table public.letter_sources to authenticated;

drop policy if exists "owners manage letters" on public.letters;
drop policy if exists "archive members read letters" on public.letters;
drop policy if exists "archive editors insert letters" on public.letters;
drop policy if exists "archive editors update letters" on public.letters;
drop policy if exists "archive admins delete letters" on public.letters;

create policy "archive members read letters"
on public.letters for select to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor','viewer'));

create policy "archive editors insert letters"
on public.letters for insert to authenticated
with check (
  owner_id = (select auth.uid())
  and (select private.archive_member_role(archive_id)) in ('admin','editor')
);

create policy "archive editors update letters"
on public.letters for update to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor'))
with check ((select private.archive_member_role(archive_id)) in ('admin','editor'));

create policy "archive admins delete letters"
on public.letters for delete to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "owners manage letter processing" on public.letter_processing;
drop policy if exists "archive members read letter processing" on public.letter_processing;
drop policy if exists "archive editors insert letter processing" on public.letter_processing;
drop policy if exists "archive editors update letter processing" on public.letter_processing;
drop policy if exists "archive admins delete letter processing" on public.letter_processing;

create policy "archive members read letter processing"
on public.letter_processing for select to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor','viewer'));

create policy "archive editors insert letter processing"
on public.letter_processing for insert to authenticated
with check (
  owner_id = (select auth.uid())
  and (select private.archive_member_role(archive_id)) in ('admin','editor')
);

create policy "archive editors update letter processing"
on public.letter_processing for update to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor'))
with check ((select private.archive_member_role(archive_id)) in ('admin','editor'));

create policy "archive admins delete letter processing"
on public.letter_processing for delete to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "owners manage letter relationships" on public.letter_relationships;
drop policy if exists "archive members read letter relationships" on public.letter_relationships;
drop policy if exists "archive editors insert letter relationships" on public.letter_relationships;
drop policy if exists "archive editors update letter relationships" on public.letter_relationships;
drop policy if exists "archive admins delete letter relationships" on public.letter_relationships;

create policy "archive members read letter relationships"
on public.letter_relationships for select to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor','viewer'));

create policy "archive editors insert letter relationships"
on public.letter_relationships for insert to authenticated
with check (
  owner_id = (select auth.uid())
  and (select private.archive_member_role(archive_id)) in ('admin','editor')
);

create policy "archive editors update letter relationships"
on public.letter_relationships for update to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor'))
with check ((select private.archive_member_role(archive_id)) in ('admin','editor'));

create policy "archive admins delete letter relationships"
on public.letter_relationships for delete to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "owners manage letter chunks" on public.letter_chunks;
drop policy if exists "archive members read letter chunks" on public.letter_chunks;
drop policy if exists "archive editors insert letter chunks" on public.letter_chunks;
drop policy if exists "archive editors update letter chunks" on public.letter_chunks;
drop policy if exists "archive admins delete letter chunks" on public.letter_chunks;

create policy "archive members read letter chunks"
on public.letter_chunks for select to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor','viewer'));

create policy "archive editors insert letter chunks"
on public.letter_chunks for insert to authenticated
with check (
  owner_id = (select auth.uid())
  and (select private.archive_member_role(archive_id)) in ('admin','editor')
);

create policy "archive editors update letter chunks"
on public.letter_chunks for update to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor'))
with check ((select private.archive_member_role(archive_id)) in ('admin','editor'));

create policy "archive admins delete letter chunks"
on public.letter_chunks for delete to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "owners manage processing jobs" on public.processing_jobs;
drop policy if exists "archive workers read processing jobs" on public.processing_jobs;
drop policy if exists "archive workers insert processing jobs" on public.processing_jobs;
drop policy if exists "archive workers update processing jobs" on public.processing_jobs;
drop policy if exists "archive admins delete processing jobs" on public.processing_jobs;

create policy "archive workers read processing jobs"
on public.processing_jobs for select to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor'));

create policy "archive workers insert processing jobs"
on public.processing_jobs for insert to authenticated
with check (
  owner_id = (select auth.uid())
  and (select private.archive_member_role(archive_id)) in ('admin','editor')
);

create policy "archive workers update processing jobs"
on public.processing_jobs for update to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor'))
with check ((select private.archive_member_role(archive_id)) in ('admin','editor'));

create policy "archive admins delete processing jobs"
on public.processing_jobs for delete to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "owners manage processing profile" on public.processing_profiles;
drop policy if exists "archive members read processing profile" on public.processing_profiles;
drop policy if exists "archive admins insert processing profile" on public.processing_profiles;
drop policy if exists "archive admins update processing profile" on public.processing_profiles;
drop policy if exists "archive admins delete processing profile" on public.processing_profiles;

create policy "archive members read processing profile"
on public.processing_profiles for select to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor','viewer'));

create policy "archive admins insert processing profile"
on public.processing_profiles for insert to authenticated
with check (
  owner_id = (select auth.uid())
  and (select private.archive_member_role(archive_id)) = 'admin'
);

create policy "archive admins update processing profile"
on public.processing_profiles for update to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin')
with check ((select private.archive_member_role(archive_id)) = 'admin');

create policy "archive admins delete processing profile"
on public.processing_profiles for delete to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "owners manage letter sources" on public.letter_sources;
drop policy if exists "archive members read letter sources" on public.letter_sources;
drop policy if exists "archive editors insert letter sources" on public.letter_sources;
drop policy if exists "archive editors update letter sources" on public.letter_sources;
drop policy if exists "archive admins delete letter sources" on public.letter_sources;

create policy "archive members read letter sources"
on public.letter_sources for select to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor','viewer'));

create policy "archive editors insert letter sources"
on public.letter_sources for insert to authenticated
with check (
  owner_id = (select auth.uid())
  and (select private.archive_member_role(archive_id)) in ('admin','editor')
);

create policy "archive editors update letter sources"
on public.letter_sources for update to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor'))
with check ((select private.archive_member_role(archive_id)) in ('admin','editor'));

create policy "archive admins delete letter sources"
on public.letter_sources for delete to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

create or replace function public.claim_processing_job()
returns table (
  id uuid,
  letter_id uuid,
  owner_id uuid,
  reason text,
  attempts integer,
  created_at timestamptz
)
language sql
volatile
security invoker
set search_path = public
as $$
  with candidate as (
    select j.id
    from public.processing_jobs j
    where j.owner_id = auth.uid()
      and (select private.archive_member_role(j.archive_id)) in ('admin','editor')
      and j.status = 'pending'
      and j.available_at <= now()
    order by j.created_at
    for update skip locked
    limit 1
  ),
  claimed as (
    update public.processing_jobs j
    set
      status = 'processing',
      attempts = j.attempts + 1,
      started_at = now(),
      updated_at = now(),
      last_error = null
    where j.id = (select id from candidate)
    returning
      j.id,
      j.letter_id,
      j.owner_id,
      j.reason,
      j.attempts,
      j.created_at
  )
  select * from claimed;
$$;

create or replace function public.complete_processing_job(job_id uuid)
returns table (success boolean)
language sql
volatile
security invoker
set search_path = public
as $$
  with updated as (
    update public.processing_jobs j
    set
      status = 'completed',
      completed_at = now(),
      updated_at = now(),
      last_error = null
    where j.id = job_id
      and j.owner_id = auth.uid()
      and (select private.archive_member_role(j.archive_id)) in ('admin','editor')
      and j.status = 'processing'
    returning j.id
  )
  select exists(select 1 from updated) as success;
$$;

create or replace function public.fail_processing_job(
  job_id uuid,
  error_message text
)
returns table (success boolean)
language sql
volatile
security invoker
set search_path = public
as $$
  with updated as (
    update public.processing_jobs j
    set
      status = 'failed',
      updated_at = now(),
      last_error = left(coalesce(error_message, 'unknown processing error'), 2000)
    where j.id = job_id
      and j.owner_id = auth.uid()
      and (select private.archive_member_role(j.archive_id)) in ('admin','editor')
      and j.status = 'processing'
    returning j.id
  )
  select exists(select 1 from updated) as success;
$$;

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
  where (select private.archive_member_role(l.archive_id)) = 'admin'
    and exists (
      select 1
      from public.letter_relationships r
      where r.archive_id = l.archive_id
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
  where (select private.archive_member_role(l.archive_id)) = 'admin'
    and l.status = 'superseded'
    and not exists (
      select 1
      from public.letter_relationships r
      where r.archive_id = l.archive_id
        and r.target_letter_id = l.id
        and r.relationship_type = 'supersedes'
        and r.review_status = 'confirmed'
    );

  get diagnostics current_count = row_count;

  update public.letter_processing p
  set
    status_rule_version = recalculate_letter_statuses.status_rule_version,
    updated_at = now()
  where (select private.archive_member_role(p.archive_id)) = 'admin';

  return query
    select superseded_count, current_count;
end;
$$;

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
    and (select private.archive_member_role(r.archive_id)) = 'admin';

  if not found then
    return query select false;
    return;
  end if;

  perform public.recalculate_letter_statuses('relationships-v1');
  return query select true;
end;
$$;

create or replace function public.preview_reprocessing(
  result_limit integer default 100
)
returns table (
  letter_id uuid,
  title text,
  smart_filename text,
  differences text[]
)
language sql
stable
security invoker
set search_path = public
as $$
  select
    l.id as letter_id,
    l.title,
    l.smart_filename,
    array_remove(array[
      case when p.ocr_version is distinct from profile.extraction_version
        then 'extraction' end,
      case when p.context_version is distinct from profile.context_version
        then 'context' end,
      case when p.dictionary_version is distinct from profile.dictionary_version
        then 'dictionary' end,
      case when p.filename_rule_version is distinct from profile.filename_rule_version
        then 'filename_rule' end,
      case when p.category_schema_version is distinct from profile.category_schema_version
        then 'category_schema' end,
      case when p.embedding_version is distinct from profile.embedding_version
        then 'embedding' end,
      case when p.status_rule_version is distinct from profile.status_rule_version
        then 'status_rule' end
    ], null) as differences
  from public.letters l
  join public.letter_processing p
    on p.letter_id = l.id
   and p.archive_id = l.archive_id
  join public.processing_profiles profile
    on profile.archive_id = l.archive_id
  where (select private.archive_member_role(l.archive_id)) is not null
    and (
      p.ocr_version is distinct from profile.extraction_version
      or p.context_version is distinct from profile.context_version
      or p.dictionary_version is distinct from profile.dictionary_version
      or p.filename_rule_version is distinct from profile.filename_rule_version
      or p.category_schema_version is distinct from profile.category_schema_version
      or p.embedding_version is distinct from profile.embedding_version
      or p.status_rule_version is distinct from profile.status_rule_version
    )
  order by l.received_at desc
  limit greatest(1, least(coalesce(result_limit, 100), 500));
$$;

create or replace function public.enqueue_reprocessing_jobs(
  result_limit integer default 500
)
returns table (enqueued integer)
language plpgsql
volatile
security invoker
set search_path = public
as $$
declare
  inserted_count integer := 0;
  profile_record record;
begin
  select
    archive_id,
    md5(concat_ws(
      '|',
      extraction_version,
      context_version,
      dictionary_version,
      filename_rule_version,
      category_schema_version,
      embedding_version,
      status_rule_version
    )) as profile_hash
  into profile_record
  from public.processing_profiles
  where (select private.archive_member_role(archive_id)) = 'admin'
  order by updated_at desc
  limit 1;

  if profile_record.archive_id is null then
    return query select 0;
    return;
  end if;

  insert into public.processing_jobs (
    archive_id,
    owner_id,
    letter_id,
    status,
    reason
  )
  select
    l.archive_id,
    auth.uid(),
    preview.letter_id,
    'pending',
    'reprocess:' || profile_record.profile_hash
  from public.preview_reprocessing(
    greatest(1, least(coalesce(result_limit, 500), 500))
  ) preview
  join public.letters l on l.id = preview.letter_id
  where l.archive_id = profile_record.archive_id
  on conflict (letter_id, reason) do nothing;

  get diagnostics inserted_count = row_count;
  return query select inserted_count;
end;
$$;

grant execute on function public.claim_processing_job() to authenticated;
grant execute on function public.complete_processing_job(uuid) to authenticated;
grant execute on function public.fail_processing_job(uuid, text) to authenticated;
grant execute on function public.recalculate_letter_statuses(text) to authenticated;
grant execute on function public.review_letter_relationship(
  uuid,
  public.relationship_review_status
) to authenticated;
grant execute on function public.preview_reprocessing(integer) to authenticated;
grant execute on function public.enqueue_reprocessing_jobs(integer) to authenticated;
