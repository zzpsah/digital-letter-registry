# Project Rules

1. Never commit letters, scans, student data, contact details, identifiers, credentials, tokens, keys, or sensitive logs.
2. Originals are immutable; metadata and derived text retain source and processing provenance.
3. OCR and assisted analysis are not authoritative; users can review and correct derived data.
4. Keep source-specific records separate; do not speculate about identity matches.
5. Prioritize Hindi-first content, mobile accessibility, and low bandwidth.
6. Create an enhancement brain before substantial implementation or integration work.
7. Do not deploy, import live data, configure credentials, or change production infrastructure without explicit approval.
8. Before meaningful work, read the repository's README, RULES, AGENTS, relevant docs, `.ai/` state, and relevant `brain/` enhancement context. Repository evidence is authoritative over chat memory.
9. After meaningful work, synchronize all affected source evidence and status records, including README/docs when scope or behavior changes, root TASKS, `.ai/`, and the relevant `brain/` files. Never leave stale project status documentation knowingly.
10. UI/UX work is governed by `docs/UI-DESIGN-CONTRACT.md`; preserve its colors, layout, language/search/auth/delete/restore invariants unless explicitly asked to change them. Do not wholesale redesign the portal as incidental work.

11. Keep `docs/TECHNICAL-FLOWCHART.html` and `docs/INFORMATION-FLOW-AND-DEPLOYMENT.md` synchronized with changes to routes, URLs, ports, services/timers, integrations, processing logic, translation behavior, storage/security boundaries, and failure handling. Update them in the same change; label unverified details clearly and do not expose secrets or private runtime identifiers.
