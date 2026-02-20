# 문제 해결

KIRA 사용 중 발생할 수 있는 문제와 해결 방법입니다.

---

## 🛠️ 설치 문제

### "uv not found"

uv가 설치되지 않았거나 PATH에 없습니다.

**해결:**
```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 터미널 재시작 후 확인
uv --version
```

### "claude not found" / "Claude CLI not found"

Claude Code CLI가 설치되지 않았습니다.

**해결:**
```bash
# Node.js가 설치되어 있는지 확인
node --version

# Claude Code CLI 설치
npm install -g @anthropic-ai/claude-code

# 확인
claude --version
```

### "npm not found"

Node.js가 설치되지 않았습니다.

**해결:**
1. [Node.js 공식 사이트](https://nodejs.org/)에서 LTS 버전 다운로드
2. 설치 후 터미널 재시작
3. `node --version`으로 확인

---

## 🚀 서버 시작 문제

### "서버가 시작되지 않아요"

**확인사항:**
1. KIRA 앱 로그 창에서 에러 메시지 확인
2. uv와 Claude CLI가 설치되었는지 확인
3. 앱 재시작 시도

**포트 충돌 확인:**
```bash
# 8000번 포트 사용 중인 프로세스 확인
lsof -i :8000

# 해당 프로세스 종료
kill -9 <PID>
```

### "Python 관련 에러"

**해결:**
```bash
# Python 버전 확인 (3.10 이상 필요)
python3 --version

# uv로 의존성 재설치
cd /Applications/KIRA.app/Contents/Resources/app
uv sync
```

---

## 🔌 MCP 서버 연결 문제

### "MCP 서버가 'failed' 상태로 표시돼요"

npx를 사용하는 MCP 서버들이 연결에 실패합니다.

**증상:**
- 일부 MCP 서버는 `connected`인데 다른 서버들은 `failed`
- 로컬 서버(slack, scheduler, files, deepl)는 정상인데 npx 기반 서버만 실패

**원인:**
`sudo npm install -g`로 Claude Code를 설치한 경우, npm 캐시 폴더 소유권이 root로 변경되어 권한 문제가 발생합니다.

**문제 확인:**
```bash
npx -y @mcpcentral/mcp-time
# "EACCES: permission denied" 에러가 나오면 이 문제입니다
```

**해결 방법:**
```bash
sudo chown -R $(whoami) ~/.npm
```

그 후 KIRA 앱을 재시작하세요.

::: warning 문제 예방하기
글로벌 npm 패키지 설치 시 `sudo`를 사용하지 마세요. `npm install -g`에서 권한 오류가 나면 먼저 권한을 수정하세요:
```bash
sudo chown -R $(whoami) /usr/local/lib/node_modules
sudo chown -R $(whoami) /usr/local/bin
```
그 다음 sudo 없이 `npm install -g`를 실행하세요.
:::

::: tip 권장: nvm 사용
권한 문제를 완전히 피하려면 [nvm](https://github.com/nvm-sh/nvm)으로 Node.js를 설치하세요:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
npm install -g @anthropic-ai/claude-code  # sudo 필요 없음
```
:::

---

## 💬 Slack 연결 문제

### "Slack connection failed"

**확인사항:**
1. **Bot Token** (`xoxb-...`)이 올바른지 확인
2. **App Token** (`xapp-...`)이 올바른지 확인
3. Slack App에서 **Socket Mode**가 활성화되었는지 확인
4. 워크스페이스에 앱이 설치되었는지 확인

**토큰 재발급:**
1. [Slack API](https://api.slack.com/apps) 접속
2. 앱 선택 > OAuth & Permissions > Reinstall to Workspace
3. 새 토큰으로 KIRA 설정 업데이트

### "봇이 응답하지 않아요"

**확인사항:**
1. 채널에 봇을 초대했는지: `/invite @봇이름`
2. **AUTHORIZED_USERS**에 본인 이름이 등록되었는지
3. 이름이 Slack 프로필의 **실제 이름**과 정확히 일치하는지
4. 로그에서 에러 메시지 확인

### "채널에서 멘션해도 응답 없음"

**확인사항:**
1. 채널에 봇이 초대되었는지 확인
2. Slack App에 `app_mention` 이벤트가 등록되었는지 확인
3. `message.channels` 권한이 있는지 확인

### "갑자기 메시지를 수신하지 못해요"

Event Subscriptions이 자동으로 비활성화되었을 수 있습니다.

**원인:**
KIRA가 정상적으로 종료되지 않으면(강제 종료, 크래시 등), Slack에서 해당 앱의 Event Subscriptions을 자동으로 비활성화할 수 있습니다.

**해결 방법:**
1. [Slack API Apps](https://app.slack.com/apps) 또는 [api.slack.com/apps](https://api.slack.com/apps) 접속
2. KIRA 앱 선택
3. **Event Subscriptions** 메뉴 이동
4. 토글이 **OFF** 상태인지 확인 - **ON**으로 다시 켜기
5. **Save Changes** 클릭
6. KIRA 재시작

::: warning 예방하기
앱을 닫기 전에 항상 Stop 버튼으로 KIRA를 정상 종료하세요. 강제 종료를 피하세요.
:::

---

## 🔄 업데이트 문제

### "자동 업데이트가 안돼요"

**수동 업데이트:**
1. [KIRA 다운로드 페이지](https://kira.krafton-ai.com/)에서 최신 버전 다운로드
2. 기존 앱 삭제 후 새로 설치
3. 설정은 `~/.kira/config.env`에 보존됨

---

## ⚡ Claude API 문제

### "Rate Limit 에러 (429)"

Claude API 요청 제한에 도달했습니다.

**증상:**
- 봇이 응답하지 않음
- 로그에 `429 Too Many Requests` 또는 `rate_limit_error` 메시지

**원인:**
- Claude API는 분당/일간 요청 제한이 있음
- 동시에 많은 메시지를 처리할 때 발생
- Tier에 따라 제한이 다름 (Tier 1: 분당 50 요청, Tier 4: 분당 4,000 요청)

**해결:**
1. **즉시**: 잠시 기다린 후 다시 시도 (보통 1분 이내 해제)
2. **사용량 확인**: [Anthropic Console](https://console.anthropic.com/settings/limits)에서 현재 사용량 모니터링
3. **장기 해결**:
   - Anthropic에 Tier 업그레이드 요청
   - 불필요한 능동 수신 채널(Checker) 비활성화
   - 메시지 처리 빈도 조절

::: warning 참고
Rate limit은 API 키 단위로 적용됩니다. 여러 사용자가 같은 키를 사용하면 더 빨리 제한에 도달할 수 있습니다.
:::

### "API Key 인증 실패"

**확인사항:**
1. `ANTHROPIC_API_KEY` 환경변수가 설정되었는지 확인
2. API 키가 유효한지 [Anthropic Console](https://console.anthropic.com/)에서 확인
3. API 키에 충분한 크레딧이 있는지 확인

---

## 🔧 로그 확인 방법

### KIRA 앱 로그
- 앱 하단의 로그 창에서 실시간 확인
- 파일 위치: `~/.kira/server.log`

### 로그 파일 열기
```bash
# 실시간 로그 확인
tail -f ~/.kira/server.log

# 최근 100줄 확인
tail -100 ~/.kira/server.log
```

### 에러 로그만 필터링
```bash
grep -i "error\|exception" ~/.kira/server.log
```

---

## 📞 추가 지원

문제가 해결되지 않으면:

1. **로그 확인**: `~/.kira/server.log` 파일의 에러 메시지 확인
2. **설정 확인**: KIRA 앱에서 모든 필수 설정이 입력되었는지 확인
3. **재시작**: 앱 종료 후 다시 시작
4. **재설치**: 설정 파일(`~/.kira/config.env`)은 보존되므로 앱만 재설치

::: tip 설정 백업
문제 해결 전 설정을 백업해두세요:
```bash
cp ~/.kira/config.env ~/Desktop/kira-config-backup.env
```
:::
