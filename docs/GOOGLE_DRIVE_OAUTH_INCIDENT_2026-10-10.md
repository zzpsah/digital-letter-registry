# Google Drive OAuth incident — 2026-10-10

## User-visible symptom

The authenticated eLetters **View** and **Download** actions failed to open the private original document and showed an “Original could not be opened” message.

## Evidence and root cause

Production Vercel runtime logs showed both original-stream and download requests failing during Google OAuth refresh with HTTP 401 `invalid_client`; Google's response said the configured client secret was invalid. A separate comparison found that the Google OAuth Client ID saved in Bitwarden did not match the Client ID configured in Vercel Production. This pointed to a mismatched/stale OAuth client configuration, rather than a View/Download button implementation failure.

The Client ID and Client Secret are a pair: the secret must belong to the same OAuth client as `GOOGLE_OAUTH_CLIENT_ID`. A refresh token must also have been issued for that client. Do not record credential values in this document, Git, screenshots, or logs.

## Resolution status

On 2026-10-10 the user subsequently confirmed that both **View** and **Download** worked in an authenticated browser session. Production API health also returned HTTP 200, and the latest production deployment was Ready.

**Operational status: user-verified working.** The exact credential/configuration mutation that restored service was not independently captured in the incident evidence. Therefore this record does not claim that a specific secret was rotated or that the Client ID mismatch was definitively corrected. Follow-up verification should confirm that the current Vercel Production `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` belong to the same Google Cloud OAuth client and that fresh View/Download requests produce no new `invalid_client` errors.

## What to check if it recurs

1. In Google Cloud Console, identify the OAuth 2.0 Client ID that is intended for this deployment.
2. In Vercel Production, ensure `GOOGLE_OAUTH_CLIENT_ID` matches that client and `GOOGLE_OAUTH_CLIENT_SECRET` is the active secret for that exact client.
3. Verify `GOOGLE_DRIVE_REFRESH_TOKEN` was issued for the same OAuth client and has not been revoked.
4. Redeploy Production after changing environment variables.
5. Sign in and test both View and Download against an authorized letter; inspect Vercel runtime logs for fresh errors.

Do not paste secrets or refresh tokens into chat or commit them. Do not make private Drive originals public as a workaround.

## Verification boundary

- Production health endpoint: HTTP 200 at the time checked.
- Authenticated View: confirmed working by user on 2026-10-10.
- Authenticated Download: confirmed working by user on 2026-10-10.
- OAuth log cleanliness after the successful user test: not yet independently verified; the targeted recent-log query returned no matching error lines, which is not proof of a successful authenticated backend request.
