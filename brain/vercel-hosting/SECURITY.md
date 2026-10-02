# Vercel Hosting — Security

- Do not expose Google OAuth refresh tokens, Supabase secret/service keys, or Bitwarden credentials to browser code.
- Use Supabase publishable key server-side/client-safe only where appropriate; authorization remains RLS-backed.
- Keep user sessions HttpOnly + Secure + SameSite=Lax.
- Configure the Vercel production origin in Supabase redirect allow-list before relying on email/OAuth callbacks.
- Keep real intake disabled initially.
- Do not move private archive originals into Git/Vercel build artifacts.
