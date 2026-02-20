# X (Twitter) 연동

X (구 Twitter) API를 연동하면 KIRA가 트윗을 작성하고 관리할 수 있습니다.

::: danger 웹 인터페이스 필수!
X (Twitter) 기능을 사용하려면 **웹 인터페이스가 반드시 활성화**되어 있어야 합니다.
OAuth 2.0 인증을 위한 callback URL (`http://localhost:8000/bot/auth/x/callback`)을 받아야 하기 때문입니다.

먼저 [웹 인터페이스 설정](/ko/setup/web-interface)을 완료한 후 이 페이지로 돌아와주세요.
:::

## 📋 준비물

- X (Twitter) 계정
- X Developer Account
- X Developer Portal 접근 권한
- ✅ **KIRA 웹 인터페이스 활성화** (필수!)

---

## 🔑 1단계: X Developer App 생성

### 1. X Developer Portal 접속
1. [X Developer Portal](https://developer.twitter.com/en/portal/dashboard) 접속
2. X 계정으로 로그인
3. Developer 계정이 없다면 신청 (몇 분 소요)

### 2. 새 App 생성
1. **"Projects & Apps"** 메뉴 클릭
2. **"+ Create App"** 클릭
3. App 이름 입력 (예: `KIRA Bot`)
4. App 환경 선택: **"Production"**

### 3. API Keys 확인 (OAuth 1.0a)
App 생성 직후 표시되는 키들을 복사하세요:

- **API Key (Consumer Key)** → `X_API_KEY`
- **API Secret (Consumer Secret)** → `X_API_SECRET`
- **Bearer Token** (사용 안 함)

::: warning 한 번만 표시됩니다!
API Secret은 생성 시 한 번만 표시됩니다. 반드시 복사하세요!
나중에 필요하면 **"Regenerate"**로 새로 생성해야 합니다.
:::

### 4. Access Token 생성 (OAuth 1.0a)
1. App 설정 페이지에서 **"Keys and tokens"** 탭 클릭
2. **"Access Token and Secret"** 섹션
3. **"Generate"** 클릭
4. 생성된 토큰 복사:
   - **Access Token** → `X_ACCESS_TOKEN`
   - **Access Token Secret** → `X_ACCESS_TOKEN_SECRET`

### 5. OAuth 2.0 설정 (중요!)

OAuth 2.0은 웹 인터페이스를 통한 사용자 인증에 필요합니다.

1. App 설정 페이지에서 **"Settings"** 탭 클릭
2. **"User authentication settings"** 섹션에서 **"Set up"** 클릭
3. **"App permissions"** 선택:
   - ✅ **Read and write** (읽기 및 쓰기)
   - 또는 필요에 따라 **Read and write and Direct message**
4. **"Type of App"** 선택:
   - ✅ **Web App, Automated App or Bot**
5. **"App info"** 입력:
   - **Callback URI / Redirect URL**:
     ```
     http://localhost:8000/bot/auth/x/callback
     ```
   - **Website URL**: `http://localhost:8000` (임시)
6. **"Save"** 클릭

### 6. OAuth 2.0 Client ID 및 Secret
설정 완료 후 표시되는 값을 복사:

- **OAuth 2.0 Client ID** → `X_OAUTH2_CLIENT_ID`
- **OAuth 2.0 Client Secret** → `X_OAUTH2_CLIENT_SECRET`

::: tip Callback URL이 중요한 이유
X OAuth 2.0 인증은 사용자를 X 로그인 페이지로 리다이렉트한 후,
인증 완료 시 `http://localhost:8000/bot/auth/x/callback`로 돌아옵니다.
따라서 **KIRA 웹 서버(port 8000)가 실행 중**이어야 합니다.
:::

---

## ⚙️ 2단계: KIRA 설정

### 1. 웹 인터페이스 먼저 활성화

::: danger 순서가 중요합니다!
X 설정 **전에** 반드시 웹 인터페이스를 활성화하세요.
:::

1. KIRA 앱 > 환경변수 설정
2. **"웹 서버 / 음성 수신 채널"** 섹션으로 스크롤
3. **WEB_INTERFACE_ENABLED** 토글을 **켜기**로 변경
4. 필요한 웹 인터페이스 설정 완료
5. 설정 저장 및 서버 재시작
6. 웹 서버가 `http://localhost:8000`에서 실행 중인지 확인

자세한 내용은 [웹 인터페이스 설정 가이드](/ko/setup/web-interface)를 참고하세요.

### 2. X 섹션 찾기
**MCP 설정** > **X (Twitter)**

### 3. 설정 활성화
- 토글 스위치를 **켜기**로 변경

### 4. API 키 입력

**OAuth 1.0a (기본 API 접근):**
- **X_API_KEY**: API Key (Consumer Key)
- **X_API_SECRET**: API Secret (Consumer Secret)
- **X_ACCESS_TOKEN**: Access Token
- **X_ACCESS_TOKEN_SECRET**: Access Token Secret

**OAuth 2.0 (사용자 인증):**
- **X_OAUTH2_CLIENT_ID**: OAuth 2.0 Client ID
- **X_OAUTH2_CLIENT_SECRET**: OAuth 2.0 Client Secret

### 5. 설정 저장
- **"설정 저장"** 버튼 클릭
- 서버 재시작

---

## ✅ 3단계: OAuth 인증

### 웹 브라우저를 통한 인증

KIRA가 X에 처음 접근할 때:

1. **브라우저가 자동으로 열립니다**
2. X 로그인 페이지 표시
3. 계정으로 로그인
4. **앱 권한 승인 화면**:
   - KIRA Bot이 트윗 읽기/쓰기 권한 요청
5. **"Authorize app"** 클릭
6. 자동으로 `http://localhost:8000/bot/auth/x/callback`로 리다이렉트
7. 인증 완료 메시지 확인

::: tip 자동 인증
- OAuth 토큰은 안전하게 저장됩니다
- 다음부터는 자동으로 인증됩니다
- 토큰 만료 시 자동으로 갱신됩니다
:::

---

## 🎯 사용 예시

### 트윗 작성
```
사용자: X에 트윗 올려줘: "KIRA와 함께하는 AI 자동화"
KIRA: [X 트윗] 트윗을 게시했습니다.
      https://twitter.com/yourname/status/1234567890
```

### 최근 트윗 조회
```
사용자: 내 최근 트윗 5개 보여줘
KIRA: [X 조회]
      1. "KIRA와 함께하는..." - 2시간 전
      2. "AI 자동화 시작" - 5시간 전
      ...
```

### 멘션 확인
```
사용자: 내게 온 멘션 확인해줘
KIRA: [X 조회]
      1. @friend: "안녕하세요!"
      2. @colleague: "미팅 일정 공유 부탁드립니다"
```

### 트윗 검색
```
사용자: X에서 "AI" 키워드로 트윗 검색해줘
KIRA: [X 검색]
      1. @tech_user: "AI의 미래는..."
      2. @ai_news: "최신 AI 뉴스..."
```

---

## 🔧 문제해결

### "Callback URL mismatch"
- X Developer Portal에서 Callback URI 확인
- 정확히 `http://localhost:8000/bot/auth/x/callback` 입력
- **HTTPS가 아닌 HTTP** 확인
- 포트 번호(8000) 확인

### "Web Interface not enabled"
- KIRA 설정에서 WEB_INTERFACE_ENABLED 확인
- 웹 서버가 실행 중인지 확인 (`http://localhost:8000`)
- 로그에서 웹 서버 시작 메시지 확인

### OAuth 브라우저가 열리지 않음
- 방화벽에서 port 8000 차단 확인
- 웹 인터페이스가 제대로 활성화되었는지 확인
- 수동으로 `http://localhost:8000/bot/auth/x/start` 접속

### "Authentication failed"
- API Keys가 올바른지 확인
- OAuth 2.0 Client ID/Secret 확인
- X Developer Portal에서 앱이 활성화되었는지 확인
- App permissions (Read and write) 확인

### "Rate limit exceeded"
- X API 사용 한도 초과
- [X Developer Portal](https://developer.twitter.com/en/portal/dashboard)에서 사용량 확인
- Free tier: 월 500 트윗 제한
- 유료 플랜 고려

---

## 💡 팁

### API 플랜 이해하기

**Free Tier:**
- 월 1,500 트윗 읽기
- 월 500 트윗 쓰기
- 개인 프로젝트에 적합

**Basic ($100/month):**
- 월 10,000 트윗 쓰기
- 고급 검색 기능

**Pro ($5,000/month):**
- 무제한 API 접근
- 기업용

### 보안 강화
- API Keys와 Secrets 안전하게 보관
- OAuth 2.0 토큰 정기적으로 갱신
- 필요한 권한만 부여 (Read/Write 분리)

### 효과적인 사용
- 트윗 스케줄링 활용
- 자동 답글 기능
- 트렌드 모니터링
- 멘션 자동 응답

### 포트 8000 이미 사용 중이라면?
KIRA는 기본적으로 port 8000을 사용합니다.
다른 포트를 사용하려면:
1. 웹 인터페이스 설정에서 포트 변경
2. X Developer Portal의 Callback URI도 변경
3. 예: `http://localhost:3000/bot/auth/x/callback`

---

## ⚠️ 중요 체크리스트

시작하기 전 확인하세요:

- [ ] X Developer Account 생성 완료
- [ ] X App 생성 및 API Keys 발급
- [ ] OAuth 2.0 설정 완료 (Callback URI 포함)
- [ ] **KIRA 웹 인터페이스 활성화** ✅
- [ ] 웹 서버 실행 확인 (`http://localhost:8000`)
- [ ] 6개 키 모두 KIRA에 입력
  - API Key, API Secret
  - Access Token, Access Token Secret
  - OAuth2 Client ID, OAuth2 Client Secret
- [ ] 설정 저장 및 서버 재시작
- [ ] OAuth 브라우저 인증 완료

모든 항목을 확인한 후 X 기능을 사용하세요! 🎉
