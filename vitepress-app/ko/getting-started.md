---
title: KIRA 시작하기 | 설치 가이드
description: KIRA AI 가상 직원을 설치하고 설정하는 단계별 가이드입니다. Slack 연동, 토큰 설정, AI 비서와의 첫 대화까지 15분 안에 완료하세요.
head:
  - - meta
    - name: keywords
      content: KIRA 설치, 슬랙 봇 설정, AI 비서 가이드, KIRA 튜토리얼, AI 가상 직원 설정, 크래프톤 AI
  - - meta
    - property: og:title
      content: KIRA 시작하기 | 설치 가이드
  - - meta
    - property: og:description
      content: 15분 안에 KIRA를 설치하세요. Slack 앱 설정, 토큰 구성, 첫 대화 시작까지 완벽 가이드.
  - - meta
    - property: og:url
      content: https://kira.krafton-ai.com/ko/getting-started
  - - meta
    - property: og:locale
      content: ko_KR
---

# 시작하기

KIRA를 시작하는 것은 정말 간단합니다. 이 가이드를 따라하면 15분 안에 나만의 AI 가상 직원과 대화를 시작할 수 있습니다.

## 🎯 모드 선택

KIRA는 두 가지 모드로 사용할 수 있습니다. **먼저 원하는 모드를 선택하세요.**

<img src="/images/screenshots/mode-comparison.png" alt="봇 모드 vs 가상직원 모드" style="max-width: 550px; width: 100%;" />

::: info 모드별 비교
| 구분 | 봇 모드 | 가상직원 모드 |
|------|---------|---------------|
| **설치 위치** | 내 컴퓨터 | 전용 컴퓨터/VM/서버 |
| **Slack 계정** | 내 계정 또는 봇 앱 | 가상직원 전용 계정 |
| **토큰** | Bot Token (`xoxb-...`) | User Token (`xoxp-...`) |
| **표시** | 봇 아이콘으로 표시 | 실제 사용자처럼 표시 |
| **운영 시간** | 컴퓨터 켜져 있을 때 | 24/7 (항시 가동) |
| **운영 주체** | 나 | 독립적 운영 |
| **설정 난이도** | 쉬움 | 약간 복잡 |
:::

> 💡 **KRAFTON 사용 사례**: KRAFTON은 사내 계정과 컴퓨터를 지급하여 KIRA를 가상직원으로 운영하고 있습니다. 마치 신입 직원을 온보딩하는 것처럼요.

### 🤖 봇 모드

**내 컴퓨터에서 개인 AI 비서로 사용하는 방식입니다.**

- **내 컴퓨터**에 KIRA 앱 설치
- **내 Slack 계정** 또는 봇 앱으로 동작
- 내가 직접 관리하고 운영
- 내 컴퓨터가 꺼지면 KIRA도 중지됨

**적합한 경우:**
- 개인 업무 보조가 필요할 때
- AI 비서를 혼자 사용할 때
- 간단하게 시작하고 싶을 때

### 👤 가상직원 모드

**전용 컴퓨터에서 팀 공용 AI 직원으로 운영하는 방식입니다.**

- **가상직원 전용 컴퓨터**(또는 VM/서버)에 KIRA 설치
- **가상직원 전용 Slack 계정** 생성 (예: "김키라", "KIRA Kim")
- 24시간 독립적으로 운영
- 실제 팀원처럼 채널에 참여하고 업무 수행

**적합한 경우:**
- 팀 전체가 공유하는 AI 직원이 필요할 때
- 24/7 항시 가동이 필요할 때
- 실제 팀원처럼 운영하고 싶을 때

::: warning 모드 선택 후 진행
이 가이드는 선택한 모드에 따라 설정 방법이 다릅니다. 각 단계에서 **봇 모드** 또는 **가상직원 모드**에 맞는 설정을 따라주세요.
:::

---

## 📋 사전 준비사항

시작하기 전에 다음이 필요합니다:

### 1. Slack 워크스페이스
- 개인 워크스페이스 또는 관리자 권한이 있는 워크스페이스
- 무료 플랜으로도 충분합니다

### 2. Node.js
- Node.js 18 이상 설치
- Claude Code CLI 설치에 필요합니다
- [Node.js 다운로드](https://nodejs.org/)

### 3. 컴퓨터 사양
- **macOS**: 10.15 (Catalina) 이상
- 디스크 여유 공간: 500MB 이상

### 4. Claude Pro 플랜
- KIRA는 내부적으로 Claude Code를 사용하며, **Claude Pro 플랜 이상**이 필요합니다
- [Claude 플랜 자세히 보기](https://www.anthropic.com/pricing)

---

## 🛠️ 1단계: 필수 도구 설치

KIRA 앱을 실행하기 전에 필요한 도구들을 설치합니다.

### 1. Claude Code CLI 설치

터미널에서 다음 명령어를 실행하세요:

```bash
npm install -g @anthropic-ai/claude-code
```

::: danger sudo 사용 금지!
**절대 `sudo npm install -g`를 사용하지 마세요**. sudo를 사용하면 npm 캐시 권한 문제가 발생하여 나중에 MCP 서버 연결이 실패합니다.

권한 오류가 발생하면 먼저 권한을 수정하세요:
```bash
sudo chown -R $(whoami) /usr/local/lib/node_modules
sudo chown -R $(whoami) /usr/local/bin
```
그 다음 sudo 없이 `npm install -g`를 실행하세요.

이미 sudo로 설치했다면 [문제 해결 - MCP 서버 연결 문제](/ko/troubleshooting#mcp-서버가-failed-상태로-표시돼요)를 참조하세요.
:::

설치 확인:
```bash
claude --version
```

### 2. mcp-cache 설치

MCP 서버 최적화를 위해 mcp-cache를 설치하세요:

```bash
npm install -g @hapus/mcp-cache
```

::: tip mcp-cache란?
mcp-cache는 MCP 서버의 시작 시간과 캐시 크기를 줄여줍니다. GitLab, MS365, Atlassian, Tableau, Computer Use (Playwright) 기능에 필요합니다.
:::

### 3. Claude 로그인

**중요**: Claude Code CLI 설치 후 반드시 로그인해야 합니다:

```bash
claude
```

`claude` 명령어를 실행하면:
1. 브라우저 창이 자동으로 열립니다
2. Anthropic 계정으로 로그인합니다 (계정이 없으면 생성)
3. 인증 완료 후 터미널에 확인 메시지가 표시됩니다
4. 터미널을 종료해도 로그인 상태는 유지됩니다

::: warning 최초 설정 필수
KIRA는 내부적으로 Claude Agent SDK를 사용하므로, KIRA를 시작하기 전에 이 로그인 단계를 반드시 완료해야 합니다. 이 단계를 건너뛰면 KIRA가 Claude AI를 사용할 수 없습니다.
:::

::: tip Claude Code CLI란?
KIRA의 AI 엔진인 Claude Agent SDK가 내부적으로 사용하는 CLI 도구입니다.
:::

### 4. uv (Python 패키지 관리자) - 자동 설치

::: tip 자동 설치
uv는 KIRA를 처음 시작할 때 **자동으로 설치**됩니다. uv가 감지되지 않으면 자동 설치 여부를 묻는 다이얼로그가 나타납니다.
:::

자동 설치가 실패한 경우 수동으로 설치할 수 있습니다:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 확인:
```bash
uv --version
```

::: info uv란?
uv는 빠른 Python 패키지 관리자입니다. KIRA가 필요한 Python 라이브러리를 자동으로 설치하고 관리합니다.
:::

---

## 📥 2단계: KIRA 다운로드 및 설치

1. [KIRA for macOS (Apple Silicon)](https://kira.krafton-ai.com/download/KIRA-0.1.7-arm64.dmg) 다운로드
2. DMG 파일을 열고 KIRA.app을 Applications 폴더로 드래그
3. Applications 폴더에서 KIRA 실행

---

## 🔧 3단계: Slack App 생성

KIRA가 Slack과 통신하려면 Slack App이 필요합니다.

### 1. Slack App 만들기
1. [Slack API 페이지](https://api.slack.com/apps) 접속
2. **"Create New App"** 클릭
3. **"From scratch"** 선택
4. App 이름 입력 (예: "KIRA Bot")
5. 워크스페이스 선택

### 2. Socket Mode 활성화
1. 왼쪽 메뉴에서 **"Socket Mode"** 클릭
2. **"Enable Socket Mode"** 토글 켜기
3. App-Level Token 이름 입력 (예: "kira-socket")
4. **`connections:write`** scope 선택
5. **Generate** 클릭
6. 생성된 토큰 복사 (나중에 사용) → `xapp-...`

### 3. Event Subscriptions 설정
1. **"Event Subscriptions"** 클릭
2. **"Enable Events"** 토글 켜기
3. 선택한 모드에 따라 이벤트 추가:

::: code-group
```txt [🤖 봇 모드]
"Subscribe to bot events" 섹션에서 추가:
- app_mention (앱 멘션 메시지)
- file_shared (파일 공유 알림)
- link_shared (링크 공유 알림)
- message.channels (공개 채널 메시지)
- message.groups (비공개 채널 메시지)
- message.im (DM 메시지)
- message.mpim (그룹 DM 메시지)
```

```txt [👤 가상직원 모드]
"Subscribe to events on behalf of users" 섹션에서 추가:
- file_shared (파일 공유 알림)
- link_shared (링크 공유 알림)
- message.channels (공개 채널 메시지)
- message.groups (비공개 채널 메시지)
- message.im (DM 메시지)
- message.mpim (그룹 DM 메시지)

※ app_mention은 User Token에서 지원되지 않습니다
```
:::

4. **"Save Changes"** 클릭

::: tip 이벤트 개수
- 봇 모드: 7개
- 가상직원 모드: 6개
검색창에 이벤트 이름을 입력하여 추가하세요.
:::

### 4. App Home 설정
1. 왼쪽 메뉴에서 **"App Home"** 클릭
2. **"Show Tabs"** 섹션에서:
   - **"Messages Tab"** 체크 확인
   - ✅ **"Allow users to send Slash commands and messages from the messages tab"** 반드시 체크
3. **"Save Changes"** 클릭

::: warning 중요
"Allow users to send Slash commands and messages from the messages tab" 옵션을 체크하지 않으면 사용자가 봇에게 DM을 보낼 수 없습니다!
:::

### 5. Token Scopes 설정
1. **"OAuth & Permissions"** 클릭
2. 선택한 모드에 따라 권한 추가:

::: code-group
```txt [🤖 봇 모드]
"Bot Token Scopes" 섹션에서 추가 (총 21개):

[메시지 관련]
- app_mentions:read (@멘션 메시지 읽기)
- channels:history (공개 채널 메시지 읽기)
- groups:history (비공개 채널 메시지 읽기)
- im:history (DM 메시지 읽기)
- mpim:history (그룹 DM 메시지 읽기)
- chat:write (메시지 전송)

[채널 정보]
- channels:read (공개 채널 정보 보기)
- groups:read (비공개 채널 정보 보기)
- im:read (DM 정보 보기)
- mpim:read (그룹 DM 정보 보기)

[DM 시작]
- im:write (DM 시작하기)
- mpim:write (그룹 DM 시작하기)

[파일 및 기타]
- files:read (파일 읽기)
- files:write (파일 업로드/편집)
- links:read (메시지의 URL 보기)
- reactions:write (이모지 리액션 추가)

[사용자 정보]
- users:read (워크스페이스 사용자 정보 보기)
- users:read.email (사용자 이메일 주소 보기)
- users.profile:read (사용자 프로필 상세정보 보기)
- users:write (봇 상태 설정)
```

```txt [👤 가상직원 모드]
"User Token Scopes" 섹션에서 추가 (총 21개):

[메시지 관련]
- channels:history (공개 채널 메시지 읽기)
- groups:history (비공개 채널 메시지 읽기)
- im:history (DM 메시지 읽기)
- mpim:history (그룹 DM 메시지 읽기)
- chat:write (메시지 전송)

[채널 정보]
- channels:read (공개 채널 정보 보기)
- groups:read (비공개 채널 정보 보기)
- im:read (DM 정보 보기)
- mpim:read (그룹 DM 정보 보기)

[DM 시작]
- im:write (DM 시작하기)
- mpim:write (그룹 DM 시작하기)

[파일 및 기타]
- files:read (파일 읽기)
- files:write (파일 업로드/편집)
- links:read (메시지의 URL 보기)
- reactions:write (이모지 리액션 추가)

[사용자 정보]
- users:read (워크스페이스 사용자 정보 보기)
- users:read.email (사용자 이메일 주소 보기)
- users.profile:read (사용자 프로필 상세정보 보기)
- users.profile:write (사용자 프로필 업데이트)
- users:write (사용자 상태 설정)

※ app_mentions:read는 User Token에서 지원되지 않습니다
```
:::

::: tip 권한 추가 방법
검색창에 권한 이름을 입력하고 **"Add"** 버튼을 클릭하세요.
- 봇 모드: 21개 권한
- 가상직원 모드: 21개 권한
:::

### 6. 워크스페이스에 설치
1. 페이지 상단 **"Install to Workspace"** 클릭
2. 권한 허용
3. 선택한 모드에 따라 토큰 복사:

::: code-group
```txt [🤖 봇 모드]
"Bot User OAuth Token" 복사 → xoxb-...
```

```txt [👤 가상직원 모드]
"User OAuth Token" 복사 → xoxp-...
```
:::

### 7. Signing Secret 확인
1. **"Basic Information"** 클릭
2. **"App Credentials"** 섹션에서 **Signing Secret** 확인
3. **"Show"** 클릭 후 복사

---

## ⚙️ 4단계: KIRA 앱 설정

### 1. KIRA 앱 실행
처음 실행하면 설정 화면이 나타납니다.

![KIRA 설정 화면](/images/screenshots/kira-settings-main.png)

### 2. 필수 설정 입력

이제 Slack App에서 복사한 토큰들을 KIRA 앱에 입력합니다.

#### Slack 연동
- **SLACK_BOT_TOKEN**: 앞서 복사한 토큰
  - 봇 모드: `xoxb-...` (Bot User OAuth Token)
  - 가상직원 모드: `xoxp-...` (User OAuth Token)
- **SLACK_APP_TOKEN**: 앞서 복사한 `xapp-...` 토큰
- **SLACK_SIGNING_SECRET**: Signing Secret
- **SLACK_TEAM_ID**: 워크스페이스 ID (선택사항)

::: tip 워크스페이스 ID 찾기
Slack 웹에서 워크스페이스 이름 클릭 > "설정 및 관리" > URL에서 확인
예: `https://app.slack.com/client/T01234ABCDE/...`에서 `T01234ABCDE` 부분
:::

#### 봇 정보

![봇 정보 설정](/images/screenshots/kira-settings-bot-info.png)

**BOT_NAME**
- **설명**: Slack에서 생성한 봇의 이름입니다.
- **용도**: KIRA가 자신을 식별하는 데 사용됩니다.
- **예시**: `KIRA Bot`, `지호봇`, `Jiho Bot`
- **찾는 방법**: Slack App 설정 > Basic Information > Display Name

**BOT_EMAIL**
- **설명**: 봇 관리자(사용자)의 이메일 주소입니다.
- **용도**: 중요한 알림이나 에러 발생 시 알림을 받을 수 있습니다.
- **예시**: `hong@company.com`
- **선택사항**: 현재는 필수이지만, 실제로는 알림 기능이 활성화되지 않았을 수 있습니다.

**AUTHORIZED_USERS**
- **설명**: KIRA를 사용할 수 있는 권한이 있는 사용자 목록입니다.
- **용도**: 지정된 사용자만 봇을 사용할 수 있도록 제한합니다.
- **형식**: 쉼표(,)로 구분하여 여러 명 입력 가능
- **예시**: `홍길동, 김철수, Sarah Kim, John Doe`
- **주의**:
  - Slack 프로필에 설정된 **실제 이름(Real Name)**을 정확히 입력해야 합니다.
  - 대소문자를 정확히 입력하세요.
  - 공백도 정확히 일치해야 합니다.

::: tip Slack 사용자 이름 확인 방법
Slack에서 본인 프로필 클릭 > "프로필 보기" > "전체 이름" 항목 확인
또는 워크스페이스 멤버 목록에서 이름 확인
:::

::: warning 권한 설정 주의
AUTHORIZED_USERS에 등록되지 않은 사용자가 봇에게 메시지를 보내면 응답하지 않습니다.
팀 전체가 사용하려면 모든 팀원의 이름을 등록하세요.
:::

### 3. 설정 저장
- 모든 필수 항목 입력 후 **"설정 저장"** 버튼 클릭
- 설정은 `~/.kira/config.env`에 안전하게 저장됩니다

---

## 🚀 5단계: KIRA 시작하기

### 1. 서버 시작
- KIRA 앱에서 **"시작하기"** 버튼 클릭
- 로그 창에 "✓ Slack connected" 메시지 확인

### 2. Slack에서 봇 초대
1. Slack 워크스페이스 열기
2. 채널 또는 DM에서 `/invite @KIRA Bot` 입력
3. 또는 채널 상세 정보 > "통합" > "앱 추가"

### 3. 첫 대화 시작
DM으로 간단하게 인사해보세요:

```
안녕 KIRA!
```

KIRA가 응답하면 성공입니다! 🎉

---

## 🧠 메모리 구축 (권장)

KIRA를 더욱 효과적으로 사용하려면 처음에 메모리를 구축하는 것이 좋습니다.

팀원 정보, 조직 구조, 프로젝트 정보, Confluence 문서 등을 미리 기억시켜두면:
- 팀원 태그 없이도 자동으로 이메일 주소 인식
- 프로젝트 맥락을 자동으로 참조
- 문서를 찾지 않고도 즉시 정보 활용

::: tip 메모리 초기화 가이드
자세한 메모리 구축 방법은 [메모리 시스템](/ko/features/memory#메모리-초기화-가이드) 페이지를 참고하세요.
:::

---

## ✅ 테스트 체크리스트

다음을 확인해보세요:

- [ ] KIRA 앱이 정상적으로 실행됨
- [ ] 로그에 에러 없이 "Slack connected" 표시됨
- [ ] Slack DM에서 KIRA와 대화 가능
- [ ] 채널에서 `@KIRA` 멘션 시 응답함
- [ ] 스레드에서도 대화 가능

---

## 🎯 다음 단계

기본 설정을 마쳤다면 다음 기능들을 추가해보세요:

- [Perplexity 웹 검색](/ko/setup/perplexity) - 실시간 정보 검색
- [MS365 이메일 모니터링](/ko/setup/ms365) - 자동 작업 추출 및 수행
- [Confluence 문서 추적](/ko/setup/atlassian) - 문서 업데이트 알림
- [음성 입력](/ko/setup/voice) - 음성으로 대화하기

---

## 🆘 문제가 발생했나요?

일반적인 문제와 해결 방법은 [문제해결](/ko/troubleshooting) 페이지를 참고하세요.

**자주 발생하는 문제:**

### "Slack connection failed"
- Bot Token과 App Token이 올바른지 확인
- Socket Mode가 활성화되어 있는지 확인
- 워크스페이스에 앱이 설치되어 있는지 확인

### "봇이 응답하지 않아요"
- 채널에 봇을 초대했는지 확인 (`/invite @봇이름`)
- DM의 경우 멘션 없이도 응답해야 합니다
- 로그에서 에러 메시지 확인

### "서버가 시작되지 않아요"
- 8000번 포트가 사용 중인지 확인
- KIRA 앱 로그 창에서 자세한 에러 확인
- 앱을 재시작해보세요

---

<div style="text-align: center; margin-top: 60px; padding: 30px; border-radius: 12px; border: 1px solid var(--vp-c-divider);">
  <h3>🎉 축하합니다!</h3>
  <p>이제 나만의 AI 가상 직원 KIRA와 함께 일할 준비가 되었습니다.</p>
  <p>다음은 <a href="/ko/features/chat">대화하기</a> 가이드를 읽어보세요.</p>
</div>
