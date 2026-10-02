# Project

## Identity

- Project ID: digital-letter-registry
- Name: Digital Letter Registry
- Formal archive name: Official Letter Intelligence Archive
- Repository: zzpsah/digital-letter-registry

## Purpose

Operate a private, Hindi-first archive for official school and government letters. It preserves immutable originals while deriving searchable OCR, structured context, filename metadata, relationships, and reviewable lifecycle information.

## Current scope

The application foundation is implemented in the public repository:

- FastAPI private API and Hindi-first mobile PWA.
- Passwordless Supabase-authenticated sessions using Secure HttpOnly cookies.
- Synthetic-first intake, immutable Drive storage adapter, Supabase persistence, durable processing jobs, duplicate checks, and source provenance.
- Native PDF extraction, Hindi/English OCR fallback contracts, structured-context adapters, embeddings, full-text/fuzzy/semantic/hybrid search, and relationship/reprocessing workflows.
- Preview-first historical import and approval-locked rename execution.

## Safety boundary

- Public Git contains code, documentation, migrations, and synthetic fixtures only.
- Real letters, private Drive identifiers/URLs, API keys, Supabase credentials, OAuth tokens, SSH keys, and server details must never be committed.
- Real intake remains disabled by default.
- Live letter ingestion, renames, imports, provider configuration, and production deployment require explicit authorization.

## Current integration gaps

- Google Drive OAuth is verified in the private runtime through secret-manager-injected refresh credentials; read/list/stream and disposable synthetic write/delete checks passed.
- Gemini runtime credentials are not yet configured/verified.
- A final authenticated HTTP/PostgREST synthetic vertical-slice check remains pending.
- Hosted Supabase magic-link template and production redirect/Site URL setup remain an external dashboard task.


## Drive deployment model

- Source code is not bound to a specific Google account.
- Each deployment must use an explicitly authorized OAuth identity plus configured archive folder references.
- Current private runtime is a single archive-owner deployment.
- A second Google account must use separate OAuth/secret-manager configuration and archive references. Authorization is also subject to the Google OAuth consent-screen publishing/testing policy.


## Authentication responsibility

- Passwordless email/Magic Link identifies the DLR user and establishes the browser session.
- Supabase RLS consumes that identity to enforce row ownership/isolation.
- Tailscale controls private network reachability.
- Google OAuth controls backend access to the configured Drive archive.
- Real document mutation remains separately approval-gated even for a successfully authenticated owner.
