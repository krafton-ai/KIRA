# KiraClaw

KiraClaw is the next product line after KIRA-Slack.
The target is to follow OpenClaw as closely as possible while staying simple.

The first principle is to keep the architecture small:

- `krim-sdk` is the embedded agent engine.
- `agentd` is the local long-running gateway.
- `desktop` is the packaged local app for install, config, logs, updates, and future direct chat.
- KIRA-Slack remains the bridge for user migration and auto-update.

## Agentic Model

KiraClaw now treats the local engine more like a thinking core than a direct reply generator.

- adapters are the outside ears and mouth
- the core agent thinks, plans, and chooses tools
- `speak` is the explicit outward speech action
- `internal_summary` is the internal run summary kept for QA and diagnostics
- the legacy wire field `final_response` still carries that same internal summary for compatibility
- memory has both implicit runtime behavior and explicit index tools

This keeps the product closer to an agent runtime than to a simple chat wrapper.

## Current Scope

This folder starts with the smallest useful slice:

- architecture and migration docs
- bridge release checklist
- a minimal `agentd` built on `krim-sdk`
- a desktop workspace that stays part of the product plan
- Slack and Telegram channel adapters
- direct desktop chat against the same daemon
- schedules as the current automation surface

It does not try to recreate KIRA-Slack all at once.

## Why This Exists

KRIM already proved the core agent loop can stay small.
KIRA-Slack already proved the product shell needs desktop packaging, config, update, and local data handling.

KiraClaw combines those lessons without inheriting KIRA-Slack's full complexity.

## Initial Layout

```text
KiraClaw/
  apps/
    agentd/     # Local Python gateway using krim-sdk
    desktop/    # Desktop shell for the packaged product
  docs/
    architecture.md
    bridge-release-checklist.md
    migration-from-kira-slack.md
  pyproject.toml
  package.json
```

## Product Assumptions

- Slack remains the first real channel, with Telegram as a lightweight second channel.
- The desktop app still exists as a first-class product shell.
- The desktop app is already a direct chat surface and control plane.
- Long-running work is a primary use case.
- `krim-sdk.Agent` is the core execution loop.
- One long-running gateway per host is the default shape.
- Bridge mode should feel like the existing KIRA-Slack install.
- Shared rooms should be treated as spaces the agent can listen to without being forced to reply every time.

## Bridge Compatibility

The daemon now prefers legacy KIRA-Slack state when it already exists:

- `KIRACLAW_HOME_MODE=auto` uses `~/.kira` before `~/.kiraclaw`
- legacy `~/.kira/config.env` is used to backfill Slack tokens and workspace base dir
- legacy `~/.kira/credential.json` is reused for Vertex AI if no explicit provider was set
- `KIRACLAW_PROVIDER` can still be set to `claude`, `openai`, or `vertex_ai`

## Running The Daemon

```bash
cd /Users/batteryho/Documents/github/KIRA/KiraClaw
cp .env.example .env
uv run kiraclaw-agentd
```

Then check:

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

Slack startup is automatic when the Slack tokens are present in `.env` or legacy `~/.kira/config.env`.

## Running The Desktop Shell

```bash
cd /Users/batteryho/Documents/github/KIRA/KiraClaw/apps/desktop
npm install
npm start
```

The current desktop app is a thin local shell:

- runtime status
- direct test runs against the daemon
- settings for name, persona, channels, MCP, and workspace
- skills and schedules visibility

## Notes

- The daemon is intentionally small.
- The desktop app exists as a minimal shell today.
- The current product shape is `Chat + Schedules`.
- Group rooms rely on `speak` for outward replies instead of forcing every run to produce a visible answer.
- Desktop direct runs expose both internal summaries and spoken replies when they exist.
- Schedules are allowed to finish silently; outward delivery happens only when the agent actually uses `speak` or another explicit channel tool.
- Run-level observability is persisted to `Filesystem Base Dir/logs/runs.jsonl`.
- KIRA-Slack auto-update migration stays in the existing `KIRA-Slack` product line until a bridge release is ready.
