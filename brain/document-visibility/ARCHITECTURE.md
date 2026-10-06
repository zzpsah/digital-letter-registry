# Architecture

Portal PATCH visibility -> Supabase letters visibility/RLS -> authenticated search/open/download obey RLS.

Oracle index refresh -> select Public only -> publish public HTML -> ensure public Drive permission only for Public originals -> revoke anonymous permission for Private/Personal.

Oracle delivery postprocess -> detect non-public visibility -> suppress future WhatsApp receipt -> remove previously generated receipt when present.
