---
layout: home
title: KiraClaw
description: Install KiraClaw, the local agentic desktop runtime for chat, Slack, Telegram, Discord, skills, schedules, and run logs.

hero:
  name: KiraClaw
  text: Agentic Desktop Runtime
  tagline: Local chat, Slack, Telegram, and Discord channels, workspace skills, schedules, and run logs in one desktop app.
  image:
    src: /images/screenshots/hero-kira-claw.png
    alt: KiraClaw
  actions:
    - theme: brand
      text: Download for macOS
      link: https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-arm64.dmg
    - theme: alt
      text: Download for Windows
      link: https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-x64.exe
    - theme: alt
      text: GitHub
      link: https://github.com/krafton-ai/KIRA/tree/main/KiraClaw

features:
  - icon: 🧠
    title: Agentic Runtime
    details: The local engine thinks first, uses tools explicitly, and speaks outward through `speak` instead of treating every run as a forced reply.

  - icon: 💬
    title: Shared Core Across Surfaces
    details: Talk, Slack, Telegram, Discord, schedules, memory, and skills all run on the same local daemon.

  - icon: 🗂️
    title: Workspace-First
    details: Skills live in your workspace, run logs stay local, and memory stays under your filesystem base directory.

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

## Demo

| Search + PPTX | GitRepo + PDF | Web + Wiki |
|:---:|:---:|:---:|
| <video src="https://github.com/user-attachments/assets/284f9d0d-056c-42e9-8f1f-19873431ddba" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/721bc704-8b1a-4673-829a-52309ae69601" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/7329039a-fdad-4f4b-8f03-65402e4d6f6c" width="240" controls></video> |

| Proactive + Thread | Email + Schedule | Proactive + Translate |
|:---:|:---:|:---:|
| <video src="https://github.com/user-attachments/assets/9ee1a520-507c-408a-a1d2-4a7a393385eb" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/79959017-67c2-4109-98bd-8c1dbba2b34f" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/c78768be-580e-42e8-a3d8-34eb5f0db6cb" width="240" controls></video> |

## Download

- macOS (Apple Silicon): [Download KiraClaw for macOS](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-arm64.dmg)
- Windows: [Download KiraClaw for Windows](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-x64.exe)

If macOS warns about the app on first launch, use the steps in [Troubleshooting](/troubleshooting).

## Next step

Go to [Getting Started](/getting-started) for install, first launch, workspace setup, and channel setup.
