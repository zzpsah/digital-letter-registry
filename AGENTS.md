# Project AI Entry Point

This project is governed by Development OS (DevOS), the DevOS Vibe Coding standard, portable `.ai/` context, and the mandatory `brain/` project memory.

Before substantial work: read the DevOS/Vibe Coding instructions, `.ai/manifest.yaml`, `.ai/STATE-INDEX.md`, `.ai/PROJECT.md`, `.ai/CURRENT-STATE.md`, `brain/README.md`, and the relevant `brain/<enhancement>/` documents; then inspect source, tests, and Git state.

When substantial feature or enhancement work begins, create or update `brain/<enhancement>/` using `brain/ENHANCEMENT-STANDARD.md`. After meaningful work, synchronize source evidence, `.ai/`, project docs, and the relevant brain documents.

For any change affecting architecture or runtime behavior—including URLs/routes, ports, systemd services/timers, integrations/tools, OCR/AI/translation branches, storage boundaries, security exposure, or error/retry paths—update `docs/TECHNICAL-FLOWCHART.html` and `docs/INFORMATION-FLOW-AND-DEPLOYMENT.md` in the same change. Keep README and current-state/brain records aligned. Label unverified details as unconfirmed and never expose secrets or private runtime identifiers.

Repository-local state is authoritative over AI account/chat memory. Brain files record context and decisions but never grant execution, provider, deployment, publication, or destructive authority.

Before any UI, navigation, auth UX, search UX, language, recipient, delete/restore, or admin-console change, **must read `docs/UI-DESIGN-CONTRACT.md` and `brain/ui-governance/`**. The accepted UI is a locked baseline: do not perform a wholesale redesign, recolor, framework rewrite, or navigation replacement unless the user explicitly requests it.

## Remote access / Desktop Commander

For authorized Oracle VPS access, read [`docs/REMOTE-ACCESS.md`](docs/REMOTE-ACCESS.md). A new AI chat must use Desktop Commander `list_devices`, select the online `oracle-server`, ping it, and only then operate on the live server. Do not confuse GitHub access with VPS/runtime access.
