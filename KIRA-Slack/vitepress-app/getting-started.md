# Getting Started

This guide is intentionally short. The old `KIRA-Slack` setup surface is no longer the main product path.

Use `KiraClaw` for fresh installs.

## 1. Download

- macOS (Apple Silicon): [Download KiraClaw for macOS](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-arm64.dmg)
- Windows: [Download KiraClaw for Windows](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-x64.exe)

## 2. Install

### macOS

1. Open the `.dmg`
2. Drag `KiraClaw.app` into `Applications`
3. Launch it

If macOS blocks first launch, see [Troubleshooting](/troubleshooting).

### Windows

1. Run the installer
2. Finish the setup wizard
3. Launch `KiraClaw`

## 3. Choose a workspace

KiraClaw uses a local filesystem base directory for:

- `skills/`
- `memories/`
- `schedule_data/`
- `logs/`

The current default workspace is typically under `~/Documents/KiraClaw`.

## 4. Open the desktop app

Inside the app, start with:

- `Talk`
- `Channels`
- `Skills`
- `Schedules`
- `Logs`

## 5. Optional: connect channels

The app currently supports:

- Slack
- Telegram
- Discord

Channel settings live in the desktop `Channels` screen.

## 6. Identity and persona

Set:

- your agent name
- persona text

in `Settings > Identity`.

## 7. Verify the runtime

The simplest smoke test is:

1. Open `Talk`
2. Ask a short question
3. Confirm that both internal summary and spoken reply appear

## Migrating from KIRA-Slack

`KIRA-Slack` is now treated as legacy.

If you already used `KIRA-Slack`, KiraClaw can still reuse:

- `~/.kira/config.env`
- `~/.kira/credential.json`

That lets you move forward without rebuilding everything from scratch.
