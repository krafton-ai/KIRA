# Tableau

Tableau MCP를 연동하면 KIRA가 Tableau 대시보드와 데이터를 관리할 수 있습니다.

## 📋 준비물

- Tableau Server 또는 Tableau Cloud 계정
- Personal Access Token (PAT) 발급 권한

---

## 🎯 주요 기능

### 데이터 조회
- Workbook 목록 조회
- Dashboard 조회
- View (시트) 조회
- Data Source 정보 확인

### 데이터 관리
- Workbook 게시
- Dashboard 업데이트
- 권한 관리
- 메타데이터 조회

---

## ⚙️ 1단계: Personal Access Token 발급

### 1. Tableau Server 로그인
브라우저에서 Tableau Server 또는 Tableau Cloud에 로그인합니다.

### 2. 계정 설정 열기
- 우측 상단 프로필 아이콘 클릭
- **"My Account Settings"** 선택

### 3. Personal Access Tokens 섹션 이동
- 좌측 메뉴에서 **"Personal Access Tokens"** 클릭

### 4. 새 토큰 생성
1. **"Create new token"** 버튼 클릭
2. **Token Name** 입력
   - 예: `KIRA Bot Token`
3. **"Create"** 클릭
4. **Token Secret** 복사
   - ⚠️ 이 화면에서만 확인 가능합니다!
   - 안전한 곳에 저장하세요

::: warning 중요
Token Secret은 생성 시 한 번만 표시됩니다. 분실 시 새로 발급받아야 합니다.
:::

---

## ⚙️ 2단계: KIRA 설정

### 1. KIRA 앱 실행
환경변수 설정 탭을 엽니다.

### 2. Tableau 섹션 찾기
**MCP 설정** > **Tableau**

### 3. 설정 활성화
- 토글 스위치를 **켜기**로 변경

### 4. 서버 정보 입력

**TABLEAU_SERVER**
- Tableau Server URL을 입력합니다
- **Tableau Server**: `https://tableau.company.com`
- **Tableau Cloud**: `https://10ax.online.tableau.com`

::: tip URL 형식
- 프로토콜(`https://`) 포함
- URL 끝에 슬래시(`/`) 제거
:::

**TABLEAU_SITE_NAME**
- Site 이름을 입력합니다
- **Default Site**: 비워두세요
- **특정 Site**: Site URL Name 입력 (예: `marketing`)
  - Site URL이 `https://tableau.com/#/site/marketing`인 경우 → `marketing`

**TABLEAU_PAT_NAME**
- 1단계에서 생성한 Token Name 입력
- 예: `KIRA Bot Token`

**TABLEAU_PAT_VALUE**
- 1단계에서 복사한 Token Secret 입력
- 예: `XYZ123...`

### 5. 설정 저장
- **"설정 저장"** 버튼 클릭
- 서버 재시작

---

## 🎯 사용 예시

### Workbook 목록 조회
```
사용자: Tableau에 있는 Workbook 목록 보여줘
KIRA: [Tableau 조회]
      1. Sales Dashboard
      2. Marketing Analytics
      3. HR Metrics
```

### Dashboard 조회
```
사용자: "Sales Dashboard"의 대시보드 정보 알려줘
KIRA: [Tableau 조회]
      Workbook: Sales Dashboard
      Owner: John Doe
      Created: 2024-01-15
      Views:
      - Sales Overview
      - Regional Performance
      - Monthly Trends
```

### 데이터 업데이트
```
사용자: "Marketing Analytics" Workbook 새로 고침해줘
KIRA: [Tableau 업데이트] Workbook을 새로 고침했습니다.
      마지막 업데이트: 2025-01-21 14:30:00
```

---

## 🔧 문제해결

### "Invalid credentials"
- **PAT Name**과 **PAT Value**가 정확한지 확인
- Tableau Server에서 토큰이 삭제되지 않았는지 확인
- 토큰 만료 여부 확인 (필요 시 재발급)

### "Site not found"
- **TABLEAU_SITE_NAME**이 올바른지 확인
- Default Site는 비워두기
- Site URL Name 확인 (Display Name이 아님)

### "Permission denied"
- Tableau 계정의 권한 확인
- 해당 Workbook/Dashboard 접근 권한 확인
- Site Admin 권한이 필요한 작업인지 확인

### "Server URL invalid"
- TABLEAU_SERVER URL이 올바른지 확인
- 프로토콜(`https://`) 포함 확인
- 네트워크/방화벽 설정 확인

---

## 💡 팁

### Site Name 찾는 방법
1. Tableau Server/Cloud에 로그인
2. URL 확인:
   - `https://tableau.com/#/site/marketing/home`
   - Site Name: `marketing`
3. Default Site인 경우 URL에 `/site/`가 없음

### 효과적인 사용
- Workbook/Dashboard 이름을 정확히 지정
- Project 구조를 활용하여 체계적으로 관리
- 정기적인 데이터 새로 고침 스케줄 설정

### Personal Access Token 관리
- **유효 기간**: 토큰 생성 시 설정 가능
- **보안**: 토큰은 암호처럼 관리
- **취소**: 필요 시 Tableau Server에서 즉시 취소 가능
- **갱신**: 만료 전에 새 토큰 발급 권장

---

## 🔐 보안 및 권한

### Token 권한
Personal Access Token은 발급한 사용자의 모든 권한을 상속받습니다:
- Workbook 읽기/쓰기
- Dashboard 관리
- Data Source 접근
- 사용자가 속한 Project/Site의 모든 권한

### 최소 권한 원칙
- 봇 전용 Tableau 계정 생성 권장
- 필요한 최소 권한만 부여
- 민감한 데이터는 별도 Project로 분리

### Token 관리
- 정기적으로 토큰 교체 (예: 3개월마다)
- 사용하지 않는 토큰은 즉시 삭제
- 토큰 유출 의심 시 즉시 취소하고 재발급

### Tableau Server vs Cloud
- **Tableau Server**: 회사 내부 서버, IT 팀과 협의 필요
- **Tableau Cloud**: Tableau 호스팅, 인터넷 연결 필요

---

## 📚 참고 자료

- [Tableau REST API 문서](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api.htm)
- [Personal Access Tokens 관리](https://help.tableau.com/current/server/en-us/security_personal_access_tokens.htm)
- [Tableau MCP Server GitHub](https://github.com/tableau/mcp-server)
