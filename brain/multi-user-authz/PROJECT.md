# Multi-user authorization — Project

## Goal
Replace the single configured archive-owner authorization model with archive membership and roles while keeping Supabase Auth provider-neutral.

## Roles
- admin
- editor
- viewer

## Login methods
Authentication provider is independent of authorization. Email/password, Magic Link, Google Sign-In, and future providers may all resolve to a Supabase user. Access is granted only by active archive membership.
