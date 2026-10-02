# Live Integration Checkpoint

Last verified: 2026-10-02

## Completed

- Private archive Drive structure is reachable.
- A synthetic PDF was generated and uploaded successfully into the private `originals/` folder.
- The uploaded file used the approved archive filename convention.
- The synthetic source document used to generate the PDF was deleted after export.
- The uploaded PDF was verified as private/not shared.
- SHA-256 fingerprinting was computed for the synthetic PDF.
- Supabase passwordless signup was initiated for the archive owner.
- The archive owner now exists in Supabase Auth.

## Pending

Supabase reports the archive owner email as unconfirmed.

Because all archive tables enforce RLS with:

```text
auth.uid() = owner_id
```

the live Data API insert test must wait until the owner confirms the Supabase email.

## Next verification after confirmation

1. Obtain an authenticated user session.
2. Insert the synthetic Drive-backed source into `letters`.
3. Initialize `letter_processing`.
4. Confirm the owner can read the rows through RLS.
5. Confirm an unauthenticated request cannot read/write them.
6. Confirm duplicate SHA protection rejects a second source with the same content.
7. Keep all real archive letters untouched.

## Privacy

This public repository does not record the private Drive file ID, Drive folder ID, Supabase project reference, Auth user UUID, email verification token, session token, API key, or other credential.
