# 웹 인터페이스 (음성 입력)

![웹 인터페이스](/images/screenshots/web-interface-main.png)

웹 인터페이스를 활성화하면 브라우저에서 KIRA와 대화하고 음성으로 입력할 수 있습니다.

::: tip 필수 기능
웹 인터페이스는 다음 기능을 사용하기 위해 **필수**입니다:
- 음성 입력 (마이크 사용)
- Clova Speech (회의록 작성)
- X (Twitter) OAuth 인증
:::

## 📋 준비물

- Microsoft 365 계정 또는 Slack 계정 (로그인용)
- 브라우저 (Chrome, Safari, Edge 등)

---

## ⚙️ 1단계: KIRA 설정

### 1. KIRA 앱 실행
환경변수 설정 탭을 엽니다.

### 2. 웹 서버 섹션 찾기
**웹 서버 / 음성 수신 채널** 섹션으로 스크롤

### 3. Web Interface 활성화
- **Web Interface** 토글 스위치를 **켜기**로 변경

::: info 웹 서버 정보
- **포트**: 8000
- **프로토콜**: HTTPS
- **URL**: `https://localhost:8000`
:::

### 4. 인증 방식 선택
드롭다운에서 선택:
- **Microsoft 365**: 회사 계정으로 로그인
- **Slack**: Slack 워크스페이스 계정으로 로그인

::: tip 어떤 인증 방식을 선택할까?
- Microsoft 365 사용 중 → **Microsoft 365**
- Slack만 사용 → **Slack**
- 둘 다 사용 → 선호하는 방식 선택
:::

### 5. Slack 인증 선택 시 (선택사항)
Slack을 인증 방식으로 선택한 경우:

1. Slack App 설정 페이지 접속
2. **"OAuth & Permissions"** 클릭
3. **"Redirect URLs"** 섹션에서 **"Add New Redirect URL"** 클릭
4. 다음 URL 추가:
   ```
   http://localhost:8000/auth/callback
   ```
5. **"Save URLs"** 클릭
6. **"Basic Information"** > **"App Credentials"**에서:
   - **Client ID** 복사 → KIRA에 `WEB_SLACK_CLIENT_ID` 입력
   - **Client Secret** 복사 → KIRA에 `WEB_SLACK_CLIENT_SECRET` 입력

::: warning Slack OAuth 설정
Slack을 인증 방식으로 사용하려면 Slack App에 Redirect URL을 추가해야 합니다.
Microsoft 365를 사용한다면 이 단계는 건너뛰세요.
:::

### 6. 외부 접속 URL (선택사항)
**Base URL (외부 접속용)**:
- 로컬에서만 사용: 비워두기
- 외부(인터넷)에서 접속: ngrok 등의 URL 입력
  - 예: `https://abc123.ngrok-free.app`

### 7. 설정 저장
- **"설정 저장"** 버튼 클릭
- 서버 재시작

---

## ✅ 2단계: 웹 접속 및 로그인

### 1. 브라우저 열기
1. 브라우저에서 `https://localhost:8000` 접속
2. 보안 경고가 나타날 수 있음 (자체 서명 인증서 사용)
3. **"고급"** > **"계속 진행"** 클릭

::: tip HTTPS 보안 경고
KIRA는 로컬 HTTPS 서버를 사용하므로 브라우저에서 보안 경고가 표시됩니다.
이는 정상이며 안전하게 진행하셔도 됩니다.
:::

### 2. 로그인
선택한 인증 방식으로 로그인:

**Microsoft 365:**
1. **"Microsoft로 로그인"** 버튼 클릭
2. Microsoft 계정 입력
3. 권한 승인
4. 로그인 완료

**Slack:**
1. **"Slack으로 로그인"** 버튼 클릭
2. Slack 워크스페이스 선택
3. 권한 승인
4. 로그인 완료

### 3. 권한 확인
- 로그인한 사용자가 `BOT_AUTHORIZED_USERS`에 등록되어 있어야 합니다
- 등록되지 않은 경우 접근이 거부됩니다

---

## 🎤 3단계: 음성 입력 사용

### 1. 마이크 권한 허용
1. 웹 페이지에서 **마이크 버튼** 클릭
2. 브라우저가 마이크 권한 요청
3. **"허용"** 클릭

### 2. 음성으로 말하기
1. 마이크 버튼이 빨간색으로 변함 (녹음 중)
2. KIRA에게 질문이나 요청 말하기
3. 말이 끝나면 자동으로 텍스트 변환
4. KIRA가 응답

### 3. 중지
- **정지 버튼** 클릭하여 녹음 종료

---

## 🎯 사용 예시

### 음성으로 대화
```
[마이크 버튼 클릭]
"안녕 KIRA, 오늘 날씨 어때?"

[KIRA 응답]
"안녕하세요! 오늘 서울은 맑고 최고 기온 18도입니다."
```

### 회의록 작성 (Clova Speech 필요)
```
[마이크 버튼 클릭]
"오늘 미팅에서는 신규 프로젝트 일정을 논의했습니다.
개발팀은 다음 주까지 프로토타입을 완성하고..."

[KIRA가 자동으로 회의록 정리]
```

### 긴 메시지 입력
```
타이핑하기 번거로운 긴 내용을 음성으로 빠르게 입력
```

---

## 🔧 문제해결

### "웹 서버에 접속할 수 없습니다"
- WEB_INTERFACE_ENABLED가 켜져 있는지 확인
- KIRA 서버가 실행 중인지 확인
- 포트 8000이 다른 프로그램에서 사용 중인지 확인

### HTTPS 보안 경고
- **정상입니다!** 로컬 자체 서명 인증서 사용
- "고급" > "계속 진행" 클릭하세요
- Chrome: "thisisunsafe" 타이핑 (화면에 보이지 않음)

### 마이크가 작동하지 않음
- 브라우저 설정에서 마이크 권한 확인
- Chrome: 설정 > 개인정보 및 보안 > 사이트 설정 > 마이크
- 시스템 설정에서 브라우저의 마이크 접근 허용 확인

### "권한이 없습니다"
- BOT_AUTHORIZED_USERS에 본인 이름이 등록되어 있는지 확인
- 이름이 Slack/Microsoft 프로필과 정확히 일치하는지 확인
- 대소문자, 공백까지 정확해야 합니다

### Slack 로그인 실패
- WEB_SLACK_CLIENT_ID와 WEB_SLACK_CLIENT_SECRET 확인
- Slack App의 Redirect URL이 `http://localhost:8000/auth/callback`로 설정되었는지 확인
- Slack App이 워크스페이스에 설치되어 있는지 확인

---

## 💡 팁

### 음성 인식 정확도 높이기
- 조용한 환경에서 사용
- 마이크와 20-30cm 거리 유지
- 명확한 발음
- 배경 소음 최소화

### 외부에서 접속하기
ngrok 사용 예시:
```bash
ngrok http 8000
```

생성된 URL을 KIRA 설정의 **Base URL**에 입력:
```
https://abc123.ngrok-free.app
```

::: warning 외부 접속 보안
외부에서 접속 가능하게 설정하면 보안에 주의해야 합니다.
- 강력한 인증 사용
- 신뢰할 수 있는 사람만 접근
- 임시로만 사용 권장
:::

### 브라우저별 호환성
- ✅ Chrome / Edge (Chromium) - 권장
- ✅ Safari - 호환
- ✅ Firefox - 호환
- ❌ IE - 지원 안 함

### 모바일에서 사용
- 모바일 브라우저에서도 접속 가능
- 음성 입력도 작동
- 단, 화면이 작아 PC 권장

---

## 🔐 보안

### 인증 시스템
- Microsoft 365 또는 Slack OAuth 사용
- 세션 기반 인증
- 승인된 사용자만 접근 가능

### HTTPS 사용
- 모든 통신이 암호화됩니다
- 자체 서명 인증서 사용 (로컬)
- 외부 접속 시 ngrok 등의 정식 인증서 사용 권장

### 데이터 보안
- 음성 데이터는 서버로 전송 후 즉시 처리
- 녹음 파일은 저장되지 않음
- 모든 대화 내용은 메모리에만 저장

---

## ⚠️ 중요 체크리스트

웹 인터페이스 사용 전:

- [ ] WEB_INTERFACE_ENABLED 활성화
- [ ] 인증 방식 선택 (Microsoft 365 or Slack)
- [ ] Slack 선택 시 Redirect URL 설정
- [ ] 설정 저장 및 서버 재시작
- [ ] `https://localhost:8000` 접속 가능 확인
- [ ] 로그인 성공 확인
- [ ] 마이크 권한 허용
- [ ] 음성 입력 테스트 완료

모든 항목을 확인한 후 웹 인터페이스를 사용하세요! 🎉
