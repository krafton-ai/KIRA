# KiraClaw Desktop

KiraClaw Desktop is a small Electron shell over the same local engine that Slack uses.

Current scope:

- start and stop the local KIRA Engine
- edit `~/.kira/config.env`
- run direct desktop chat through the same daemon API
- surface a simple branded home screen for the local agent

The code is intentionally split by responsibility.

Main process:

- `main.js`: app bootstrap only
- `lib/config-store.js`: `.kira/config.env` read and write
- `lib/daemon-controller.js`: daemon lifecycle and health checks
- `lib/create-window.js`: BrowserWindow construction
- `lib/register-ipc.js`: Electron IPC registration

Renderer:

- `renderer/app/index.mjs`: renderer bootstrap and orchestration
- `renderer/app/home.mjs`: landing and engine status UI
- `renderer/app/settings.mjs`: settings form state and provider-specific fields
- `renderer/app/chat.mjs`: direct chat surface
- `renderer/app/navigation.mjs`: sidebar navigation
- `renderer/app/branding.mjs`: agent name and copy updates
- `renderer/app/dom.mjs`: small DOM helpers and secret field toggles
- `renderer/app/state.mjs`: shared renderer state

Slack remains the first real channel.
Desktop direct chat is still a thin client over the same daemon API.

## Bridge Build

KiraClaw keeps its own dev identity, but bridge releases for existing KIRA-Slack users
should preserve the old updater lineage.

Use:

- `npm run build:bridge`
- `npm run build:bridge:mac`
- `npm run build:bridge:win`
- `npm run build:bridge:smoke`
- `npm run build:bridge:smoke:dir`

The bridge build config is:

- [electron-builder.bridge.json](/Users/batteryho/Documents/github/KIRA/KiraClaw/apps/desktop/electron-builder.bridge.json)
- [electron-builder.bridge.smoke.json](/Users/batteryho/Documents/github/KIRA/KiraClaw/apps/desktop/electron-builder.bridge.smoke.json)

Current scope of the bridge scaffold:

- preserves `com.krafton.kira`
- preserves the S3 updater feed
- reuses the old icons and mac entitlements
- stages the KiraClaw Python project under `process.resourcesPath/kiraclaw`
- stages local `KRIM` and `krim-sdk` sources under `process.resourcesPath/kiraclaw/vendor`
- packaged app starts the daemon with `uv run kiraclaw-agentd`

Smoke build scope:

- disables mac signing, hardened runtime, and notarization
- targets a local packaged app smoke run first
- keeps the same staged `process.resourcesPath/kiraclaw` layout so daemon startup can be checked before release signing work

Current bridge assumption:

- `uv` is available on the host machine, as it was in the KIRA-Slack line
