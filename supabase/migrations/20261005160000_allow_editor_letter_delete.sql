drop policy if exists "archive admins delete letters" on public.letters;
drop policy if exists "archive editors delete letters" on public.letters;

create policy "archive editors delete letters"
on public.letters for delete to authenticated
using ((select private.archive_member_role(archive_id)) in ('admin','editor'));
