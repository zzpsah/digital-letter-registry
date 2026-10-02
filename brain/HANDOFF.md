# Project Brain — Handoff

Before meaningful work, read `AGENTS.md`, `RULES.md`, README/PRD, `.ai/manifest.yaml`, `.ai/STATE-INDEX.md`, `.ai/PROJECT.md`, `.ai/CURRENT-STATE.md`, root `TASKS.md`, `brain/README.md`, and the relevant enhancement brain.

Repository evidence is authoritative over chat memory. After meaningful work, synchronize source evidence plus all affected README/docs, root tasks, `.ai/`, and relevant `brain/` records.

Current runtime checkpoint: DB-level synthetic owner RLS insert/read and wrong-user denial are verified using simulated request JWT claims. A real short-lived authenticated HTTP/PostgREST vertical slice is still pending. Magic-link delivery to the archive owner was verified, but the hosted email template is still the default direct-confirmation flow while the application callback expects a server-readable token-hash flow. The connected execution layer correctly blocked forwarding the one-time auth token into a remote command, so no credential was persisted or bypassed.

Private Google Drive archive discovery was re-verified through the connected Drive account: the archive has `originals/`, `quarantine/`, and `exports/`; `originals/` contains only the previously used synthetic integration PDF. The VPS's existing read-only rclone remote does not expose this archive path, so refreshable Drive OAuth/runtime wiring remains pending.

One synthetic DB verification row remains; no real archive letters exist.

Do not deploy, ingest real documents, activate live connectors, rename real Drive files, configure or expose secrets, or perform destructive live-data actions without the required explicit authorization.
