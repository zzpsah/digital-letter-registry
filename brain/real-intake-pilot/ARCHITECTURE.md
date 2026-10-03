# Architecture

Manual authenticated upload on the private Oracle DLR endpoint → immutable private Drive original → Supabase metadata/job → dedicated Oracle worker → OCR/context → search/original access. Public Vercel remains control/search plane without Drive secrets. No connector automation in pilot.
