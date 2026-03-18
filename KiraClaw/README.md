# KiraClaw

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18.0.0-green)](https://nodejs.org/)
[![Electron](https://img.shields.io/badge/electron-39.x-9feaf9)](https://www.electronjs.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey)]()
[![Bridge](https://img.shields.io/badge/migration-KIRA--Slack%20bridge-orange)](docs/migration-from-kira-slack.md)

Agentic desktop runtime for KIRA.

KiraClaw is the successor product line to `KIRA-Slack`. It keeps the local desktop product shape, but moves the runtime toward a more agentic model:

- adapters are the outside ears and mouth
- the core agent thinks, plans, and chooses tools
- `speak` is the explicit outward speech action
- `internal_summary` is the internal run summary for QA and diagnostics
- memory has both implicit runtime behavior and explicit index tools

`KIRA-Slack` is now the legacy product line used only for bridge migration and auto-update replacement. New runtime work happens in `KiraClaw`.

---

## Demo

| Search + PPTX | GitRepo + PDF | Web + Wiki |
|:---:|:---:|:---:|
| <video src="https://github.com/user-attachments/assets/284f9d0d-056c-42e9-8f1f-19873431ddba" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/721bc704-8b1a-4673-829a-52309ae69601" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/7329039a-fdad-4f4b-8f03-65402e4d6f6c" width="240" controls></video> |

| Proactive + Thread | Email + Schedule | Proactive + Translate |
|:---:|:---:|:---:|
| <video src="https://github.com/user-attachments/assets/9ee1a520-507c-408a-a1d2-4a7a393385eb" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/79959017-67c2-4109-98bd-8c1dbba2b34f" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/c78768be-580e-42e8-a3d8-34eb5f0db6cb" width="240" controls></video> |

---

## What Is KiraClaw?

KiraClaw is a local AI agent runtime that combines:

- a long-running local gateway
- a desktop control plane
- channel adapters for Slack, Telegram, and Discord
- local memory, skills, schedules, and run logs

It is closer to an agent runtime than to a simple chat wrapper.

The design goal is small and explicit:

- `krim-sdk` is the external agent engine
- `agentd` is the local gateway
- `desktop` is the packaged shell for setup, status, runs, logs, and direct chat
- schedules are the current automation surface

---

## Why It Exists

`KIRA-Slack` proved the product shell:

- desktop packaging
- local settings
- update flow
- channel integrations
- local data handling

`KRIM` proved the core loop can stay small.

KiraClaw combines those lessons without dragging the old multi-agent Slack-first structure forward.

---

## Current Product Shape

### Core surfaces

- `Talk`: direct local chat against the same daemon
- `Channels`: Slack, Telegram, and Discord on the same runtime
- `Skills`: workspace skills loaded from `Filesystem Base Dir/skills`
- `Schedules`: time-based automation runs
- `Logs`: recent run logs, internal summaries, spoken replies, and tool usage

### Current runtime rules

- shared rooms are treated as ambient spaces, not strict one-user request channels
- grouped room messages are passed in as room transcripts
- outward speech in channels should happen through `speak`
- silent completion is valid for schedules and shared-room runs
- run-level observability is persisted to `Filesystem Base Dir/logs/runs.jsonl`

### Legacy compatibility

The daemon still supports bridge-mode compatibility with existing `KIRA-Slack` installs:

- `KIRACLAW_HOME_MODE=auto` prefers `~/.kira` before `~/.kiraclaw`
- legacy `~/.kira/config.env` is used to backfill tokens and workspace settings
- legacy `~/.kira/credential.json` is reused for Vertex AI when needed

See [migration-from-kira-slack.md](docs/migration-from-kira-slack.md).

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- `uv`

Optional:

- Slack app credentials
- Telegram bot token
- Discord bot token
- Anthropic / OpenAI / Vertex credentials depending on provider

### Run the daemon

```bash
cd KiraClaw
cp .env.example .env
uv run kiraclaw-agentd
```

Check health:

```bash
curl http://127.0.0.1:8787/health
```

Useful endpoints:

- `GET /v1/runtime`
- `GET /v1/sessions`
- `GET /v1/run-logs`
- `GET /v1/schedules`
- `GET /v1/skills`
- `POST /v1/runs`

### Run the desktop shell

```bash
cd KiraClaw/apps/desktop
npm install
npm start
```

The desktop app is the local control plane for:

- runtime status
- direct test runs
- identity and persona settings
- channel settings
- MCP settings
- skills and schedules visibility
- recent run logs

---

## Agentic Runtime Model

KiraClaw no longer assumes that every run must directly produce a user-facing answer.

### Runtime concepts

- `adapter`: receives external input and publishes external output
- `core agent`: thinks, decides, and uses tools
- `speak`: explicit outward speech
- `internal_summary`: internal run summary
- `memory index`: stable metadata for memory lookup and updates

### Memory model

Memory now has two layers:

- implicit runtime retrieval/save for normal runs
- explicit tools for memory-aware work

The intended explicit flow is:

1. `memory_index_search`
2. read or edit the actual memory files
3. `memory_index_save`

That keeps the index stable while still letting the agent manipulate the underlying memory files.

### Channel behavior

- direct replies to the current conversation should use `speak`
- proactive delivery to another target should use explicit channel tools
- shared-room runs can remain silent if speaking is not useful

---

## Features

### Desktop

- local runtime control
- direct chat surface
- settings for identity, persona, channels, workspace, and MCP
- recent run logs with prompt, internal summary, spoken reply, and tool usage

### Channels

- Slack
- Telegram
- Discord

### Local agent substrate

- skills from `Filesystem Base Dir/skills`
- local memory store and index
- schedules for time-based automation
- persistent run logs

### Bridge release support

- keeps `KIRA` app identity for migration releases
- uses the existing update line for `KIRA-Slack -> KiraClaw`
- keeps the bridge-specific release checklist separate from the core runtime design

See [bridge-release-checklist.md](docs/bridge-release-checklist.md).

---

## Project Structure

```text
KiraClaw/
  apps/
    agentd/     # Local Python gateway
    desktop/    # Electron desktop shell
  defaults/
    skills/     # Seed skills copied into new workspaces
  docs/
    architecture.md
    bridge-release-checklist.md
    migration-from-kira-slack.md
    qa-benchmark.md
  scripts/
    verify_bridge_release.sh
  pyproject.toml
  package.json
```

---

## Development

### Test the Python side

```bash
cd KiraClaw
uv run pytest
```

### Test the desktop side

```bash
cd KiraClaw/apps/desktop
node --check renderer/app/*.mjs
npm start
```

### Bridge verification

```bash
cd KiraClaw/apps/desktop
npm run verify:bridge
```

---

## Documentation

- [architecture.md](docs/architecture.md)
- [migration-from-kira-slack.md](docs/migration-from-kira-slack.md)
- [bridge-release-checklist.md](docs/bridge-release-checklist.md)
- [qa-benchmark.md](docs/qa-benchmark.md)
- [desktop/README.md](apps/desktop/README.md)

---

## Notes

- KiraClaw is the active runtime line.
- `KIRA-Slack` is now legacy and kept for bridge migration only.
- The current product shape is intentionally small: `Chat + Schedules + Local Control Plane`.
- The runtime should stay agentic without becoming structurally heavy.
