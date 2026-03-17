# KiraClaw Architecture

## Product Goal

KiraClaw is the successor product to KIRA-Slack.

It must:

- feel like a real desktop product on macOS and Windows
- inherit existing KIRA-Slack users with minimal friction
- reuse KRIM's engine instead of rebuilding agent runtime logic
- follow OpenClaw's product shape as closely as possible without inheriting unnecessary complexity

## First Principle

Do not rebuild KIRA-Slack in one shot.

Add one thin layer at a time:

1. `krim-sdk` stays the agent engine.
2. `agentd` becomes the local daemon and product boundary.
3. `desktop` becomes the packaged shell.
4. Slack arrives first as the only chat channel.
5. Desktop direct chat can arrive on the same daemon boundary later.
6. Memory, schedules, and watch systems arrive later as explicit modules.

## OpenClaw Alignment

The target shape is:

- one long-running gateway per host
- embedded agent engine, not a CLI subprocess wrapper
- serialized runs per session
- channel adapters attached to one gateway boundary
- desktop app present as a local product shell

That keeps KiraClaw close to OpenClaw conceptually while still preserving the desktop product expectation from KIRA-Slack.

## What We Keep From KRIM

- single-agent loop
- small module boundaries
- model abstraction
- tool abstraction
- event-handler based output

Keep:

- `krim_sdk.Agent`
- model backends
- tool registry from `krim-sdk`

Do not import:

- KRIM CLI UX
- slash command handling
- terminal banners
- worktree orchestration

## What We Keep From KIRA-Slack

- desktop product mindset
- local daemon plus desktop shell split
- auto-update bridge constraints
- local config and data migration concerns
- Slack as the first real user channel
- desktop packaging as part of the product itself

Keep the migration constraints outside the new engine:

- existing KIRA-Slack auto-update flow
- existing app identity during bridge releases
- existing user data reading ability

## Initial Layers

### Layer 1: Engine

Dependency: `krim-sdk`

Responsibility:

- run prompts
- execute tools
- stream model output
- return final response

### Layer 2: Agent Daemon

Folder: `apps/agentd`

Responsibility:

- own product config
- create long-running agent sessions
- expose HTTP API
- become the stable boundary for Slack and desktop

This is effectively the KiraClaw gateway.

### Layer 3: Desktop

Folder: `apps/desktop`

Responsibility:

- installation UX
- config UX
- logs
- updater integration later
- future direct chat UI

It starts as control plane plus product shell.
It can become a direct conversation surface later without changing the daemon architecture.

### Layer 4: Slack Adapter

Responsibility:

- receive user requests
- create or resume agent jobs
- publish progress and final answers

Slack is the first supported channel.

### Layer 5: Desktop Direct Chat

Responsibility:

- provide a local direct-chat surface
- reuse the same daemon session API as Slack
- avoid creating a second agent architecture

This is explicitly secondary to Slack in the first phase.

## Resource Policy

KiraClaw should favor completion over artificial throttling.

That means:

- use a single strong agent loop for real work
- allow long-running sessions with generous turn and timeout limits
- avoid a large classifier pipeline before the main agent
- avoid splitting simple and complex tasks into many agents unless data proves it is needed

This is intentionally different from KIRA-Slack's multi-agent orchestration.
It is intentionally closer to an OpenClaw-style embedded loop than to a many-agent classifier graph.

## Long-Running Task Policy

The default assumption is that KiraClaw should be able to stay on a task for a long time.

Initial implications:

- generous `max_turns`
- generous command timeout
- stable workspace per run
- future support for supervised loop jobs on top of `krim-sdk.Agent`
- per-session serialized execution

## Watch Layer

KIRA-Slack proved that recurring observation and proactive work matter.
KiraClaw keeps that value, but in a simpler `watch` shape:

1. a watch has time, condition, and action
2. scheduler decides when the watch runs
3. the same KRIM-based agent loop evaluates the watch
4. the watch can no-op, write memory, send a message, or perform tool-driven work

This avoids rebuilding a separate checker/proactive graph before the product boundary is stable.

## What We Are Not Building Yet

- Jira/Confluence/Outlook producers inside the daemon
- a large scheduler graph
- confirm DB workflow
- memory graph
- account migration logic inside the daemon
- full desktop direct-chat UX

These come only after the small watch substrate is stable.

## Initial API Contract

The daemon starts with a very small API:

- `GET /health`
- `GET /v1/runtime`
- `GET /v1/watches`
- `GET /v1/watch-runs`
- `POST /v1/watches`
- `POST /v1/watches/{watch_id}/run`
- `POST /v1/runs`

That is enough to validate:

- config loading
- engine creation
- session execution
- future desktop-to-daemon communication

## Migration Strategy

KiraClaw should not replace KIRA-Slack packaging on day one.

Instead:

1. build KiraClaw as the new architecture
2. keep KIRA-Slack as the shipping shell for bridge releases
3. move users gradually through compatible updates

See `docs/migration-from-kira-slack.md`.
