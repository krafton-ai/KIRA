# Bridge Release Checklist

Use this checklist before shipping the first `KIRA-Slack -> KiraClaw` bridge release.

## Identity

- preserve `com.krafton.kira`
- preserve the updater S3 feed
- preserve old icons and signing assets
- keep bridge builds named `KIRA`

## Local Compatibility

- `~/.kira/config.env` still loads cleanly
- legacy Slack tokens still connect
- legacy workspace base dir still resolves
- legacy credential file discovery still works

## Runtime

- desktop app starts and reaches `healthy`
- daemon starts from packaged resources
- packaged bridge app auto-installs `uv` if it is missing on the target machine
- Slack chat works
- desktop chat works
- skills load from `Filesystem Base Dir/skills`
- memory writes to `Filesystem Base Dir/memories`

## Build Verification

Run:

- `npm --prefix apps/desktop run verify:bridge`

That preflight checks:

- local prerequisites
- bridge build config shape
- desktop syntax
- `pytest`
- smoke packaged bridge output layout

## Final Release Gate

- signed mac build succeeds
- notarization succeeds
- update feed serves the new bridge artifact
- existing KIRA-Slack install updates in place without reinstall
