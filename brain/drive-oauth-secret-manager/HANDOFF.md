# Drive OAuth Secret Manager — Handoff

Read project rules, `.ai/CURRENT-STATE.md`, root `TASKS.md`, this brain, and `brain/runtime-verification/` before continuing.

Resume by confirming the private runtime still uses secret-manager-injected refresh credentials and that no persistent credential file has been reintroduced. Complete write-capable OAuth re-consent through the private operations runbook, rotate the refresh token without printing it, then run synthetic upload/write/cleanup before changing any real-intake authorization.
