# GitLab 연동

GitLab API를 연동하면 KIRA가 코드 저장소를 관리할 수 있습니다.

## 📋 준비물

- GitLab 계정 (gitlab.com 또는 Self-hosted)
- Personal Access Token

---

## 🔑 1단계: Access Token 발급

### 1. GitLab 접속
- [GitLab.com](https://gitlab.com) 또는 회사 GitLab 서버

### 2. Personal Access Token 생성
1. 우측 상단 프로필 아이콘 클릭
2. **"Edit Profile"** 선택
3. 왼쪽 메뉴에서 **"Access Tokens"** 클릭
4. **"Add new token"** 클릭

### 3. Token 설정
- **Token name**: `KIRA Bot` (원하는 이름)
- **Expiration date**: 만료일 설정 (선택사항)
- **Select scopes**: 다음 권한 선택
  - ✅ `api` - 전체 API 접근
  - ✅ `read_repository` - 저장소 읽기
  - ✅ `write_repository` - 저장소 쓰기

### 4. Token 생성 및 복사
1. **"Create personal access token"** 클릭
2. 생성된 토큰 복사 (한 번만 표시됨!)
3. 안전한 곳에 보관

::: warning Token 보안
Personal Access Token은 한 번만 표시됩니다.
복사하지 않으면 다시 볼 수 없으므로 안전하게 보관하세요.
:::

---

## ⚙️ 2단계: KIRA 설정

### 1. KIRA 앱 실행
환경변수 설정 탭을 엽니다.

### 2. GitLab 섹션 찾기
**MCP 설정** > **GitLab**

### 3. 설정 활성화
- 토글 스위치를 **켜기**로 변경

### 4. 정보 입력
- **GITLAB_API_URL**: GitLab 서버 URL
  - GitLab.com: `https://gitlab.com`
  - Self-hosted: `https://git.company.com`
- **GITLAB_PERSONAL_ACCESS_TOKEN**: 앞서 복사한 Access Token

### 5. 설정 저장
- **"설정 저장"** 버튼 클릭
- 서버 재시작

---

## ✅ 3단계: 테스트

Slack에서 KIRA에게 물어보세요:

```
내 GitLab 프로젝트 목록 보여줘
```

```
프로젝트 "myapp"의 최근 커밋 알려줘
```

KIRA가 GitLab API를 통해 정보를 가져옵니다.

---

## 🎯 사용 예시

### 프로젝트 조회
```
사용자: GitLab에 있는 프로젝트 목록 보여줘
KIRA: [GitLab 조회]
      1. project-alpha
      2. project-beta
      3. my-app
```

### 이슈 관리
```
사용자: "my-app" 프로젝트에 이슈 생성해줘: "버그 수정 필요"
KIRA: [GitLab 이슈 생성] 이슈 #42를 생성했습니다.
```

### 커밋 조회
```
사용자: "my-app"의 최근 커밋 5개 보여줘
KIRA: [GitLab 조회]
      1. fix: 로그인 버그 수정
      2. feat: 새로운 기능 추가
      ...
```

### MR(Merge Request) 조회
```
사용자: 내가 올린 MR 목록 보여줘
KIRA: [GitLab 조회]
      1. MR !123: 기능 개선
      2. MR !124: 버그 수정
```

---

## 🔧 문제해결

### "Authentication failed"
- Access Token이 올바른지 확인
- Token이 만료되지 않았는지 확인
- GitLab에서 Token이 활성화되었는지 확인

### "API URL is incorrect"
- GITLAB_API_URL이 올바른지 확인
- Self-hosted인 경우 URL이 정확한지 확인
- 프로토콜 포함 여부 확인 (https://)

### "Permission denied"
- Access Token의 권한(scopes)를 확인
- `api`, `read_repository`, `write_repository` 권한 필요
- 프로젝트 접근 권한 확인

### 특정 프로젝트에 접근 불가
- 해당 프로젝트의 멤버인지 확인
- 프로젝트가 비공개(Private)인 경우 권한 확인

---

## 💡 팁

### Self-hosted GitLab
회사 내부 GitLab 서버를 사용하는 경우:
- GITLAB_API_URL에 회사 GitLab 주소 입력
- 예: `https://git.company.com`

### Token 관리
- Token 이름을 명확하게 설정 (`KIRA Bot`)
- 만료일을 설정하여 보안 강화
- 정기적으로 Token 갱신

### 권한 최소화
필요한 권한만 부여:
- 읽기 전용: `read_repository`만 선택
- 쓰기 필요: `write_repository` 추가
- 전체 API: `api` 선택

### 효과적인 사용
- 프로젝트 이름을 명확히 지정
- 브랜치 이름 정확히 입력
- 이슈 번호로 빠른 조회
