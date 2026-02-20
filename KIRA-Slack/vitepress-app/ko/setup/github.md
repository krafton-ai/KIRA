# GitHub 연동

GitHub API를 연동하면 KIRA가 코드 저장소를 관리할 수 있습니다.

## 📋 준비물

- GitHub 계정
- Personal Access Token (Classic 또는 Fine-grained)

---

## 🔑 1단계: Personal Access Token 발급

### 1. GitHub 접속
[GitHub.com](https://github.com)에 로그인

### 2. Settings 이동
1. 우측 상단 프로필 아이콘 클릭
2. **"Settings"** 선택
3. 왼쪽 메뉴 하단 **"Developer settings"** 클릭

### 3. Token 생성
1. **"Personal access tokens"** > **"Tokens (classic)"** 클릭
2. **"Generate new token"** > **"Generate new token (classic)"** 선택

::: tip Fine-grained Token
더 세밀한 권한 제어가 필요하다면 **Fine-grained tokens**를 사용할 수 있습니다.
:::

### 4. Token 설정 (Classic)
- **Note**: `KIRA Bot` (원하는 이름)
- **Expiration**: 만료일 설정 (90일 권장)
- **Select scopes**: 다음 권한 선택
  - ✅ `repo` - 저장소 전체 접근
  - ✅ `read:packages` - 패키지 읽기
  - ✅ `read:org` - 조직 정보 읽기 (선택사항)
  - ✅ `workflow` - GitHub Actions 관리 (선택사항)

### 5. Token 생성 및 복사
1. **"Generate token"** 클릭
2. 생성된 토큰 복사 (`ghp_`로 시작)
3. 안전한 곳에 보관

::: warning Token 보안
Personal Access Token은 한 번만 표시됩니다.
복사하지 않으면 다시 볼 수 없으므로 안전하게 보관하세요.
:::

---

## ⚙️ 2단계: KIRA 설정

### 1. KIRA 앱 실행
환경변수 설정 탭을 엽니다.

### 2. GitHub 섹션 찾기
**MCP 설정** > **GitHub**

### 3. 설정 활성화
- 토글 스위치를 **켜기**로 변경

### 4. 정보 입력
- **GITHUB_PERSONAL_ACCESS_TOKEN**: 앞서 복사한 Personal Access Token
  - Classic: `ghp_xxxxxxxxxxxx`
  - Fine-grained: `github_pat_xxxxxxxxxxxx`

### 5. 설정 저장
- **"설정 저장"** 버튼 클릭
- 서버 재시작

---

## ✅ 3단계: 테스트

Slack에서 KIRA에게 물어보세요:

```
내 GitHub 저장소 목록 보여줘
```

```
"myrepo" 저장소의 최근 이슈 알려줘
```

KIRA가 GitHub API를 통해 정보를 가져옵니다.

---

## 🎯 사용 예시

### 저장소 조회
```
사용자: GitHub에 있는 내 저장소 목록 보여줘
KIRA: [GitHub 조회]
      1. user/project-alpha
      2. user/project-beta
      3. user/my-app
```

### 이슈 관리
```
사용자: "my-app" 저장소에 이슈 생성해줘: "버그 수정 필요"
KIRA: [GitHub 이슈 생성] 이슈 #42를 생성했습니다.
      https://github.com/user/my-app/issues/42
```

### Pull Request 조회
```
사용자: 내가 올린 PR 목록 보여줘
KIRA: [GitHub 조회]
      1. PR #123: 기능 개선
         https://github.com/user/my-app/pull/123
      2. PR #124: 버그 수정
         https://github.com/user/my-app/pull/124
```

### 커밋 조회
```
사용자: "my-app"의 최근 커밋 5개 보여줘
KIRA: [GitHub 조회]
      1. fix: 로그인 버그 수정 (2시간 전)
      2. feat: 새로운 기능 추가 (5시간 전)
      3. docs: README 업데이트 (1일 전)
      ...
```

### GitHub Actions 확인
```
사용자: "my-app"의 최근 워크플로우 상태 알려줘
KIRA: [GitHub Actions 조회]
      ✅ CI/CD: 성공 (10분 전)
      ✅ Tests: 성공 (10분 전)
      ❌ Deploy: 실패 (5분 전)
```

---

## 🔧 문제해결

### "Authentication failed"
- Personal Access Token이 올바른지 확인
- Token이 만료되지 않았는지 확인
- GitHub에서 Token이 활성화되었는지 확인
- Token이 `ghp_` 또는 `github_pat_`로 시작하는지 확인

### "Permission denied"
- Token의 권한(scopes)을 확인
- `repo` 권한이 필요
- Private 저장소 접근 시 적절한 권한 필요

### "Repository not found"
- 저장소 이름을 정확히 입력 (`owner/repo` 형식)
- Private 저장소는 Token에 접근 권한이 있어야 함
- 조직(Organization) 저장소는 조직 권한 확인

### "Rate limit exceeded"
- GitHub API 요청 제한 초과
- 인증된 요청: 시간당 5,000회
- 1시간 후 자동 초기화
- [Rate Limit 확인](https://api.github.com/rate_limit)

---

## 💡 팁

### Token 권한 최소화
필요한 권한만 부여:
- **읽기 전용**: `repo` (public만), `read:org`
- **이슈/PR 관리**: `repo` 전체
- **Actions 관리**: `workflow` 추가

### Token 관리
- Token 이름을 명확하게 설정 (`KIRA Bot`)
- 만료일을 설정하여 보안 강화 (90일 권장)
- 정기적으로 Token 갱신
- 사용하지 않는 Token은 즉시 삭제

### Fine-grained Token 사용
더 세밀한 권한 제어:
- 특정 저장소에만 접근 허용
- 읽기/쓰기 권한 분리
- 만료일 자동 갱신 가능

### 효과적인 사용
- 저장소 이름을 `owner/repo` 형식으로 명확히 지정
- 이슈/PR 번호로 빠른 조회 (#123)
- 브랜치 이름 정확히 입력
- Labels과 Milestones 활용

### 보안 권장사항
- Token을 코드에 하드코딩하지 마세요
- Token을 Git 저장소에 커밋하지 마세요
- 의심스러운 활동 감지 시 즉시 Token 재발급
- GitHub Security Log 주기적 확인

---

## 🔗 관련 링크

- [GitHub Personal Access Tokens 생성](https://github.com/settings/tokens)
- [GitHub API 문서](https://docs.github.com/en/rest)
- [GitHub Copilot MCP Server](https://github.com/github/github-mcp-server)
- [Rate Limits 확인](https://api.github.com/rate_limit)
