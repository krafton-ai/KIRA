# 설정 가이드

KIRA의 기본 설정([Slack 연동](/ko/getting-started#%E2%9A%99%EF%B8%8F-3%EB%8B%A8%EA%B3%84-kira-%EC%95%B1-%EC%84%A4%EC%A0%95))을 완료하셨다면, 이제 추가 기능을 활성화할 수 있습니다.

::: tip 기본 설정 먼저!
아직 기본 설정을 하지 않으셨다면 [시작하기 가이드](/ko/getting-started)를 먼저 참고하세요.
:::

## 📋 설정 구조

### 1. MCP 설정
필요에 따라 활성화할 수 있는 MCP(Model Context Protocol) 서버들입니다.

- [Perplexity 웹 검색](/ko/setup/perplexity) - 실시간 웹 정보 검색
- [DeepL (문서 번역)](/ko/setup/deepl) - 문서 번역
- [GitHub](/ko/setup/github) - GitHub 저장소 연동
- [GitLab](/ko/setup/gitlab) - GitLab 저장소 연동
- [Microsoft 365 (Outlook/OneDrive/SharePoint)](/ko/setup/ms365) - 이메일 및 파일 자동 관리
- [Confluence & Jira](/ko/setup/atlassian) - 문서 및 이슈 추적
- [Tableau](/ko/setup/tableau) - BI 대시보드 연동
- [X (Twitter)](/ko/setup/x) - 소셜 미디어 연동
- [Clova Speech (회의록)](/ko/setup/voice) - 음성 녹음 및 회의록 작성

### 2. 고급 설정
고급 사용자를 위한 설정입니다.

- [Computer Use](/ko/setup/computer-use) - 웹 브라우저 자동화
- [웹 인터페이스 (음성 입력)](/ko/setup/web-interface) - 웹 기반 인터페이스 및 음성 입력

---

## ⚙️ 설정 관리

### 설정 파일 위치
모든 설정은 다음 위치에 저장됩니다:
```
~/.kira/config.env
```

### 설정 변경하기
1. KIRA 앱 실행
2. 상단 **"환경변수 설정"** 탭 클릭
3. 원하는 항목 수정
4. **"설정 저장"** 버튼 클릭
5. **"서버 재시작"** 버튼 클릭 (변경사항 적용)

### 설정 백업
설정 파일을 백업해두면 재설치 시 유용합니다:

```bash
cp ~/.kira/config.env ~/Desktop/kira-config-backup.env
```

---

## 🎯 추천 설정 조합

업무 유형에 따른 추천 설정입니다.

### 💼 비즈니스 사용자
```
✓ Slack 연동
✓ Perplexity 웹 검색
✓ DeepL 번역
✓ Outlook 이메일
```

### 📊 프로젝트 관리자
```
✓ Slack 연동
✓ Confluence & Jira
✓ Outlook 이메일
✓ 선제적 제안 기능
```

### 💻 개발자
```
✓ Slack 연동
✓ GitHub / GitLab
✓ Confluence & Jira
✓ Perplexity 웹 검색
```

### 📱 소셜 미디어 매니저
```
✓ Slack 연동
✓ X (Twitter)
✓ Perplexity 웹 검색
✓ DeepL 번역
```

---

## 🔒 보안 및 개인정보

### 데이터 저장 위치

KIRA의 모든 데이터는 로컬 컴퓨터에 저장됩니다.

**앱 설정:**
```
~/.kira/
├── config.env          # 환경변수 설정 파일
└── server.log          # 서버 로그 파일
```

**데이터 및 메모리:**

메모리와 데이터베이스는 `FILESYSTEM_BASE_DIR` 환경변수로 설정한 위치에 저장됩니다.

- **기본값**: `~/Documents/KIRA/`
- **커스텀**: 환경변수 설정에서 변경 가능

```
{FILESYSTEM_BASE_DIR}/
├── db/                # 데이터베이스 파일들
│   ├── waiting_answer.db  # 답변 대기 DB
│   ├── confirm.db         # 승인 대기 DB
│   ├── email_tasks.db     # 이메일 작업 DB
│   └── jira_tasks.db      # Jira 작업 DB
└── memories/          # 메모리 (대화 기록)
    ├── channels/      # 채널별 대화
    ├── projects/      # 프로젝트 정보
    ├── users/         # 사용자 정보
    ├── decisions/     # 결정사항
    └── index.md       # 자동 생성 인덱스
```

::: tip 데이터 저장 위치 변경
KIRA 앱 > 환경변수 설정 > `FILESYSTEM_BASE_DIR` 항목에서 원하는 경로를 입력하세요.
예: `/Users/yourname/Dropbox/KIRA` (Dropbox와 동기화)
:::

### 인증 정보 보호
- 모든 API 키와 토큰은 `config.env`에 암호화되지 않은 상태로 저장됩니다
- 파일 권한은 현재 사용자만 읽을 수 있도록 설정됩니다
- 설정 파일을 절대 공유하지 마세요

### 외부 통신
KIRA는 다음 서비스와만 통신합니다:
- Anthropic API (Claude)
- 활성화한 MCP 서버 (Slack, Outlook, Perplexity 등)

---

## ❓ 다음 단계

1. 필요한 [MCP 설정](#1-mcp-설정) 활성화
2. [고급 설정](#2-고급-설정)이 필요하면 활성화
3. [대화하기](/ko/features/chat) 가이드로 사용법 익히기

문제가 발생하면 [문제해결](/ko/troubleshooting) 페이지를 참고하세요.
