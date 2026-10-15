-- Authenticated archive members need read access to authority reference data.
-- Row-level security remains the boundary: only active archive members can read
-- rows for their archive, and only archive admins can manage them.
GRANT SELECT ON TABLE public.authorities, public.authority_aliases TO authenticated;
