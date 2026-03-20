---
layout: home
title: KiraClaw
description: KiraClaw는 가벼운 코어 엔진에서 시작하는 로컬 desktop AI Coworker runtime입니다. 대화, 채널, memory, skills, schedules, logs를 하나의 앱에서 다룹니다.

hero:
  name: KiraClaw
  text: Lightweight Local AI Coworker
  tagline: 가벼운 코어 엔진 위에 채널 어댑터, workspace skills, schedules, run logs를 얹은 로컬 desktop AI Coworker.
  image:
    src: /images/screenshots/hero-kira-claw-new.png
    alt: KiraClaw
  actions:
    - theme: brand
      text: macOS 다운로드
      link: https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.2.6-arm64.dmg
    - theme: alt
      text: Windows 다운로드
      link: https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.2.6-x64.exe
    - theme: alt
      text: GitHub
      link: https://github.com/krafton-ai/KIRA/tree/main/KiraClaw

features:
  - icon: 🧠
    title: 가벼운 코어 엔진
    details: KiraClaw는 작은 로컬 코어 엔진에서 시작하고, 그 위에 데스크톱 런타임을 얹는 방향으로 설계되어 있습니다.

  - icon: 🗣️
    title: 명시적인 말하기
    details: 런타임은 생각하고, 도구를 쓰고, 조용히 끝나거나, 필요할 때만 `speak`로 바깥에 말합니다.

  - icon: 💬
    title: 채널은 어댑터
    details: Talk, Slack, Telegram, Discord는 서로 다른 봇이 아니라 같은 로컬 런타임에 붙은 귀와 입처럼 동작합니다.

  - icon: 🗂️
    title: 워크스페이스 중심
    details: skills는 workspace에 있고, logs와 memory도 로컬 파일 시스템 안에 파일과 인덱스 형태로 남습니다.

  - icon: 🤖
    title: API Key로 바로 시작
    details: 데스크톱 앱에 Claude 또는 OpenAI API key를 넣으면 바로 시작할 수 있고, 다른 provider는 나중에 추가로 설정할 수 있습니다.

  - icon: 📅
    title: 스케줄 실행
    details: 시간 기반 실행은 생각하고, 필요하면 말하거나 저장하고, 아니면 조용히 끝날 수 있습니다.

  - icon: 🔍
    title: Run Logs
    details: prompt, internal summary, spoken reply, tool usage를 데스크톱 UI에서 바로 볼 수 있습니다.

  - icon: 🔒
    title: 로컬 우선
    details: 설정, 로그, 메모리는 기본적으로 내 컴퓨터에 남습니다. KiraClaw는 hosted SaaS가 아니라 로컬 제어면입니다.
---

## 기본 개념

KiraClaw는 가벼운 로컬 코어 엔진에서 시작하고, 실제로 AI Coworker를 쓰는 데 필요한 표면만 얹습니다.

- 설정과 상태를 보는 데스크톱 harness
- Talk와 채널을 같은 런타임에 연결하는 adapter 구조
- `speak` 중심의 명시적인 바깥 발화
- 로컬 memory, skills, schedules, logs

복잡한 플랫폼을 지향하기보다, 단순하지만 좋은 agent 개념들이 자연스럽게 드러나도록 만든 런타임이라고 보면 됩니다.

또한 KiraClaw는 [OpenClaw](https://github.com/openclaw/openclaw)에서 일부 영감을 받아 새롭게 시작한 프로젝트이기도 합니다. 핵심을 가볍게 유지하고, 로컬 런타임을 이해 가능하게 두려는 방향을 중요하게 봅니다.

## 무엇이 달라졌나요?

`KIRA-Slack`은 이제 legacy 라인이고, 새로운 데스크톱 런타임 작업은 `KiraClaw` 기준으로 진행됩니다.

즉:

- 수동 설치는 `KiraClaw`를 사용하고
- 기존 `KIRA-Slack`는 점진적으로 전환되며
- 문서도 예전 Slack-first 제품이 아니라 현재 런타임 기준으로 설명합니다

## 현재 포함된 것

KiraClaw에는 현재 다음이 포함됩니다.

- `Talk` 로컬 실행
- Slack / Telegram / Discord 채널
- workspace `skills/`
- local memory + index tools
- schedules 자동화
- desktop run logs

## 다운로드

- macOS (Apple Silicon): [KiraClaw for macOS 다운로드](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.2.6-arm64.dmg)
- Windows: [KiraClaw for Windows 다운로드](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.2.6-x64.exe)

macOS에서 첫 실행 경고가 뜨면 [문제 해결](/ko/troubleshooting)을 보면 됩니다.

## 다음 단계

[시작하기](/ko/getting-started)에서 설치, 첫 실행, workspace 설정, 채널 설정까지 바로 진행할 수 있습니다.
