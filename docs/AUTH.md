# Passwordless Authentication

The private archive uses Supabase Auth and Row-Level Security. Browser sessions
are handled server-side; access and refresh tokens are stored in HttpOnly
cookies and are not exposed to page JavaScript.

## Required Supabase configuration

Configure the application Site URL and allowed redirects for the environment.
For local development, allow the local FastAPI origin. For a future private
deployment, use its HTTPS origin.

The Magic Link email template must use Supabase's token-hash form so the link
lands on the application callback instead of returning access tokens in a URL
fragment.

Use this pattern in the hosted Supabase **Magic Link** template:

```html
<h2>Sign in to Official Letter Intelligence Archive</h2>
<p>
  <a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email">
    Sign in
  </a>
</p>
```

This follows Supabase's current server-side/PKCE guidance for token-hash email
verification.

## Runtime variables

```bash
SUPABASE_URL=...
SUPABASE_PUBLISHABLE_KEY=...
AUTH_REDIRECT_URL=https://archive.example.com/auth/confirm
AUTH_COOKIE_SECURE=true
```

For local HTTP development only:

```bash
AUTH_REDIRECT_URL=http://localhost:8000/auth/confirm
AUTH_COOKIE_SECURE=false
```

## Flow

```text
email address
  → POST /api/v1/auth/magic-link
  → Supabase sends one-time token-hash link
  → GET /auth/confirm?token_hash=...&type=email
  → server verifies token hash with Supabase
  → server stores access + refresh tokens in HttpOnly SameSite=Lax cookies
  → 303 redirect to /
  → API requests use cookie session under the user's normal RLS identity
```

When the access cookie expires, the server uses the refresh-token cookie to
obtain a rotated session and rewrites both cookies. Logout clears both cookies.

Auth callback/session responses use `Cache-Control: private, no-store`.

## Security boundaries

- New user creation remains disabled in the magic-link request.
- Do not commit access tokens, refresh tokens, token hashes, project URLs, or keys.
- Do not put Supabase access/refresh tokens in localStorage/sessionStorage.
- Do not cache responses that contain authentication cookies.
- Keep `AUTH_COOKIE_SECURE=true` for HTTPS environments.
