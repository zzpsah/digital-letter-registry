-- Shared archive-level importance/highlight metadata for eLetters.
alter table public.letters
  add column if not exists is_important boolean not null default false,
  add column if not exists user_comment text,
  add column if not exists important_at timestamptz,
  add column if not exists important_by uuid references auth.users(id) on delete set null;

create index if not exists idx_letters_archive_important_latest
  on public.letters (archive_id, is_important desc, uploaded_at desc);

create index if not exists idx_letters_important_by
  on public.letters (important_by)
  where important_by is not null;

drop function if exists public.search_letter_cards(text,text,text,letter_status,integer,text,integer);

CREATE OR REPLACE FUNCTION public.search_letter_cards(search_query text DEFAULT NULL::text, authority_filter text DEFAULT NULL::text, category_filter text DEFAULT NULL::text, status_filter letter_status DEFAULT NULL::letter_status, year_filter integer DEFAULT NULL::integer, file_type_filter text DEFAULT NULL::text, result_limit integer DEFAULT 25)
 RETURNS TABLE(id uuid, smart_filename text, title text, summary text, summary_hi text, reference_number text, authority text, category text, issue_date date, status letter_status, action_required text, action_required_hi text, concepts text[], context_snippet text, file_type text, is_important boolean, user_comment text, uploaded_at timestamp with time zone, important_at timestamp with time zone, text_rank real, fuzzy_rank real, combined_rank real)
 LANGUAGE sql
 STABLE
 SET search_path TO 'public', 'extensions'
AS $function$
           with normalized as (
             select
               nullif(btrim(search_query), '') as q,
               lower(nullif(btrim(search_query), '')) as ql,
               case
                 when lower(coalesce(search_query,'')) ~ '(fee|fees|shulk|शुल्क)' then array['fee','fees','shulk','शुल्क']
                 when lower(coalesce(search_query,'')) ~ '(salary|vetan|वेतन)' then array['salary','vetan','वेतन']
                 when lower(coalesce(search_query,'')) ~ '(teacher|shikshak|शिक्षक)' then array['teacher','shikshak','शिक्षक']
                 when lower(coalesce(search_query,'')) ~ '(exam|pariksha|परीक्षा)' then array['exam','pariksha','परीक्षा']
                 when lower(coalesce(search_query,'')) ~ '(registration|panjiyan|पंजीयन|पंजीकरण)' then array['registration','panjiyan','पंजीयन','पंजीकरण']
                 when lower(coalesce(search_query,'')) ~ '(admission|namankan|नामांकन|प्रवेश)' then array['admission','namankan','नामांकन','प्रवेश']
                 when lower(coalesce(search_query,'')) ~ '(transfer|sthanantaran|स्थानांतरण)' then array['transfer','sthanantaran','स्थानांतरण','समायोजन']
                 when lower(coalesce(search_query,'')) ~ '(udise|यूडाइस)' then array['udise','यूडाइस']
                 when lower(coalesce(search_query,'')) ~ '(scholarship|छात्रवृत्ति)' then array['scholarship','छात्रवृत्ति']
                 else array[]::text[]
               end as aliases
           ),
           base as (
             select
               l.*,
               p.concepts,
               p.extracted_text,
               p.structured_context,
               coalesce(p.structured_context->>'summary_hi','') as summary_hi_value,
               coalesce(p.structured_context->>'action_required_hi','') as action_required_hi_value,
               concat_ws(' ',
                 l.smart_filename,l.original_filename,l.title,l.summary,l.reference_number,l.authority,
                 l.category,l.subcategory,l.action_required,l.user_comment,array_to_string(p.concepts,' '),
                 p.structured_context->>'summary_hi',p.structured_context->>'action_required_hi',
                 p.structured_context->'related_terms_hi',p.structured_context->'related_terms_en',
                 p.extracted_text
               ) as haystack
             from public.letters l
             left join public.letter_processing p on p.letter_id=l.id
           ),
           ranked as (
             select
               b.*,
               case when n.q is null then 0::real else
                 ts_rank_cd(to_tsvector('simple',b.haystack),websearch_to_tsquery('simple',n.q))::real
               end as text_rank_value,
               case when n.q is null then 0::real else greatest(
                 similarity(coalesce(b.smart_filename,''),n.q),
                 similarity(coalesce(b.title,''),n.q),
                 similarity(coalesce(b.summary,''),n.q),
                 similarity(coalesce(b.reference_number,''),n.q),
                 similarity(coalesce(b.authority,''),n.q),
                 similarity(coalesce(b.user_comment,''),n.q)
               )::real end as fuzzy_rank_value,
               case when n.q is not null and exists (
                 select 1 from unnest(n.aliases) a
                 where lower(b.haystack) like '%' || lower(a) || '%'
               ) then 1::real else 0::real end as alias_rank_value,
               case
                 when n.q is null then 0::real
                 when regexp_replace(lower(coalesce(b.reference_number,'')),'[^[:alnum:]]','','g')
                    = regexp_replace(n.ql,'[^[:alnum:]]','','g') then 1::real
                 when lower(coalesce(b.reference_number,'')) like '%' || n.ql || '%' then 0.75::real
                 when lower(coalesce(b.title,'')) like '%' || n.ql || '%' then 0.5::real
                 when lower(b.haystack) like '%' || n.ql || '%' then 0.25::real
                 else 0::real
               end as exact_rank_value
             from base b cross join normalized n
             where
               (authority_filter is null or lower(coalesce(b.authority,'')) like '%'||lower(authority_filter)||'%')
               and (category_filter is null or lower(coalesce(b.category,'')) like '%'||lower(category_filter)||'%')
               and (status_filter is null or b.status=status_filter)
               and (year_filter is null or extract(year from b.issue_date)::integer=year_filter)
               and (
                 file_type_filter is null or
                 lower(nullif(regexp_replace(coalesce(b.original_filename,''),'^.*\.',''),coalesce(b.original_filename,'')))=lower(file_type_filter)
               )
               and (
                 n.q is null
                 or to_tsvector('simple',b.haystack) @@ websearch_to_tsquery('simple',n.q)
                 or lower(b.haystack) like '%'||n.ql||'%'
                 or coalesce(b.smart_filename,'') % n.q
                 or coalesce(b.title,'') % n.q
                 or coalesce(b.summary,'') % n.q
                 or coalesce(b.reference_number,'') % n.q
                 or coalesce(b.authority,'') % n.q
                 or coalesce(b.user_comment,'') % n.q
                 or exists (
                   select 1 from unnest(n.aliases) a
                   where lower(b.haystack) like '%' || lower(a) || '%'
                 )
               )
           )
           select
             r.id,r.smart_filename,r.title,r.summary,
             nullif(r.summary_hi_value,'') as summary_hi,
             r.reference_number,r.authority,r.category,r.issue_date,r.status,r.action_required,
             nullif(r.action_required_hi_value,'') as action_required_hi,
             r.concepts,
             case when r.extracted_text is null then null else left(r.extracted_text,360) end,
             lower(nullif(regexp_replace(coalesce(r.original_filename,''),'^.*\.',''),coalesce(r.original_filename,''))),
             r.is_important,r.user_comment,r.uploaded_at,r.important_at,
             r.text_rank_value,r.fuzzy_rank_value,
             (r.text_rank_value*0.50 + r.fuzzy_rank_value*0.20 + r.alias_rank_value*0.15 + r.exact_rank_value*0.15)::real
           from ranked r
           order by
             (r.text_rank_value*0.50 + r.fuzzy_rank_value*0.20 + r.alias_rank_value*0.15 + r.exact_rank_value*0.15) desc,
             r.uploaded_at desc
           limit greatest(1,least(coalesce(result_limit,25),100));
         $function$


grant execute on function public.search_letter_cards(text,text,text,letter_status,integer,text,integer) to authenticated;
