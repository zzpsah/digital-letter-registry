-- Restore the pre-existing OSINT phone-search RPC access. These functions belong
-- to the separate phone-search application and are outside the DLR migration scope.
grant execute on function public.osint_admin_list_requests() to anon, authenticated, service_role;
grant execute on function public.osint_admin_review_request(uuid,text,text) to anon, authenticated, service_role;
grant execute on function public.osint_request_access(text,text) to anon, authenticated, service_role;
