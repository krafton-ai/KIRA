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
