# Drive OAuth Secret Manager — Security

- Never commit OAuth refresh/access tokens, client-secret values, secret-manager machine credentials or private Drive identifiers.
- Inject only the explicitly required DLR OAuth keys into the application process.
- Do not pass the secret-manager machine token to the application child process.
- Keep access tokens in memory only.
- Use synthetic Drive objects for authorization verification.
- A broader OAuth scope does not bypass real-intake, rename or import approval gates.
- Public repository documentation records contracts and verification state, not private server paths or secret values.


## OAuth permission boundary

- The verified private runtime uses a write-capable Google Drive OAuth grant.
- That Google-level grant is broader than DLR's intended archive-specific usage.
- Application logic must stay constrained to configured archive folder/object references.
- Real ingestion, rename, delete and historical adoption remain separately approval-gated.
- Another Google account requires separate OAuth consent, secret-manager credentials and archive-folder configuration.
- Depending on the Google OAuth consent-screen mode, additional accounts may require test-user allowlisting.
