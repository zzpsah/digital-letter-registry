create table if not exists public.document_categories (
  id uuid primary key default extensions.gen_random_uuid(),
  archive_id uuid not null references public.archives(id) on delete cascade,
  code text not null,
  name_en text not null,
  name_hi text not null,
  icon text not null default '📁',
  keywords text[] not null default '{}'::text[],
  sort_order integer not null default 100,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (archive_id, code)
);

create index if not exists document_categories_archive_sort_idx
  on public.document_categories (archive_id, is_active desc, sort_order, name_en);

alter table public.document_categories enable row level security;
revoke all on table public.document_categories from anon;
revoke all on table public.document_categories from authenticated;
grant select, insert, update, delete on table public.document_categories to authenticated;

drop policy if exists "members read document categories" on public.document_categories;
create policy "members read document categories"
on public.document_categories for select to authenticated
using ((select private.archive_member_role(archive_id)) is not null);

drop policy if exists "admins insert document categories" on public.document_categories;
create policy "admins insert document categories"
on public.document_categories for insert to authenticated
with check ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "admins update document categories" on public.document_categories;
create policy "admins update document categories"
on public.document_categories for update to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin')
with check ((select private.archive_member_role(archive_id)) = 'admin');

drop policy if exists "admins delete document categories" on public.document_categories;
create policy "admins delete document categories"
on public.document_categories for delete to authenticated
using ((select private.archive_member_role(archive_id)) = 'admin');

insert into public.document_categories
  (archive_id, code, name_en, name_hi, icon, keywords, sort_order)
select a.id, seed.code, seed.name_en, seed.name_hi, seed.icon, seed.keywords, seed.sort_order
from public.archives a
cross join (values
 ('salary_payment','Salary / Payment','वेतन / भुगतान','💰',array['sna sparsh','salary','वेतन','payee','payment','भुगतान']::text[],10),
 ('teacher_service','Teacher Service','शिक्षक सेवा','💼',array['teacher','शिक्षक','service','grievance','transfer','joining','स्थानांतरण','योगदान','सेवा']::text[],20),
 ('fee_finance','Fee / Finance','शुल्क / वित्त','💳',array['fee','fees','शुल्क','finance','financial','वित्त']::text[],30),
 ('exam','Examination','परीक्षा','📝',array['exam','examination','परीक्षा','compartment','improvement']::text[],40),
 ('admission','Admission','नामांकन','🎓',array['admission','नामांकन','प्रवेश']::text[],50),
 ('registration','Registration','पंजीकरण','📋',array['registration','पंजीयन','पंजीकरण']::text[],60),
 ('udise_data','UDISE / School Data','UDISE / विद्यालय डेटा','🏫',array['udise','यूडाइस','school data','student module','pen']::text[],70),
 ('scholarship_scheme','Scholarship / Scheme','छात्रवृत्ति / योजना','🎁',array['scholarship','छात्रवृत्ति','scheme','योजना','benefit']::text[],80),
 ('order_notice','Order / Notice','आदेश / निर्देश','📢',array['order','circular','notice','निर्देश','आदेश','परिपत्र','सूचना']::text[],90),
 ('other','Other','अन्य','📁',array[]::text[],999)
) as seed(code,name_en,name_hi,icon,keywords,sort_order)
on conflict (archive_id, code) do nothing;
