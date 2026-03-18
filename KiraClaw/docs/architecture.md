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
4. Slack arrives first, Telegram follows, and Discord shares the same adapter pattern.
5. Desktop direct chat lives on the same daemon boundary.
6. Memory and schedules stay explicit modules instead of becoming hidden product magic.

## OpenClaw Alignment

The target shape is:

- one long-running gateway per host
- embedded agent engine, not a CLI subprocess wrapper
- serialized runs per session
- channel adapters attached to one gateway boundary
- desktop app present as a local product shell

That keeps KiraClaw close to OpenClaw conceptually while still preserving the desktop product expectation from KIRA-Slack.

## Agentic Execution Model

KiraClaw now treats the core engine as a thinking system, not as a direct reply printer.

- adapters are external ears and mouth
- the core agent thinks and chooses tools
- `speak` is the explicit act of talking back to the outside world
- `internal_summary` is the internal run summary kept for history and diagnostics
- the current API still exposes the same value as `final_response` for compatibility
- shared-room inputs are treated as room transcripts, not as guaranteed direct requests

This matters because group chat and automations should be allowed to run without always producing a visible reply.

## What We Keep From KRIM

- single-agent loop
- small module boundaries
- model abstraction
- tool abstraction
- event-handler based output
- progressive skill loading

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
- produce an internal run summary
- produce outward speech only when `speak` is used

### Layer 2: Agent Daemon

Folder: `apps/agentd`

Responsibility:

- own product config
- create long-running agent sessions
- expose HTTP API
- become the stable boundary for Slack and desktop

This is effectively the KiraClaw gateway.

The daemon also owns run-level observability:

- persistent run logs under `Filesystem Base Dir/logs/runs.jsonl`
- recent run log retrieval through `GET /v1/run-logs`
- separate visibility for prompt, internal summary, spoken reply, tool events, and silent runs

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
- build room transcripts for shared spaces
- publish only spoken outward replies when appropriate

Slack is the first supported channel.

### Layer 5: Telegram Adapter

Responsibility:

- receive Telegram DM and group messages
- reuse the same session and engine boundary as Slack
- support the same `speak` and file-return model

Telegram is intentionally lightweight and shares the same agent core.

### Layer 6: Discord Adapter

Responsibility:

- receive Discord DM and server-channel messages
- reuse the same room-transcript model as other shared-space channels
- support the same `speak` and file-return model

Discord is intentionally implemented as another thin adapter on the same daemon boundary.

### Layer 7: Desktop Direct Chat

Responsibility:

- provide a local direct-chat surface
- reuse the same daemon session API as Slack
- expose both internal summaries and spoken replies for debugging and QA

This is explicitly secondary to Slack in the first phase.

### Layer 8: Memory

Responsibility:

- implicit retrieval and save for normal chat flows
- explicit memory tools for agent-directed memory work
- structured memory index management

Memory is split between deterministic index management and agent-directed file work so the agent can stay flexible without corrupting the substrate.
The intended explicit flow is:

- `memory_index_search`
- read or edit the actual memory files
- `memory_index_save`

### Layer 9: Scheduler

Responsibility:

- act as the current automation runner
- trigger agent runs on time
- optionally deliver outward results through channel delivery when the run actually uses `speak`

KiraClaw currently uses schedules rather than a separate watch subsystem.

## Resource Policy

KiraClaw should favor completion over artificial throttling.

That means:

- use a single strong agent loop for real work
- allow long-running sessions with generous turn and timeout limits
- avoid a large classifier pipeline before the main agent
- avoid splitting simple and complex tasks into many agents unless data proves it is needed

This is intentionally different from KIRA-Slack's multi-agent orchestration.
It is intentionally closer to an OpenClaw-style embedded loop than to a many-agent classifier graph.

It also means KiraClaw avoids a mandatory classifier or bot-call detector in front of every shared-room message.
The current design prefers agent judgment plus `speak` over a large pre-routing layer.

## Long-Running Task Policy

The default assumption is that KiraClaw should be able to stay on a task for a long time.

Initial implications:

- generous `max_turns`
- generous command timeout
- stable workspace per run
- future support for supervised loop jobs on top of `krim-sdk.Agent`
- per-session serialized execution

## What We Are Not Building Yet

- Jira/Confluence/Outlook producers inside the daemon
- a large scheduler graph
- confirm DB workflow
- memory graph
- account migration logic inside the daemon
- multi-agent routing nodes
- a separate background watcher runtime

## Initial API Contract

The daemon starts with a very small API:

- `GET /health`
- `GET /v1/runtime`
- `GET /v1/run-logs`
- `GET /v1/schedules`
- `GET /v1/skills`
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
