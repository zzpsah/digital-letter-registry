# Drive OAuth Secret Manager — Security

- Never commit OAuth refresh/access tokens, client-secret values, secret-manager machine credentials or private Drive identifiers.
- Inject only the explicitly required DLR OAuth keys into the application process.
- Do not pass the secret-manager machine token to the application child process.
- Keep access tokens in memory only.
- Use synthetic Drive objects for authorization verification.
- A broader OAuth scope does not bypass real-intake, rename or import approval gates.
- Public repository documentation records contracts and verification state, not private server paths or secret values.
