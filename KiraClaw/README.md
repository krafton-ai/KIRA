# KiraClaw

KiraClaw is the next product line after KIRA-Slack.
The target is to follow OpenClaw as closely as possible while staying simple.

The first principle is to keep the architecture small:

- `krim-sdk` is the embedded agent engine.
- `agentd` is the local long-running gateway.
- `desktop` is the packaged local app for install, config, logs, updates, and future direct chat.
- KIRA-Slack remains the bridge for user migration and auto-update.

## Current Scope

This folder starts with the smallest useful slice:

- architecture and migration docs
- a minimal `agentd` built on `krim-sdk`
- a desktop workspace that stays part of the product plan
- Slack-first product assumptions

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
    migration-from-kira-slack.md
  pyproject.toml
  package.json
```

## Product Assumptions

- The first user-facing channel is Slack.
- The desktop app still exists as a first-class product shell.
- The desktop app can grow into a direct chat surface later.
- Long-running work is a primary use case.
- `krim-sdk.Agent` is the core execution loop.
- One long-running gateway per host is the default shape.
- Bridge mode should feel like the existing KIRA-Slack install.

## Bridge Compatibility

The daemon now prefers legacy KIRA-Slack state when it already exists:

- `KIRACLAW_HOME_MODE=auto` uses `~/.kira` before `~/.kiraclaw`
- legacy `~/.kira/config.env` is used to backfill Slack tokens and workspace base dir
- legacy `~/.kira/credential.json` is reused for Vertex AI if no explicit provider was set
- `KIRACLAW_PROVIDER` can still be set to `claude`, `openai`, or `vertex_ai`

## Watch System

KiraClaw replaces the old checker/proactive split with a smaller `watch` model:

- schedule decides when a watch runs
- each watch defines an instruction, a condition, and an action
- the same KRIM-based agent loop runs the watch
- the watch may use tools, write memory, send Slack messages, or do nothing

This keeps the KIRA-Slack checker idea without rebuilding a separate checker graph.

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
- `GET /v1/watches`
- `GET /v1/watch-runs`
- `POST /v1/watches`
- `POST /v1/watches/{watch_id}/run`
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
- session list
- direct test runs against the daemon

## Notes

- The daemon is intentionally small.
- The desktop app exists as a minimal shell today.
- The first channel is Slack.
- Desktop direct runs exist as a thin test surface, not the main product flow yet.
- KIRA-Slack auto-update migration stays in the existing `KIRA-Slack` product line until a bridge release is ready.
