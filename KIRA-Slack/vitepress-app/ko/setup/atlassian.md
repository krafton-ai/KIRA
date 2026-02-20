# Confluence & Jira

Atlassian Rovo MCP를 연동하면 KIRA가 Confluence와 Jira를 관리할 수 있습니다.

## 📋 준비물

- Atlassian 계정
- Confluence 및/또는 Jira 액세스 권한

---

## 🎯 주요 기능

### Confluence
- 페이지 읽기/검색
- 페이지 생성/수정
- 페이지 이력 조회
- 첨부 파일 관리

### Jira
- 이슈 조회/검색
- 이슈 생성/수정
- 코멘트 추가
- 상태 변경

---

## ⚙️ 1단계: KIRA 설정

### 1. KIRA 앱 실행
환경변수 설정 탭을 엽니다.

### 2. Atlassian 섹션 찾기
**MCP 설정** > **Atlassian (Jira/Confluence)**

### 3. 설정 활성화
- 토글 스위치를 **켜기**로 변경

### 4. 사이트 URL 입력

**ATLASSIAN_CONFLUENCE_SITE_URL**
- Confluence 사이트 URL을 입력합니다
- 예: `https://your-company.atlassian.net`
- 또는: `https://confluence.company.com` (Self-hosted)

**ATLASSIAN_JIRA_SITE_URL**
- Jira 사이트 URL을 입력합니다
- 예: `https://your-company.atlassian.net`
- 또는: `https://jira.company.com` (Self-hosted)

::: tip Cloud vs Self-hosted
- **Atlassian Cloud**: `https://yourname.atlassian.net` 형식
- **Self-hosted (Server/Data Center)**: 회사 도메인 사용
:::

**ATLASSIAN_CONFLUENCE_DEFAULT_PAGE_ID** (선택사항)
- "위키에 올려줘" 요청 시 사용할 기본 페이지 ID
- Confluence 페이지 URL에서 확인 가능
- 예: `https://...atlassian.net/wiki/spaces/ABC/pages/782407271/...`
  - → Page ID: `782407271`

### 5. 설정 저장
- **"설정 저장"** 버튼 클릭
- 서버 재시작

---

## ✅ 2단계: 테스트 질문으로 인증 완료

설정을 저장하고 서버를 시작한 후, **테스트 질문**을 통해 인증을 완료하세요.

### 테스트 질문 예시
Slack에서 KIRA에게 다음과 같이 질문하세요:

```
Confluence에서 최근 업데이트된 페이지 보여줘
```

또는 Jira를 사용하는 경우:
```
내게 할당된 Jira 이슈 보여줘
```

### 인증 과정
1. KIRA가 Atlassian에 **처음 접근**할 때 브라우저가 자동으로 열립니다
2. Atlassian 로그인 페이지에서 **계정으로 로그인**
3. **권한 승인 화면**에서:
   - Confluence 읽기/쓰기
   - Jira 읽기/쓰기
4. **"Accept"** 클릭
5. 인증 완료 후 **브라우저를 닫아도 됩니다**
6. Slack으로 돌아가면 KIRA가 결과를 응답합니다

::: warning KIRA가 실행 중인 컴퓨터에서 인증
브라우저는 **KIRA가 실행 중인 컴퓨터**에서 열립니다. 본인 컴퓨터에서 실행 중이라면 바로 인증하면 됩니다.
:::

::: tip 한 번만 인증하면 됩니다
OAuth 토큰은 안전하게 저장되며, 다음부터는 자동으로 인증됩니다.
토큰 만료 시 자동으로 갱신됩니다.
:::

---

## 🎯 사용 예시

### Confluence 페이지 검색
```
사용자: Confluence에서 "API 문서" 검색해줘
KIRA: [Confluence 검색]
      1. API 사용 가이드
      2. REST API 문서
      3. GraphQL API 레퍼런스
```

### Confluence 페이지 읽기
```
사용자: "API 사용 가이드" 페이지 내용 보여줘
KIRA: [Confluence 조회]
      # API 사용 가이드

      ## 개요
      ...
```

### Confluence 페이지 생성
```
사용자: Confluence에 페이지 만들어줘
      제목: 신규 기능 설명
      내용: ## 기능 개요...
KIRA: [Confluence 생성] 페이지를 생성했습니다.
      https://...atlassian.net/wiki/spaces/.../pages/123456
```

### Jira 이슈 조회
```
사용자: 내게 할당된 Jira 이슈 보여줘
KIRA: [Jira 조회]
      1. ABC-123: 로그인 버그 수정
      2. ABC-124: 새 기능 개발
```

### Jira 이슈 생성
```
사용자: Jira 이슈 만들어줘
      프로젝트: ABC
      제목: UI 개선 필요
      설명: 메인 페이지 UI 개선이 필요합니다
KIRA: [Jira 생성] 이슈 ABC-125를 생성했습니다.
```

### Jira 이슈 상태 변경
```
사용자: ABC-123 이슈를 "In Progress"로 변경해줘
KIRA: [Jira 업데이트] ABC-123의 상태를 변경했습니다.
```

---

## 🔧 문제해결

### OAuth 브라우저가 열리지 않음
- 방화벽에서 port 8000 차단 확인
- 웹 인터페이스가 활성화되었는지 확인
- 로그에서 에러 메시지 확인

### "Site URL is invalid"
- ATLASSIAN_CONFLUENCE_SITE_URL이 올바른지 확인
- URL 끝에 슬래시(/) 제거
- 프로토콜(https://) 포함 확인

### "Permission denied"
- Atlassian 계정 권한 확인
- Confluence/Jira 접근 권한 확인
- OAuth 승인이 완료되었는지 확인

### 특정 Space/Project에 접근 불가
- 해당 Space/Project의 멤버인지 확인
- 읽기/쓰기 권한이 있는지 확인
- 관리자에게 권한 요청

---

## 💡 팁

### Page ID 찾는 방법
1. Confluence 페이지 열기
2. 우측 상단 **"..."** 메뉴 클릭
3. **"Page Information"** 클릭
4. URL에서 Page ID 확인
   - 예: `.../pages/pageInfo.action?pageId=782407271`

### Space Key 찾는 방법
1. Confluence Space 홈 열기
2. URL 확인: `https://.../wiki/spaces/ABC/...`
   - Space Key: `ABC`

### Project Key 찾는 방법
1. Jira 프로젝트 열기
2. 이슈 번호 확인: `ABC-123`
   - Project Key: `ABC`

### 효과적인 사용
- 페이지/이슈 제목을 명확히 지정
- Space/Project Key 사용으로 빠른 검색
- 템플릿 활용하여 일관성 유지

### Rovo MCP 특징
- **통합 검색**: Confluence와 Jira를 한 번에 검색
- **자동 OAuth**: 별도 토큰 발급 불필요
- **실시간 동기화**: 최신 데이터 자동 반영

---

## 🔐 보안 및 권한

### OAuth Scopes
Atlassian Rovo MCP가 요청하는 권한:
- **Confluence**:
  - `read:confluence-content.all`
  - `write:confluence-content`
  - `read:confluence-space.summary`
- **Jira**:
  - `read:jira-work`
  - `write:jira-work`
  - `read:jira-user`

### 권한 관리
- 필요한 Space/Project만 접근
- 민감한 정보는 별도 관리
- 정기적으로 OAuth 토큰 검토

### Self-hosted
회사 내부 Atlassian Server를 사용하는 경우:
- Server/Data Center 버전 호환성 확인
- 네트워크 접근 권한 확인
- IT 관리자와 협의
