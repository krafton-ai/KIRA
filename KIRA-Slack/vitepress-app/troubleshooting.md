# Troubleshooting

## macOS says the app cannot be opened

If the current build is not notarized yet, macOS may show a warning on first launch.

Use this path:

1. In Finder, locate `KiraClaw.app`
2. Right-click the app
3. Choose `Open`
4. Confirm again

After that, later launches usually work normally.

## The old KIRA-Slack app still opens

That means you are still launching the legacy app.

Check that you installed and opened:

- `KiraClaw.app`

not the older `KIRA` app.

## I expected KIRA-Slack to auto-update in place

`KIRA-Slack` is now treated as legacy.

Use manual migration instead:

1. Download the latest `KiraClaw`
2. Install it as a separate app
3. Reuse your existing `~/.kira` config if needed

## How updates appear in KiraClaw now

KiraClaw checks for updates:

- once when the app starts
- again when you enter `Home`

The `Home` screen does not always show a button.

- If you are already current, no update button is shown
- If a new version is available, `Update to vX` appears
- After the download finishes, it changes to `Restart to Update`

If you keep the app open for a long time, go back to `Home` to refresh the update state.

## Slack or Telegram is not responding

Check the desktop app:

- `Channels`
- `Logs`

If the runtime is healthy but no outward reply appears, inspect:

- internal summary
- spoken reply
- tool usage
- silent reason

from the `Logs` screen.

## OpenAI fails with a tools array error

If you use the OpenAI provider and see an error like:

- `Invalid 'tools': array too long`
- `Expected an array with maximum length 128`

then too many tools are currently enabled for that model request.

This usually happens when several MCP servers are enabled at the same time.

Use one of these fixes:

1. Open `Settings > MCP`
2. Disable some MCP servers you do not need right now
3. Restart the engine
4. Try the run again

If you want to keep a large tool surface enabled, use a provider/model combination that tolerates more tools better than the current OpenAI chat path.

## Where are my local files?

KiraClaw keeps local state under your filesystem base directory, including:

- `skills/`
- `memories/`
- `schedule_data/`
- `logs/`

The desktop app can open the relevant folders directly.
