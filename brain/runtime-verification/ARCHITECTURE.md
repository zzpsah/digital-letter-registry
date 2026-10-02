# Runtime Verification — Architecture

Verification layers:
1. Database RLS structure and simulated JWT-claim checks.
2. Real Supabase Auth short-lived session through PostgREST/API.
3. Runtime-only Drive OAuth for synthetic upload/read/original streaming.
4. Runtime-only Gemini configuration for synthetic structured analysis/embeddings.
5. Secret-safe readiness checks.
6. Cleanup of temporary synthetic verification artifacts.

Secrets and private identifiers remain runtime-only and never enter Git.
