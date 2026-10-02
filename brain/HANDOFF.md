# Project Brain — Handoff

Before meaningful work, read `AGENTS.md`, `RULES.md`, README/PRD, `.ai/manifest.yaml`, `.ai/STATE-INDEX.md`, `.ai/PROJECT.md`, `.ai/CURRENT-STATE.md`, root `TASKS.md`, `brain/README.md`, and the relevant enhancement brain.

Repository evidence is authoritative over chat memory. After meaningful work, synchronize source evidence plus all affected README/docs, root tasks, `.ai/`, and relevant `brain/` records.

Current runtime checkpoint: DB-level synthetic owner RLS insert/read and wrong-user denial are verified using simulated request JWT claims. A real short-lived authenticated HTTP/PostgREST vertical slice is still pending. One synthetic verification row remains; no real archive letters exist.

Do not deploy, ingest real documents, activate live connectors, rename real Drive files, configure or expose secrets, or perform destructive live-data actions without the required explicit authorization.
