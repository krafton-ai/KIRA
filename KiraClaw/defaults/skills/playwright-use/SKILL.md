---
name: playwright-use
description: >
  Practical browser automation guidance for KiraClaw browser MCP tasks.
  Trigger on: opening a downloaded HTML file, testing a localhost app, validating
  a web flow in the browser, interacting with a browser game, or when Playwright/browser
  actions keep timing out or failing.
---

# Playwright Use

Use this skill when the task depends on a live page and browser behavior matters.

## Core Rules

1. For remote websites, use browser tools directly.
2. For local HTML or downloaded web assets, do **not** use `file://`. Serve the directory over local HTTP and open `http://127.0.0.1` or `http://localhost` instead.
3. Before starting a new local server, check existing background process sessions and reuse one if it already serves the needed directory.
4. Reuse the current app tab when possible. Do not intentionally create extra blank tabs.

## Local HTML / Localhost Workflow

1. Identify the HTML file and its containing directory.
2. Check whether a suitable local server is already running.
3. If not, start one with a simple command such as:

```bash
cd /path/to/dir && python3 -m http.server 8765 --bind 127.0.0.1
```

4. Open the page through `http://127.0.0.1:8765/...`.
5. Once the page is no longer needed, stop the temporary server unless the user still needs it.

## Page Readiness

- After navigation, do a lightweight readiness check before acting.
- Prefer title, `document.readyState`, visible buttons, or small DOM checks over immediate screenshots.
- Use screenshots sparingly. They are for confirmation, evidence, or final reporting, not for every step.

## Interaction Strategy

Start with normal browser interactions:
- `browser_navigate`
- `browser_click`
- `browser_fill`
- `browser_wait_for`
- `browser_snapshot`

If normal interactions fail repeatedly because of overlays, viewport problems, canvas rendering, or unstable refs, switch quickly instead of repeating the same failed action.

## Canvas / WebGL / Three.js / Game Pages

For canvas-heavy or animated pages:
- do not rely on screenshots as the main control strategy
- do not keep reusing stale snapshot refs after rerenders
- prefer targeted `browser_evaluate` or `browser_run_code` against app state, exposed globals, or known UI handlers

When you switch to script-driven interaction, keep it focused:
- inspect the current app state
- call the smallest useful function or click handler
- verify the resulting state change before moving on

## Common Failure Patterns

- `file://` blocked: switch to localhost
- click timeout or pointer interception: inspect overlays, viewport, and visible state
- stale ref errors: capture a fresh snapshot or use direct state inspection
- repeated screenshot timeout: stop using screenshots as your primary probe
- browser page/context closed: reopen the target page and rebuild current state before continuing

## Decision Heuristic

- Standard website or form: browser actions first
- Local HTML demo or app: localhost first, then browser actions
- Canvas/game/non-DOM UI: browser actions if they work, otherwise targeted script interaction
