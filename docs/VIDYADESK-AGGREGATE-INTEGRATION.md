# VidyaDesk Digital Letter Registry aggregate

**Route:** GET /api/v1/integrations/vidyadesk/summary  
**Status:** implemented in feat/vidyadesk-public-summary; not deployed or activated.

## Returned data

The endpoint returns only:
- count of public, non-archived letters in the configured school archive;
- timestamp of the latest public, non-archived letter;
- fixed school scope and aggregate snapshot metadata.

It never returns letter IDs, filenames, titles, subjects, authorities, references, extracted text, Drive IDs, user IDs, owner IDs, personal/private letters, or processing-job details.

## Authentication and RLS

- Caller must present a dedicated bearer token in DLR_VIDYADESK_READ_TOKEN.
- DLR_VIDYADESK_SCHOOL_KEY must equal umv-tetahali.
- DLR_VIDYADESK_ARCHIVE_NAME must exactly match the active archive row name.
- DLR_VIDYADESK_SERVICE_EMAIL and DLR_VIDYADESK_SERVICE_PASSWORD must belong to a dedicated Supabase account with the viewer role in that archive.
- The route verifies the account's archive membership with the existing RLS-aware access layer and requires the viewer role only.
- It queries through the authenticated user transport, not the service-role key.
- A narrowly scoped SQL RPC re-checks viewer membership and active archive status, then returns only COUNT(*) and MAX(uploaded_at) for visibility=public and is_archived=false.
- Query parameters are rejected. The route cannot select another archive or school.

## Activation gates

Do not configure this endpoint until:
1. A dedicated non-human Supabase service identity has been created for VidyaDesk.
2. That identity has only viewer membership in the correct UMV Tetahali archive.
3. The archive's exact active name has been checked and stored in DLR_VIDYADESK_ARCHIVE_NAME.
4. The machine token and viewer credentials are stored in Bitwarden and injected only into the DLR server environment.
5. The VidyaDesk caller is configured with the matching machine token in a server-only environment variable.
6. The network path is approved. The current DLR API port is tailnet-only; no Tailscale Funnel or public route was changed.

Do not use the Supabase service-role key as a shortcut around archive membership/RLS. Do not reuse a human owner's password or session. The new RPC is authenticated-only, rejects non-viewers, and returns aggregates rather than rows. Until all gates are satisfied, the route returns 503 and no archive data is queried.
