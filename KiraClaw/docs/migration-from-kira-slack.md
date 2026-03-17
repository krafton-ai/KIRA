# Migration From KIRA-Slack

## Goal

Existing KIRA-Slack users should move to KiraClaw through familiar updates, not through a disruptive reinstall story.

## Rules

- Do not break the current KIRA-Slack auto-update path.
- Do not force users to manually move data if it can be migrated.
- Do not couple KiraClaw core design to old KIRA-Slack internals.

## Bridge Model

Use two tracks:

### Track A: New Product Development

Folder: `KiraClaw/`

Purpose:

- build the new daemon
- build the new desktop shell
- keep the new architecture clean

### Track B: Existing User Bridge

Folder: `KIRA-Slack/`

Purpose:

- ship bridge releases
- preserve existing installer and updater identity
- migrate config and data forward
- preserve Slack-facing continuity for existing users

## Items To Preserve During Bridge Releases

- existing `appId`
- existing updater feed location
- existing signing and notarization flow
- existing user config directory handling
- existing local data discovery
- existing Slack configuration and team identity
- the expectation that there is an installed local app

## Data Strategy

KiraClaw should be able to detect legacy KIRA-Slack state.

Current bridge rule:

- legacy home: `~/.kira`
- new home: `~/.kiraclaw`

In `auto` mode, the daemon now prefers `~/.kira` when it already exists.
That lets the bridge keep using the existing local config, Slack identity, workspace base dir, and credential file without forcing a reinstall-time migration.

## Sequencing

1. Stabilize KiraClaw daemon API.
2. Build a minimal Slack adapter against the daemon.
3. Keep `.kira` compatibility until the bridge release is stable.
4. Add explicit migration code from `~/.kira` to `~/.kiraclaw` only when needed.
5. Build the desktop shell against the same daemon.
6. Only then prepare a KIRA-Slack bridge release.

## Non-Goal For This Phase

This phase does not rename KIRA-Slack in place.

It creates the clean replacement architecture first.
