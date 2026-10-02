# DLR Account Administration — Project

## Goal
Make DLR authentication provider-independent and computer-independent. A DLR account may use any valid email address; Gmail is optional. Google Sign-In remains an optional convenience provider.

## Roles
- admin: manage members/invites and privileged archive operations.
- editor: read/search plus intake/write workflows.
- viewer: read/search only.

## Onboarding model
DLR access is invite/approval based. An authenticated admin pre-authorizes an email with a role. The invited person can then establish a Supabase Auth account using an email/password registration flow or Magic Link. A database trigger converts a matching pending invite into an active archive membership.

Direct unaffiliated Supabase signups do not grant DLR access because every application request still requires an active archive membership.
