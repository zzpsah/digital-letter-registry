# Project AI Entry Point

This repository uses three documentation layers with distinct roles:

- `docs/` — durable human/project documentation: handoff, architecture, security, decisions, tests.
- `brain/` — current working memory only: current state, active decisions, and next tasks.
- `.ai/` — lightweight AI navigation/index pointers only.

Before substantial work, read:
1. `README.md`
2. `PRD.md`
3. `docs/PROJECT-HANDOFF.md`
4. `docs/ARCHITECTURE.md`
5. `docs/DECISIONS.md`
6. `brain/CURRENT_STATE.md`
7. `brain/DECISIONS.md`
8. `brain/TASKS.md`
9. `.ai/STATE-INDEX.md`

Do not duplicate durable project documentation into `brain/` or `.ai/`.

Repository-local source and documentation are authoritative over chat/account memory. No documentation file grants deployment, credential, production, or destructive authority.
