# Vercel Hosting — Project

## Goal
Make the DLR web application reachable from ordinary browsers without requiring Tailscale, while preserving Supabase authorization, private Drive storage, and existing real-intake safety gates.

## Initial deployment boundary
- Vercel hosts the DLR web/auth/search/admin control plane.
- Supabase remains the identity/database authorization layer.
- Google Drive remains private original-file storage accessed server-side with scoped OAuth credentials.
- Real intake remains disabled unless explicitly enabled later.
- OCR/background processing that depends on VPS system binaries remains an Oracle/private-worker concern.
