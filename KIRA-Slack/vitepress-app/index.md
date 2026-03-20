---
layout: home
title: KiraClaw
description: Install KiraClaw, a local desktop AI Coworker runtime with a lightweight core engine, channel adapters, memory, skills, schedules, and run logs.

hero:
  name: KiraClaw
  text: Lightweight Local AI Coworker
  tagline: A local desktop AI Coworker built on a lightweight core engine with channel adapters, workspace skills, schedules, and run logs.
  image:
    src: /images/screenshots/hero-kira-claw-new.png
    alt: KiraClaw
  actions:
    - theme: brand
      text: Download for macOS
      link: https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.2.6-arm64.dmg
    - theme: alt
      text: Download for Windows
      link: https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.2.6-x64.exe
    - theme: alt
      text: GitHub
      link: https://github.com/krafton-ai/KIRA/tree/main/KiraClaw

features:
  - icon: 🧠
    title: Lightweight Core Engine
    details: KiraClaw starts from a small local core engine and builds the desktop runtime around it instead of hiding behavior behind a large orchestration layer.

  - icon: 🗣️
    title: Explicit Speech
    details: The runtime can think, use tools, stay silent, or speak outward through `speak` instead of forcing every run into a user-facing reply.

  - icon: 💬
    title: Channels as Adapters
    details: Talk, Slack, Telegram, and Discord all sit on the same local runtime, so the product behaves like one agent with multiple ears and mouths.

  - icon: 🗂️
    title: Workspace-First
    details: Skills live in your workspace, logs stay local, and memory remains file-backed and indexable under your filesystem base directory.

  - icon: 🤖
    title: API Key And Start
    details: Add your Claude or OpenAI API key in the desktop app and start immediately. Other provider paths can be configured later.

  - icon: 📅
    title: Schedules
    details: Time-based runs can think, act, speak, save memory, or finish silently when there is nothing useful to say.

  - icon: 🔍
    title: Run Logs
    details: Inspect prompt, internal summary, spoken reply, and tool usage directly in the desktop app.

  - icon: 🔒
    title: Local by Default
    details: Settings, logs, and memory stay on your machine. KiraClaw is built as a local desktop control plane, not a hosted SaaS.
---

## Core idea

KiraClaw starts from a lightweight local core engine and adds only the surfaces that make an AI Coworker useful in practice:

- a desktop harness for setup, visibility, and local control
- channels as adapters instead of separate bot stacks
- explicit outward speech through `speak`
- local memory, skills, schedules, and logs that stay inspectable

The result is intentionally simple. It is not trying to be a huge control plane, but it still keeps strong agent concepts visible.

KiraClaw is also a fresh start inspired in part by [OpenClaw](https://github.com/openclaw/openclaw): keep the core lightweight, keep the runtime local, and keep the product understandable.

## What changed?

`KIRA-Slack` is now treated as the legacy line. New desktop runtime work moves to `KiraClaw`.

That means:

- direct manual installs should use `KiraClaw`
- old `KIRA-Slack` installs should migrate forward
- docs now describe the current runtime instead of the old Slack-first product

## What you get

KiraClaw currently includes:

- `Talk` for direct local runs
- Slack, Telegram, and Discord channel adapters
- workspace `skills/`
- local memory with index tools
- schedules for automation
- run logs in the desktop UI

## Download

- macOS (Apple Silicon): [Download KiraClaw for macOS](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.2.6-arm64.dmg)
- Windows: [Download KiraClaw for Windows](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.2.6-x64.exe)

If macOS warns about the app on first launch, use the steps in [Troubleshooting](/troubleshooting).

## Next step

Go to [Getting Started](/getting-started) for install, first launch, workspace setup, and channel setup.
