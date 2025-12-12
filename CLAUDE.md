# CLAUDE.md - Developer Guide for Claude Code

This file provides critical guidance to Claude Code (claude.ai/code) when working with the KIRA project.

## 🎯 Core Concept: "Install App = Hire AI Employee"

**CRITICAL UNDERSTANDING**: This project's revolutionary concept is that installing the desktop app instantly transforms any computer into an AI employee. No servers, no cloud setup, no technical expertise required - just like installing Microsoft Office.

### The Vision
- **End Users**: Non-technical people who need an AI assistant
- **Installation**: As simple as installing any desktop application
- **Configuration**: GUI-based, no terminal or coding required
- **Result**: A fully functional AI employee working 24/7

### Development Philosophy
When developing ANY feature, always ask:
1. Can a non-developer understand and use this?
2. Does it maintain the "zero configuration" principle?
3. Is the GUI self-explanatory?
4. Will it work immediately after installation?

---

## 📁 Project Structure

```
kira/                           # Root directory
│
├── electron-app/               # 🎯 THE CORE - Desktop app
│   ├── main.js                # Electron main process - manages Python server lifecycle
│   ├── preload.js             # Secure IPC bridge
│   ├── renderer/              # User interface
│   │   ├── index.html         # Main UI structure (환경변수 설정 UI)
│   │   ├── main.css           # Dark theme styling
│   │   └── main.js            # UI logic, server control, config management
│   ├── package.json           # Node dependencies and build config
│   └── dist/                  # Built installers (.dmg, .exe, .AppImage)
│
├── app/                       # Python AI server (runs invisibly in background)
│   ├── main.py               # Server entry point, worker/scheduler setup
│   ├── cc_agents/            # AI agent modules
│   │   ├── bot_call_detector/        # 봇 호출 판단 (Haiku)
│   │   ├── simple_chat/              # 간단한 대화 (Haiku)
│   │   ├── operator/                 # 복잡한 작업 수행 (Sonnet)
│   │   ├── memory_retriever/         # 메모리 검색 (Haiku)
│   │   ├── memory_manager/           # 메모리 저장 (Haiku)
│   │   ├── answer_aggregator/        # 답변 수집 (Haiku)
│   │   ├── proactive_suggester/      # 선제적 제안 (Sonnet)
│   │   └── proactive_confirm/        # 제안 승인 요청 (Haiku)
│   ├── cc_checkers/          # 능동 수신 채널 (Proactive monitors)
│   │   ├── outlook/          # Outlook 이메일 체커
│   │   └── atlassian/        # Confluence/Jira 체커 (Rovo MCP)
│   ├── cc_tools/             # MCP tool implementations
│   │   ├── slack/            # Slack 도구 (11개)
│   │   ├── outlook/          # Outlook 도구 (7개)
│   │   ├── scheduler/        # 메시지 스케줄링
│   │   ├── waiting_answer/   # 답변 대기 관리
│   │   ├── confirm/          # 사용자 승인 관리
│   │   ├── email_tasks/      # 이메일 작업 DB
│   │   ├── jira_tasks/       # Jira 작업 DB
│   │   └── x/                # X (Twitter) 도구
│   ├── cc_web_interface/     # 웹 서버 / 음성 수신 채널
│   │   ├── server.py         # FastAPI 서버 (port 8000, HTTPS)
│   │   ├── auth_handler.py   # 인증 라우터
│   │   ├── auth_azure.py     # MS365 OAuth
│   │   └── auth_slack.py     # Slack OAuth
│   ├── cc_slack_handlers.py  # Slack 이벤트 핸들러
│   ├── queueing_extended.py  # 3-tier 큐 시스템
│   ├── scheduler.py          # APScheduler 관리
│   └── config/               # Configuration management
│       ├── settings.py       # Pydantic settings (환경변수 정의)
│       └── env/
│           ├── dev.env       # 개발 환경변수
│           └── credential.json  # GCP service account
│
└── docs/                     # User-facing documentation
```

---

## 🚨 Critical Development Rules

### 1. Electron App is Sacred
- **NEVER** break the Electron app - it's the user's only interface
- **ALWAYS** test GUI changes on multiple screen sizes
- **ENSURE** error messages are user-friendly (no stack traces!)
- **MAINTAIN** backward compatibility with saved configs

### 2. Zero-Setup Principle
- **NO** manual file editing should ever be required
- **NO** terminal commands for end users
- **ALL** configuration through GUI
- **DEFAULT** values for everything optional

### 3. 환경변수 동기화 필수
**CRITICAL**: 환경변수를 추가/수정할 때는 반드시 **5곳을 모두 업데이트**해야 합니다:

1. **app/config/settings.py** - Pydantic 모델 정의
2. **app/config/env/dev.env** - 개발 기본값
3. **electron-app/renderer/index.html** - UI 입력 필드
4. **electron-app/renderer/main.js** - `fields` 배열 (저장/로드할 필드 목록)
5. **electron-app/main.js** - config.env 저장 섹션 (`sections` 객체)

**특히 `renderer/main.js`의 `fields` 배열을 빠뜨리기 쉬우니 주의하세요!**
이 배열에 없는 필드는 저장/로드 로직에서 무시됩니다.

순서도 일치시켜야 합니다:
```
1. Slack 연동
2. 봇 정보
3. MCP 설정 (Perplexity, DeepL, GitLab, Atlassian, Outlook, X, Clova)
4. Computer Use
5. 웹 서버 / 음성 수신 채널
6. 능동 수신 채널 (Outlook, Confluence, Jira)
7. 선제적 제안 기능
```

**CRITICAL - Slack Credential Naming:**
- **Bot credentials** (for Slack Bolt framework):
  - `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_TEAM_ID`
  - Used in "Slack 연동" section
  - Slack Bolt auto-detects these names
- **Web OAuth credentials** (for web interface login):
  - `WEB_SLACK_CLIENT_ID`, `WEB_SLACK_CLIENT_SECRET`
  - Used in "웹 서버 / 음성 수신 채널" section
  - **MUST** have `WEB_` prefix to avoid Slack Bolt conflict
  - If named `SLACK_CLIENT_ID/SECRET`, Bolt switches to OAuth mode and breaks bot token

### 4. Error Handling
```python
# BAD - Developer-focused error
raise ValueError(f"Invalid token format: {token}")

# GOOD - User-friendly error
logger.error("Slack 연동 실패: 토큰이 올바르지 않습니다. 설정을 확인해주세요.")
return "Slack 연동에 실패했습니다. 환경변수 설정에서 Slack 토큰을 확인해주세요."
```

### 5. GUI Text Guidelines
- Use Korean for UI labels (primary users are Korean)
- Provide helpful placeholders
- Include inline help text (info-box, notice-box)
- Show examples where possible

---

## 🏗️ Complete System Architecture

### Message Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SLACK MESSAGE RECEIVED                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. DEBOUNCING (2초)                                         │
│    - 같은 사용자의 연속 메시지 병합                             │
│    - debounced_enqueue_message()                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CHANNEL QUEUE                                            │
│    - 채널별 독립 큐                                            │
│    - 8 workers per channel                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. MESSAGE PROCESSING (_process_message_logic)             │
│    ├─ Slack Context 수집 (최근 10개 메시지)                   │
│    ├─ Bot Call Detector (Haiku) - 봇 호출 여부 판단          │
│    │   ├─ DM: 항상 처리                                      │
│    │   ├─ Group: 멘션 시에만                                 │
│    │   └─ Thread: Thread Context Detector 추가 판단          │
│    ├─ Answer Aggregator - 답변 대기 질문 확인                 │
│    │   └─ waiting_answer DB 조회                            │
│    └─ 라우팅 결정                                            │
└─────────────────────────────────────────────────────────────┘
                 ↓                              ↓
    ┌────────────────────┐         ┌────────────────────────┐
    │ 5-A. SIMPLE CHAT   │         │ 5-B. ORCHESTRATOR      │
    │ (Haiku, no MCP)    │         │ (Sonnet, all MCP)      │
    │ - 간단한 대화       │         │ - 복잡한 작업           │
    │ - 즉시 응답         │         │ - Memory Retriever     │
    └────────────────────┘         └────────────────────────┘
                                               ↓
                              ┌────────────────────────────────┐
                              │ ORCHESTRATOR QUEUE (global)    │
                              │ - 3 workers                    │
                              │ - call_operator_agent()        │
                              └────────────────────────────────┘
                                               ↓
                              ┌────────────────────────────────┐
                              │ MEMORY QUEUE (global)          │
                              │ - 1 worker (순차 처리)          │
                              │ - call_memory_manager()        │
                              │ - 로컬 파일 시스템 저장        │
                              └────────────────────────────────┘
```

### 3-Tier Queue System

```python
# 1. Channel Queues (per-channel)
message_queues: Dict[str, asyncio.Queue] = {}
# - 8 workers per channel
# - Fast response for simple messages

# 2. Orchestrator Queue (global)
orchestrator_queue = asyncio.Queue(maxsize=100)
# - 3 workers
# - Heavy tasks with MCP tools

# 3. Memory Queue (global)
memory_queue = asyncio.Queue(maxsize=100)
# - 1 worker (sequential processing)
# - 로컬 파일 시스템 순차 저장
```

### Proactive Systems

#### 능동 수신 채널 (Checkers) - Beta

**Outlook Checker**
```
Scheduler (5분 간격)
  ↓
check_email_updates() - checker.py
  ├─ Outlook MCP로 받은메일함 조회
  └─ process_emails_batch()
       ├─ call_email_task_extractor() - agent.py
       │    └─ 중요한 작업 추출 → email_tasks DB 저장
       └─ Pending tasks → Slack Channel Queue로 전송
```

**Confluence Checker**
```
Scheduler (60분 간격)
  ↓
check_confluence_updates() - confluence_checker.py
  ├─ Rovo MCP로 최근 N시간 업데이트 조회
  ├─ Python에서 봇 본인 글 필터링
  └─ process_pages_batch()
       ├─ call_confluence_summarizer() - confluence_agent.py
       │    └─ 중요한 페이지만 요약
       └─ Memory에 저장
```

**Jira Checker**
```
Scheduler (30분 간격)
  ↓
check_jira_updates() - jira_checker.py
  ├─ Rovo MCP로 할당된 이슈 조회
  └─ process_issues_batch()
       ├─ DB에서 기존 이슈 제외
       ├─ call_jira_task_extractor() - jira_agent.py
       │    └─ 할 일 추출 → jira_tasks DB 저장
       └─ Pending tasks → Slack Channel Queue로 전송
```

#### 웹 서버 / 음성 수신 채널

```
FastAPI Server (port 8000, HTTPS)
  ├─ 인증: Microsoft 365 / Slack OAuth (OpenID Connect)
  ├─ X (Twitter) OAuth 2.0 인증 플로우
  ├─ Clova Speech 음성 인식
  └─ 음성 입력 처리
```

**필수 요구사항:**
- SSL 인증서 (`app/config/certs/`)
- Port 8000 사용 가능
- X, Clova Speech 사용 시 필수

**인증 시스템 (Critical):**
- **Slack OAuth**: OpenID Connect (OIDC) 사용
  - ❌ Legacy `identity.*` scopes (deprecated, invalid_scope 에러)
  - ✅ OIDC scopes: `openid`, `email`, `profile`
  - Endpoints: `/openid/connect/authorize`, `/api/openid.connect.token`
  - Enterprise Grid 호환 (Org-ready 필요할 수 있음)
  - Credentials: `WEB_SLACK_CLIENT_ID`, `WEB_SLACK_CLIENT_SECRET` (Bot Token과 분리)
- **Microsoft 365**: Azure AD OpenID Connect
  - Authlib 라이브러리 사용
  - Credentials: `OUTLOOK_CLIENT_ID`, `OUTLOOK_CLIENT_SECRET`, `OUTLOOK_TENANT_ID`
  - Graph API로 사용자 정보 조회

#### 선제적 제안 기능 - Beta

```
Dynamic Suggester (15분 간격)
  ↓
call_dynamic_suggester()
  ├─ 로컬 메모리 파일 분석
  ├─ 제안 생성 (Sonnet)
  ├─ call_proactive_confirm() - 사용자 승인 요청
  │    └─ confirm DB에 저장
  └─ 승인 시 → Orchestrator Queue로 전달
```

---

## 🤖 Agent Inventory

| Agent | Model | MCP | 용도 | 위치 |
|-------|-------|-----|------|------|
| **Bot Call Detector** | Haiku | ❌ | 봇 호출 여부 판단 | `cc_agents/bot_call_detector/` |
| **Thread Context Detector** | Haiku | ❌ | 스레드 내 맥락 판단 | `cc_agents/bot_thread_context_detector/` |
| **Answer Aggregator** | Sonnet | ✅ | 답변 대기 질문 확인 | `cc_agents/answer_aggregator/` |
| **Simple Chat** | Haiku | ❌ | 간단한 대화 | `cc_agents/simple_chat/` |
| **Memory Retriever** | Haiku | ✅ | 관련 메모리 검색 | `cc_agents/memory_retriever/` |
| **Operator** | Opus | ✅ | 복잡한 작업 수행 | `cc_agents/operator/` |
| **Memory Manager** | Sonnet | ✅ | 메모리 저장 | `cc_agents/memory_manager/` |
| **Email Task Extractor** | Haiku | ✅ | 이메일 작업 추출 | `cc_checkers/outlook/agent.py` |
| **Confluence Summarizer** | Haiku | ✅ | 중요 페이지 요약 | `cc_checkers/atlassian/confluence_agent.py` |
| **Jira Task Extractor** | Haiku | ✅ | Jira 작업 추출 | `cc_checkers/atlassian/jira_agent.py` |
| **Dynamic Suggester** | Sonnet | ✅ | 선제적 제안 생성 | `cc_agents/proactive_dynamic_suggester/` |
| **Proactive Confirm** | Haiku | ✅ | 제안 승인 요청 | `cc_agents/proactive_confirm/` |

---

## 🛠️ MCP Tools Available

### Core MCP Servers
- **slack**: 11 tools (메시지, 파일, 리액션, 채널 관리 등)
- **outlook**: 7 tools (메일 조회, 작성, 답장, 첨부파일 등)
- **atlassian**: Rovo MCP (Confluence/Jira 통합 검색 및 관리)
- **gitlab**: 코드 저장소 관리
- **x**: Twitter/X 도구 (OAuth 1.0a + OAuth 2.0)
- **perplexity**: 웹 검색
- **deepl**: 번역
- **playwright**: 브라우저 자동화 (Chrome profile 사용)
- **kris**: 내부 API

### Custom MCP Servers (Local)
- **scheduler**: 메시지 스케줄링 (SQLite)
- **waiting_answer**: 답변 수집 관리 (SQLite)
- **confirm**: 사용자 승인 관리 (SQLite)
- **email_tasks**: 이메일 작업 DB (SQLite)
- **jira_tasks**: Jira 작업 DB (SQLite)

---

## 💾 Data Storage

### SQLite Databases (4개)
```
~/.kira/
├── waiting_answer.db   # 답변 대기 질문
├── confirm.db          # 사용자 승인 대기 작업
├── email_tasks.db      # 이메일에서 추출된 작업
└── jira_tasks.db       # Jira에서 추출된 작업
```

### 로컬 메모리 시스템
```
$FILESYSTEM_BASE_DIR/memories/  # 기본: ~/Documents/KIRA/memories/
├── channels/           # 채널별 대화 기록
├── projects/           # 프로젝트 관련 정보
├── users/              # 유저별 정보
├── decisions/          # 결정사항
└── index.md            # 자동 생성 인덱스
```
- **형식**: Markdown 파일
- **관리**: `slack-employee-memory` skill 사용
- **검색**: Memory Retriever가 인덱스 기반 검색
- **저장**: Memory Manager가 자동 분류 및 저장

### Configuration
```
~/.kira/config.env      # 사용자 환경변수 (Electron 앱에서 저장)
```

---

## 📝 Development Patterns

### Checker Pattern (2-stage)

**Stage 1: Checker (Data Collection)**
```python
# cc_checkers/*/checker.py
async def check_*_updates():
    """스케줄러에서 주기적으로 호출"""
    # 1. MCP로 데이터 조회
    # 2. Python에서 필터링 (봇 본인 제외 등)
    # 3. Agent로 전달
    asyncio.create_task(process_*_batch(data))
```

**Stage 2: Agent (Analysis & Processing)**
```python
# cc_checkers/*/agent.py
async def call_*_extractor(data):
    """Claude SDK로 데이터 분석 및 처리"""
    # 1. System prompt 생성
    # 2. ClaudeSDKClient로 MCP 접근
    # 3. 결과를 DB 또는 메모리에 저장
    # 4. 필요 시 Slack Queue로 전송
```

### Agent Pattern (Standard)

```python
# cc_agents/*/agent.py
async def call_agent_name(
    user_query: str,
    slack_data: dict,
    message_data: dict,
    retrieved_memory: Optional[str] = None
) -> str:
    """
    Claude SDK를 사용하는 표준 에이전트 패턴

    Returns:
        str: 사용자에게 보낼 응답 (Korean)
        bool: Simple Chat의 경우 처리 여부
    """
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    # 1. System prompt 생성
    system_prompt = create_system_prompt(...)

    # 2. MCP 서버 설정
    mcp_servers = {...}

    # 3. Options 생성
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model="haiku",  # or sonnet-4-5
        permission_mode="bypassPermissions",
        allowed_tools=["*"],
        disallowed_tools=[...],
        mcp_servers=mcp_servers,
    )

    # 4. SDK 실행
    async with ClaudeSDKClient(options=options) as client:
        await client.query(user_query)
        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                return message.result
```

### MCP Tool Pattern

```python
# cc_tools/*/tools.py
@tool("tool_name", "User-friendly description", schema)
async def tool_function(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    CRITICAL: Use httpx.AsyncClient, NEVER requests
    ALWAYS return user-friendly Korean error messages
    """
    try:
        async with httpx.AsyncClient() as client:
            # Implementation
            pass
    except Exception as e:
        logger.error(f"[TOOL_NAME] Error: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"작업 실패: {str(e)}"
            }]
        }
```

### Web Authentication Pattern

**Multi-Provider OAuth Architecture:**

```python
# auth_handler.py - Provider routing
class AuthHandler:
    def __init__(self):
        self.provider = self._get_provider()  # From WEB_INTERFACE_AUTH_PROVIDER

        if self.provider == AuthProvider.MICROSOFT:
            self.azure_oauth = AzureOAuth()
        elif self.provider == AuthProvider.SLACK:
            self.slack_oauth = SlackOAuth()

    async def handle_login(self, request):
        if self.provider == AuthProvider.SLACK:
            # Slack OIDC flow
            return RedirectResponse(url=slack_oauth.get_authorize_url())
        else:
            # Microsoft Azure AD flow
            return await azure_oauth.authorize_redirect()

    async def handle_callback(self, request):
        # Provider-specific token exchange and user info retrieval
        # Both providers return: {name, email, id, provider}
```

**Critical OAuth Implementation Details:**

1. **Slack OIDC** (auth_slack.py):
   - Endpoints: `/openid/connect/authorize`, `/api/openid.connect.token`, `/api/openid.connect.userInfo`
   - Scopes: `openid email profile`
   - Response: `{ok: true, sub: "U...", name: "...", email: "...", picture: "..."}`
   - User ID field: `sub` (not `id`)

2. **Microsoft Azure** (auth_azure.py):
   - Uses Authlib OAuth library
   - Server metadata: `https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration`
   - Scopes: `openid email profile User.Read`
   - Graph API: `https://graph.microsoft.com/v1.0/me`

3. **Session Management**:
   - FastAPI SessionMiddleware
   - Session data: `{email, name, id, provider, avatar}`
   - Authorization check: `is_authorized_user(name)` from `cc_slack_handlers.py`

---

## 🖥️ Electron App Development

### Configuration File Structure

**저장 위치**: `~/.kira/config.env`

**섹션 순서** (main.js sections):
```javascript
const sections = {
  'Slack 연동': [...],
  '봇 정보': [...],
  'MCP 설정 - Perplexity': [...],
  'MCP 설정 - DeepL': [...],
  'MCP 설정 - GitLab': [...],
  'MCP 설정 - Atlassian Rovo': [...],
  'MCP 설정 - Outlook': [...],
  'MCP 설정 - X': [...],
  'MCP 설정 - Clova Speech': [...],
  'Computer Use': [...],
  '웹 서버 / 음성 수신 채널': [...],
  '능동 수신 채널 - Outlook': [...],
  '능동 수신 채널 - Confluence': [...],
  '능동 수신 채널 - Jira': [...],
  '선제적 제안 기능': [...]
};
```

### UI Section Structure (index.html)

```html
<!-- 필수 설정 -->
<section class="section">
  <h3>필수 설정 - Slack 연동</h3>
  <!-- SLACK_BOT_TOKEN, SLACK_APP_TOKEN, etc. -->
</section>

<section class="section">
  <h3>필수 설정 - 봇 정보</h3>
  <!-- BOT_NAME, BOT_EMAIL, etc. -->
</section>

<!-- MCP 설정 -->
<section class="section">
  <h3>MCP 설정</h3>
  <!-- Toggle + Fields pattern -->
  <div class="mcp-item">
    <div class="mcp-header">
      <span class="mcp-title">Service Name</span>
      <label class="toggle-switch">
        <input type="checkbox" id="SERVICE_ENABLED">
        <span class="toggle-slider"></span>
      </label>
    </div>
    <div class="mcp-fields" data-mcp="service" style="display: none;">
      <!-- Fields shown when enabled -->
    </div>
  </div>
</section>

<!-- Computer Use -->
<section class="section">
  <h3>Computer Use</h3>
</section>

<!-- 웹 서버 -->
<section class="section">
  <h3>웹 서버 / 음성 수신 채널</h3>
</section>

<!-- 능동 수신 채널 (Beta) -->
<section class="section">
  <h3>능동 수신 채널 <span class="beta-chip">beta</span></h3>
</section>

<!-- 선제적 제안 (Beta) -->
<section class="section">
  <h3>선제적 제안 기능 <span class="beta-chip">beta</span></h3>
</section>
```

### Main Process (main.js) Key Responsibilities

1. **Window Management**: 창 생성, 크기/위치 저장/복원
2. **Python Server Lifecycle**: uv 찾기, 프로세스 spawn, 환경변수 전달
3. **Configuration**: config.env 읽기/쓰기, parseConfigFile()
4. **IPC Handlers**: get-config, save-config, start-server, stop-server
5. **Log Streaming**: Python stdout/stderr를 renderer로 전송

### Renderer Process (renderer/main.js) Key Responsibilities

1. **Config Load/Save**: window.api.getConfig(), window.api.saveConfig()
2. **Toggle Visibility**: MCP fields, channel fields, voice fields 표시/숨김
3. **Auth Provider Handling**: Slack OAuth 필드 조건부 표시
4. **Server Control**: startServer(), stopServer()
5. **Log Display**: Real-time log streaming

---

## 🔥 Development Commands

### Python Server Development

```bash
# Hot reload development (recommended)
uv run python dev.py

# Direct server start (no reload)
uv run python -m app.main

# Install/sync dependencies
uv sync

# Install specific package
uv add package-name
```

### Electron App Development

```bash
cd electron-app

# Development mode (opens dev tools)
npm run start

# Build installers
npm run build           # macOS .dmg and .zip (arm64 (Apple Silicon))
npm run build -- --mac  # macOS only
npm run build -- --win  # Windows (requires Windows or Wine)
npm run build -- --linux  # Linux AppImage

# Publish to S3
npm run publish  # Requires AWS credentials

# Install dependencies
npm install
```

### Testing and Quality

```bash
# Python formatting (Black)
uv run black app/

# Check Python syntax
uv run python -m py_compile app/**/*.py

# Manual testing workflow:
# 1. Start Python server: uv run python dev.py
# 2. Start Electron app: cd electron-app && npm start
# 3. Test in Slack workspace
# 4. Check logs: tail -f ~/.kira/logs/kira.log
```

### Build Artifacts Location

```
electron-app/dist/
├── KIRA-X.X.X-arm64.dmg        # macOS installer
├── KIRA-X.X.X-arm64-mac.zip    # macOS portable
├── KIRA-1.0.5.exe                  # Windows installer
└── KIRA-1.0.5.AppImage             # Linux portable
```

---

## 🧪 Testing Checklist

### Before ANY Commit

#### Electron App
- [ ] App launches without errors
- [ ] Configuration saves/loads correctly
- [ ] Server starts/stops properly
- [ ] Logs display in real-time
- [ ] Error messages are user-friendly
- [ ] Toggle switches work (MCP, channels, voice)
- [ ] Auth provider dropdown shows/hides Slack fields

#### Python Server
- [ ] Starts with minimal config (just Slack tokens)
- [ ] Handles missing optional configs gracefully
- [ ] Responds to Slack messages
- [ ] Logs are informative but not overwhelming
- [ ] Checkers run on schedule (if enabled)
- [ ] Web server starts (if enabled)

#### Environment Variables
- [ ] settings.py 순서와 일치
- [ ] dev.env 순서와 일치
- [ ] index.html UI 순서와 일치
- [ ] main.js sections 순서와 일치

#### Integration
- [ ] Fresh install works (no existing config)
- [ ] Upgrade preserves existing config
- [ ] Server restarts handle gracefully
- [ ] Memory/CPU usage is reasonable

---

## 🎨 UI/UX Standards

### Visual Design
- **Theme**: Dark mode (easier on eyes for 24/7 operation)
- **Font**: SF Pro Display (macOS), Segoe UI (Windows)
- **Colors**: Blue accent (#007AFF), success green (#34C759), error red (#FF3B30)

### Korean Language Standards
```javascript
// UI Labels (Korean)
"시작하기"      // Start
"중지하기"      // Stop
"설정하기"      // Configure
"로그 보기"     // View Logs

// Status Messages (Korean + English technical terms)
"Slack 연결 성공"
"Outlook 모니터링 시작 (5분 간격)"
"Confluence 페이지 업데이트 확인 중"
```

### Info Box Types
```html
<!-- General information -->
<div class="info-box">
  일반 정보나 도움말
</div>

<!-- Important notice -->
<div class="notice-box">
  <strong>중요:</strong> 웹 인터페이스가 필요합니다.
</div>
```

---

## 🚀 Performance Considerations

### Electron App
- **Window State**: Save and restore window position/size
- **Log Streaming**: Limit to last 1000 lines to prevent memory issues
- **Config Updates**: Debounce saves to prevent excessive disk writes

### Python Server
- **Queue Workers**:
  - 8 workers per channel (fast response)
  - 3 orchestrator workers (heavy tasks)
  - 1 memory worker (sequential)
- **Debouncing**: 2-second delay for message grouping
- **Memory Management**: Rotate logs, clean tmp files
- **Async Everything**: Use asyncio for all I/O operations

---

## 🔐 Security Principles

1. **Credentials**: Never log tokens or passwords
2. **Storage**: `~/.kira/config.env` with proper permissions
3. **Communication**: IPC only through preload script
4. **Validation**: Sanitize all user inputs
5. **Permissions**: Request minimum required scopes
6. **Web Auth**: Microsoft 365 or Slack OAuth only (no "none" option)

---

## 📊 Monitoring & Debugging

### Development Tools
```bash
# View Python logs
tail -f ~/.kira/logs/kira.log

# Phoenix tracing (if configured)
open https://phoenix.arize.com

# Electron DevTools
# Cmd+Option+I (macOS) or F12 (Windows/Linux)
```

### Production Diagnostics
- Check `~/.kira/logs/` for server logs
- View Electron logs in app's log viewer
- Use Phoenix for tracing agent behavior
- Monitor Slack App dashboard for API limits

---

## 💡 Common Issues & Solutions

### Issue: "uv not found"
**Solution**: Install uv with `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Issue: "Slack token invalid"
**Solution**: Check Slack App settings, regenerate tokens if needed

### Issue: "Server won't start"
**Solution**: Check port 8000 availability, verify Python version 3.10+

### Issue: "Checker not working"
**Solution**:
1. Check MCP is enabled (OUTLOOK_ENABLED, ATLASSIAN_ENABLED)
2. Check checker is enabled (*_CHECK_ENABLED)
3. View logs for authentication errors

### Issue: "Web Interface dependencies"
**Solution**: Show user that X, Clova require WEB_INTERFACE_ENABLED=True

### Issue: "Slack OAuth invalid_scope error"
**Solution**:
1. Legacy `identity.*` scopes are deprecated - use OpenID Connect instead
2. In Slack App settings, User Token Scopes:
   - Remove: `identity.basic`, `identity.email`, `identity.avatar`, `identity.team`
   - Add: `openid`, `email`, `profile`
3. For Enterprise Grid, enable "Org-ready" in Slack App settings
4. Reinstall app to workspace after scope changes

---

## 🎯 Remember: The User Experience is Everything

Every line of code should consider:
- **Sarah from Marketing** who's never used a terminal
- **John from Sales** who just wants it to work
- **The IT Admin** who needs to deploy to 50 computers
- **The Solo Founder** working at 2 AM

This isn't just a bot - it's an AI employee that lives in a desktop app. Make it feel like hiring a helpful colleague, not configuring a server.

---

## 📦 배포 (Deployment)

### 프로덕션 URL

**문서 사이트:**
```
https://kira.krafton-ai.com/
```

**앱 다운로드:**
```
https://kira.krafton-ai.com/download/KIRA-{version}-arm64.dmg
```

**현재 버전**: 0.9.0

### 배포 인프라

- **S3 버킷**: `kira-releases` (ap-northeast-2)
  - 문서 HTML 파일 (VitePress)
  - 앱 다운로드 파일 (`.dmg`, `.zip`)
- **CloudFront**: Custom domain `kira.krafton-ai.com`
  - Origin: S3 Website Endpoint
  - SSL: AWS ACM 인증서
- **Route 53**: `kira.krafton-ai.com` A 레코드 (Alias)

### 배포 방법

**문서 배포:**
```bash
cd vitepress-app
npm run deploy
```

**앱 배포:**
```bash
cd electron-app
npm version patch  # 버전 업데이트
npm run deploy     # 빌드 + S3 업로드
```

**상세 가이드**: `DEPLOY.md` 참고

---

## 📌 Quick Reference

### Key Files to Check When Adding Features

1. **Environment Variables**:
   - `app/config/settings.py`
   - `app/config/env/dev.env`
   - `electron-app/renderer/index.html`
   - `electron-app/main.js`

2. **Message Processing**:
   - `app/cc_slack_handlers.py`
   - `app/queueing_extended.py`

3. **Agents**:
   - `app/cc_agents/*/agent.py`

4. **Checkers**:
   - `app/cc_checkers/*/checker.py`
   - `app/cc_checkers/*/agent.py`

5. **Scheduler**:
   - `app/main.py` (scheduler registration)

6. **Web Server**:
   - `app/cc_web_interface/server.py`
   - `app/cc_web_interface/auth_handler.py` (provider routing)
   - `app/cc_web_interface/auth_slack.py` (Slack OIDC)
   - `app/cc_web_interface/auth_azure.py` (MS365 OAuth)

---

**Final Note for Claude Code**: When in doubt, prioritize simplicity and user experience over technical elegance. The best code is the code that lets non-developers successfully deploy their own AI employee.

**추가 변경 시 반드시 체크**:
- 환경변수 4곳 동기화 (settings.py, dev.env, index.html, main.js)
- 섹션 순서 일치
- 한글 UI 레이블
- 사용자 친화적 에러 메시지
