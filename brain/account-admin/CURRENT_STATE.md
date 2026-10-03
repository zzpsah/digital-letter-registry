# DLR Account Administration — Current State

Last verified: 2026-10-03.

Current state:
- archive membership roles are `admin`, `editor`, and `viewer`;
- email/password sign-in is implemented independently of Gmail;
- self-service account creation creates a disabled viewer membership until an active admin approves it;
- the admin UI/API supports member role and active/disabled management;
- last-active-admin protection is enforced by the database;
- Magic Link remains recovery/legacy compatibility and Google Sign-In remains optional;
- the live bootstrap admin successfully updated the DLR password through the Account flow on 2026-10-03;
- no password value is stored or logged by DLR project documentation;
- no real archive letters have been ingested.

Remaining account/runtime verification:
- complete the real short-lived authenticated HTTP/PostgREST vertical slice with actual sessions;
- enable leaked-password protection when hosted Auth configuration access is available;
- keep all real archive mutations separately approval-gated.
