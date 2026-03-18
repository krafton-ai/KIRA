---
layout: home
title: KiraClaw
description: KiraClaw는 로컬에서 동작하는 agentic desktop runtime입니다. 대화, Slack/Telegram/Discord 채널, skills, schedules, run logs를 하나의 앱에서 다룹니다.

hero:
  name: KiraClaw
  text: Agentic Desktop Runtime
  tagline: 로컬 대화, Slack/Telegram/Discord 채널, workspace skills, schedules, run logs를 하나의 데스크톱 앱으로.
  image:
    src: /images/screenshots/hero-kira-claw.png
    alt: KiraClaw
  actions:
    - theme: brand
      text: macOS 다운로드
      link: https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-arm64.dmg
    - theme: alt
      text: Windows 다운로드
      link: https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-x64.exe
    - theme: alt
      text: GitHub
      link: https://github.com/krafton-ai/KIRA/tree/main/KiraClaw

features:
  - icon: 🧠
    title: 에이전틱 런타임
    details: 로컬 엔진이 먼저 생각하고, 필요할 때 도구를 쓰고, `speak`를 통해 바깥으로 말합니다.

  - icon: 💬
    title: 하나의 코어
    details: Talk, Slack, Telegram, Discord, schedules, memory, skills가 같은 로컬 daemon 위에서 동작합니다.

  - icon: 🗂️
    title: 워크스페이스 중심
    details: skills는 workspace에 있고, run logs와 memory도 로컬 파일시스템 기준으로 관리됩니다.

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

## 데모

| Search + PPTX | GitRepo + PDF | Web + Wiki |
|:---:|:---:|:---:|
| <video src="https://github.com/user-attachments/assets/284f9d0d-056c-42e9-8f1f-19873431ddba" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/721bc704-8b1a-4673-829a-52309ae69601" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/7329039a-fdad-4f4b-8f03-65402e4d6f6c" width="240" controls></video> |

| Proactive + Thread | Email + Schedule | Proactive + Translate |
|:---:|:---:|:---:|
| <video src="https://github.com/user-attachments/assets/9ee1a520-507c-408a-a1d2-4a7a393385eb" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/79959017-67c2-4109-98bd-8c1dbba2b34f" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/c78768be-580e-42e8-a3d8-34eb5f0db6cb" width="240" controls></video> |

## 다운로드

- macOS (Apple Silicon): [KiraClaw for macOS 다운로드](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-arm64.dmg)
- Windows: [KiraClaw for Windows 다운로드](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-x64.exe)

macOS에서 첫 실행 경고가 뜨면 [문제 해결](/ko/troubleshooting)을 보면 됩니다.

## 다음 단계

[시작하기](/ko/getting-started)에서 설치, 첫 실행, workspace 설정, 채널 설정까지 바로 진행할 수 있습니다.
