# AI Remote Access / Desktop Commander

This repository may be maintained through the authorized Oracle VPS using the Remote Desktop Commander connector.

## Connection procedure

1. Use the Desktop Commander `list_devices` action first.
2. Select the online device named `oracle-server`. Do not rely on a hard-coded device UUID; discover the current ID from `list_devices`.
3. Use `ping` to confirm the device is reachable.
4. Use absolute paths on the server. Repository working copies live under `/home/prashant/projects/<repo-name>`.
5. Use `read_file` / `list_directory` for inspection and `start_process` for Git, tests, service checks, and shell workflows.
6. Before edits, run `git status --short` and read repository `AGENTS.md`, `DEVOS.md`, `.ai/CURRENT-STATE.md` or equivalent project handoff files when present.
7. Never assume GitHub state equals live runtime state. Compare the repository with the documented runtime path before deployment.
8. Do not expose or commit credentials, OAuth tokens, cookies, sessions, private datasets, generated indexes, caches, logs containing personal data, or runtime-only identifiers.
9. After changes, run the repository's tests/checks, `git diff --check`, then commit/push only after verifying the intended scope.
10. For user-systemd services on the Oracle VPS, use the existing user session environment if required (`XDG_RUNTIME_DIR=/run/user/$(id -u)` and the matching DBus user bus) rather than changing system-wide configuration.

## If Desktop Commander is unavailable in a new chat

The AI should not pretend it has server access. It should ask the user to connect/install the Remote Desktop Commander plugin/connector for that chat, then call `list_devices` again. GitHub access alone is not equivalent to VPS access.

## Control principle

GitHub is the durable source repository. The Oracle VPS is the live runtime. Changes should normally flow: inspect live state -> update canonical repository -> test -> deploy/sync only the approved files -> verify live health. Runtime data must stay outside Git unless a project explicitly documents a safe exception.
