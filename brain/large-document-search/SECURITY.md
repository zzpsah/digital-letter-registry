# Security

- Do not include real document text, IDs, Drive URLs, credentials, or database dumps in source control.
- Only the Oracle primary was changed; hosted Supabase was not touched.
- The migration changes one GIN index and one active search RPC; it does not alter RLS, permissions, storage, or original files.
