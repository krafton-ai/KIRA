---
layout: home
title: KIRA - AI 가상 직원 | 15분 만에 나만의 AI 비서 고용하기
description: KIRA는 24시간 일하는 AI 가상 직원입니다. 데스크톱 앱만 설치하면 Slack, Outlook, Confluence, Jira와 연동되는 AI 비서를 바로 사용할 수 있습니다. 코딩 필요 없음.
head:
  - - meta
    - name: keywords
      content: AI 비서, 가상 직원, 슬랙 봇, AI 에이전트, 데스크톱 앱, 생산성, 자동화, Claude AI, 크래프톤 AI, KRAFTON AI
  - - meta
    - property: og:title
      content: KIRA - AI 가상 직원 | 24시간 일하는 AI 비서
  - - meta
    - property: og:description
      content: 데스크톱 앱만 설치하면 나만의 AI 가상 직원을 고용할 수 있습니다. Slack, Outlook, Confluence 등과 연동됩니다.
  - - meta
    - property: og:url
      content: https://kira.krafton-ai.com/ko/
  - - meta
    - property: og:locale
      content: ko_KR

hero:
  name: KIRA
  text: 나만의 AI 가상 직원
  tagline: 데스크톱 앱 하나로 시작하는 24/7 AI 에이전트
  image:
    src: /images/screenshots/hero-kira.png
    alt: KIRA
  actions:
    - theme: brand
      text: GitHub
      link: https://github.com/krafton-ai/kira
    - theme: alt
      text: macOS (Apple Silicon)
      link: https://kira.krafton-ai.com/download/KIRA-0.1.7-arm64.dmg
    - theme: alt
      text: Windows
      link: https://kira.krafton-ai.com/download/KIRA Setup 0.1.7.exe

features:
  - icon: 💬
    title: 간편한 대화
    details: Slack DM, 채널, 스레드 어디서든 자연스럽게 대화하세요. 복잡한 작업도 말로 요청하면 됩니다.

  - icon: 🧠
    title: 똑똑한 메모리
    details: KIRA는 대화 내용, 프로젝트 정보, 중요한 결정사항을 기억합니다. 매번 반복 설명할 필요 없어요.

  - icon: 📧
    title: 자동 이메일 처리
    details: Outlook 이메일을 모니터링하고 할당된 업무를 자동으로 추출해 직접 수행합니다.

  - icon: 📄
    title: 문서/이슈 추적
    details: Confluence 업데이트는 메모리에 저장하고, Jira 할당된 업무는 직접 수행합니다.

  - icon: 🎯
    title: 선제적 제안
    details: KIRA가 메모리를 분석해 필요한 작업을 미리 제안합니다. 놓치는 일이 없어요.

  - icon: 🎤
    title: 음성 입력
    details: 웹 인터페이스를 통해 음성으로도 대화할 수 있습니다. 타이핑이 불편할 때 유용해요.

  - icon: ⚙️
    title: 간단한 설정
    details: 코딩이나 서버 설정 필요 없어요. GUI로 모든 설정을 쉽게 관리할 수 있습니다.

  - icon: 🔒
    title: 로컬 우선
    details: 모든 데이터는 여러분의 컴퓨터에 저장됩니다. 개인정보 보호는 기본입니다.
---

## 💡 KIRA란?

> **KIRA** = **K**RAFTON **I**NTELLIGENCE **R**OOKIE **A**GENT

KIRA는 KRAFTON 사내에서 성공적으로 사용 중인 AI 에이전트 시스템 <strong>KRIS (KRAFTON Intelligence System)</strong>를 "가상 직원" 컨셉에 맞게 리패키징한 오픈소스 프로젝트입니다. 누구나 설치하고 바로 사용할 수 있는 데스크톱 앱으로 만들었습니다 — 서버 설정도, 클라우드도 필요 없이 설치만 하면 끝.

### 🎬 데모

<div style="display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; margin: 24px 0;">
  <div style="text-align: center; flex: 0 0 calc(33.333% - 8px); min-width: 250px;">
    <video src="https://kira.krafton-ai.com/videos/Search+PPTX_cut.mp4?v=2" width="100%" controls style="border-radius: 8px;"></video>
    <p style="margin-top: 8px; font-size: 13px; color: #666;">가상 직원에게 자료 조사 후 발표자료 만들어달라고 부탁</p>
  </div>
  <div style="text-align: center; flex: 0 0 calc(33.333% - 8px); min-width: 250px;">
    <video src="https://kira.krafton-ai.com/videos/GitRepo+PDF_cut.mp4?v=2" width="100%" controls style="border-radius: 8px;"></video>
    <p style="margin-top: 8px; font-size: 13px; color: #666;">가상 직원에게 코드 리뷰 후 PDF로 정리해달라고 부탁</p>
  </div>
  <div style="text-align: center; flex: 0 0 calc(33.333% - 8px); min-width: 250px;">
    <video src="https://kira.krafton-ai.com/videos/WebInterface+Wiki_cut.mp4?v=2" width="100%" controls style="border-radius: 8px;"></video>
    <p style="margin-top: 8px; font-size: 13px; color: #666;">가상 직원에게 음성으로 말하고 위키 업데이트 부탁</p>
  </div>
  <div style="text-align: center; flex: 0 0 calc(33.333% - 8px); min-width: 250px;">
    <video src="https://kira.krafton-ai.com/videos/Proactive+BotInThread_cut.mp4?v=2" width="100%" controls style="border-radius: 8px;"></video>
    <p style="margin-top: 8px; font-size: 13px; color: #666;">가상 직원이 과거 업무 기반으로 먼저 도움을 제안</p>
  </div>
  <div style="text-align: center; flex: 0 0 calc(33.333% - 8px); min-width: 250px;">
    <video src="https://kira.krafton-ai.com/videos/Outlook+Schedule_cut.mp4?v=2" width="100%" controls style="border-radius: 8px;"></video>
    <p style="margin-top: 8px; font-size: 13px; color: #666;">가상 직원에게 이메일로 스케줄 등록 요청</p>
  </div>
  <div style="text-align: center; flex: 0 0 calc(33.333% - 8px); min-width: 250px;">
    <video src="https://kira.krafton-ai.com/videos/Proactive+TranslateFile_cut.mp4?v=2" width="100%" controls style="border-radius: 8px;"></video>
    <p style="margin-top: 8px; font-size: 13px; color: #666;">가상 직원이 문서를 먼저 번역해줌</p>
  </div>
</div>

::: warning 베타 버전
KIRA는 현재 베타 버전입니다. 몇 가지 참고 사항:
- **응답 속도**: 가상 직원처럼 동작하기 위해 여러 에이전트가 협업하므로 응답이 약간 느릴 수 있습니다.
- **언어 지원**: 한국어와 영어를 지원하지만, 한국어에 최적화되어 있습니다.
:::

---

## 🚀 빠른 시작

KIRA를 시작하는 것은 정말 간단합니다:

1. **앱 다운로드**: macOS용 설치 파일 다운로드
2. **설치 실행**: 일반 앱처럼 설치하세요
3. **Slack 연동**: 앱을 열고 Slack 토큰만 입력하면 끝!

::: tip macOS 전용
현재 KIRA는 macOS 10.15 (Catalina) 이상에서만 지원됩니다.
:::

::: warning Claude Pro 플랜 필요
KIRA는 내부적으로 Claude Code를 사용하며, **Claude Pro 플랜 이상**이 필요합니다. [Claude 플랜 자세히 보기](https://www.anthropic.com/pricing)
:::

자세한 내용은 [시작하기 가이드](/ko/getting-started)를 참고하세요.

---

## 💡 누구를 위한 도구인가요?

KIRA는 **비개발자**를 위해 만들어졌습니다:

- **마케터**: 일일 리포트 자동화, 소셜 미디어 관리
- **세일즈**: 이메일 작업 추출, 고객 정보 관리
- **기획자**: 문서 업데이트 추적, 회의록 정리
- **창업가**: 모든 업무의 AI 비서

기술적인 지식이 전혀 없어도 괜찮습니다. 마이크로소프트 오피스 설치하듯 쉽게 시작할 수 있어요.

---

## 🎯 왜 KIRA인가요?

### 🔧 **설정이 필요 없습니다**
서버도, 클라우드 설정도, 터미널 명령어도 필요 없어요. 앱을 설치하고 GUI로 모든 설정을 마칠 수 있습니다.

### 💰 **합리적인 비용**
본인의 Claude API 키를 사용하므로 사용한 만큼만 비용이 발생합니다. 구독료나 숨은 비용이 없어요.

### 🏠 **데이터는 여러분 것**
모든 메모리와 데이터는 여러분의 컴퓨터에 저장됩니다. 외부로 유출될 걱정이 없습니다.

### 🔌 **풍부한 연동**
Slack, Outlook, Confluence, Jira, GitLab, X 등 업무에 필요한 도구들과 바로 연동됩니다.

---

<div style="text-align: center; margin-top: 60px;">
  <h2>지금 바로 시작하세요</h2>
  <p style="font-size: 18px;">15분이면 나만의 AI 가상 직원을 고용할 수 있습니다</p>
  <a href="/ko/getting-started" style="display: inline-block; margin-top: 20px; padding: 12px 32px; background: #3eaf7c; color: white; text-decoration: none; border-radius: 8px; font-weight: 600;">시작하기 →</a>
</div>
