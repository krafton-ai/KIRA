# Misclassification Rules - 오분류 탐지 및 이동 규칙

이 문서는 잘못된 폴더에 저장된 파일을 탐지하고 올바른 위치로 이동하는 규칙을 정의합니다.

## 오분류 탐지 기준

### 폴더별 올바른 파일 특성

| 폴더 | 올바른 파일 | 잘못된 파일 |
|------|-------------|-------------|
| `users/` | 유저 프로필 (1인당 1파일) | 작업 기록, 분석 결과 |
| `channels/` | 채널 프로필 (채널당 1파일) | 작업 기록, 성공 사례 |
| `projects/` | 프로젝트 정보 | 일회성 작업 |
| `tasks/` | 작업 기록, 완료 내역 | 프로필, 프로젝트 정보 |
| `decisions/` | 의사결정 기록 | 작업 기록 |
| `meetings/` | 회의록 | 작업 기록 |
| `misc/` | 분류 안 된 것 | (기본값이므로 다 가능) |

---

## Pattern 1: channels/ 오분류

### 올바른 channels/ 파일

```yaml
# 채널 프로필 파일
---
type: channel
channel_id: C08G76BB8JK
channel_name: my-daily-scrum
guidelines:
  tone: professional
  response_time: 1시간 이내
---

# 채널 가이드라인, 참여자, 커뮤니케이션 규칙 등
```

**특징**:
- `channel_id` 있음
- 파일명이 `{channel_id}_{name}.md` 형식
- 내용이 채널 설명, 가이드라인, 규칙

### 잘못된 channels/ 파일

```yaml
# 작업 기록 - tasks/로 가야 함
---
type: task  # 또는 type이 없음
---

# Jira 티켓 조회 성공 - 전지호 님 할당 이슈
```

**탐지 기준**:
- 파일명에 "성공", "실패", "완료", "조회", "작업" 포함
- `channel_id` 없음
- `type`이 `channel`이 아님
- 내용이 일회성 작업 결과

### 실제 오분류 예시 (현재 상태)

```
channels/
├── C08G76BB8JK_my-daily-scrum.md     ✅ 올바름
├── Confluence 멘션 후속 조치 완료.md   ❌ → tasks/
├── Jira 티켓 조회 성공.md             ❌ → tasks/
├── OpenAI KRAFTON 조직 초대 처리.md   ❌ → tasks/
├── 메일 조회 작업 성공.md             ❌ → tasks/
└── KRIS API 식당 메뉴 조회 성공.md    ❌ → tasks/
```

---

## Pattern 2: users/ 오분류

### 올바른 users/ 파일

```yaml
# 유저 프로필 파일
---
type: user
user_id: U094PFB331N
email: user@company.com
user_name: 홍길동
team: Engineering
---

# 유저 프로필, 커뮤니케이션 스타일, 업무 패턴 등
```

**특징**:
- `user_id` 또는 `email` 있음
- 파일명이 `{이름}.md` 또는 `{user_id}_{이름}.md` 형식
- 내용이 프로필, 선호도, 업무 스타일

### 잘못된 users/ 파일

```yaml
# 작업 기록 - tasks/로 가야 함
---
type: user
user_name: 전지호
---

# 전지호 - 이메일 분석 (2025-11-25)
## 2025-11-25 이메일 분석
... (특정 날짜의 작업 기록)
```

**탐지 기준**:
- 파일명에 날짜, "분석", "보고서", "작업" 포함
- 내용이 특정 날짜/작업에 대한 기록
- 프로필 정보보다 작업 기록이 주 내용

### 실제 오분류 예시 (현재 상태)

```
users/
├── 전지호 (Jiho Jeon).md                    ✅ 프로필
├── 전지호 (Jiho Jeon) - 이메일 분석.md        ❌ → tasks/
├── 전지호 (Jiho Jeon) - 이메일 분석 취합.md   ❌ → tasks/
├── 전지호 - AI의 미래 질문 및 상세 보고서.md   ❌ → tasks/ 또는 misc/
├── 전지호 - PUBG KPI 대시보드 분석.md        ❌ → tasks/
└── AI Future Discussion with Jiho Jeon.md  ❌ → misc/
```

---

## Pattern 3: projects/ 오분류

### 올바른 projects/ 파일

```yaml
# 프로젝트 정보 파일
---
type: project
project_id: PROJ-001
status: in_progress
milestones: [...]
---

# 프로젝트 개요, 목표, 진행 상황, 마일스톤 등
```

### 잘못된 projects/ 파일

```yaml
# 일회성 작업 - tasks/로 가야 함
---
type: task
---

# 특정 작업 결과 (프로젝트 전체가 아닌)
```

**탐지 기준**:
- 프로젝트 전체가 아닌 단일 작업
- `status`, `milestones` 없음
- 파일명에 날짜 포함

---

## Pattern 4: misc/ → 다른 폴더

### misc/에서 재분류 가능한 것들

```
misc/
├── Claude API 이미지 크기 제한 에러.md    → resources/ (참고자료)
├── Chat System Specification.md         → projects/ (스펙 문서)
├── PUBG KPI 대시보드 이미지 요청.md       → tasks/
└── Douyin Platform PUBG Weekly Report.md → projects/ 또는 external/
```

**재분류 기준**:
- 키워드 분석 (project, spec, guide → projects/, resources/)
- 반복적으로 참조되는 것 → resources/
- 외부 정보 → external/

---

## 이동 실행 가이드

### Step 1: 오분류 파일 탐지

```bash
# channels/ 검사
for file in channels/*.md:
    if filename not starts with "C" (channel_id):
        likely_misclassified

    metadata = parse_frontmatter(file)
    if metadata.type != 'channel':
        likely_misclassified
```

### Step 2: 올바른 위치 결정

```python
def determine_correct_folder(file, current_folder):
    metadata = parse_frontmatter(file)
    filename = file.name
    content = file.read()

    # 파일명 기반 판단
    if any(word in filename for word in ['성공', '실패', '완료', '조회', '작업']):
        return 'tasks'

    if any(word in filename for word in ['분석', '보고서']):
        return 'tasks'

    # 메타데이터 기반 판단
    if metadata.get('type') == 'task':
        return 'tasks'

    if metadata.get('type') == 'meeting':
        return 'meetings'

    # 내용 기반 판단
    if '회의록' in content or '참석자' in content:
        return 'meetings'

    if '결정사항' in content or '승인' in content:
        return 'decisions'

    return 'misc'  # 확실하지 않으면 misc
```

### Step 3: 파일 이동

```bash
# 이동 전 확인
echo "Moving: {source} → {destination}"

# 이동
mv "{memories_path}/{source_folder}/{filename}" \
   "{memories_path}/{dest_folder}/{filename}"

# 메타데이터 업데이트 (category 필드)
# 파일 내용에서 category: 값 변경
```

### Step 4: 참조 업데이트

```bash
# related_to에서 이 파일을 참조하는 다른 파일들 찾기
grep -r "related_to.*{old_path}" {memories_path}/

# 참조 경로 업데이트
sed -i 's|{old_path}|{new_path}|g' {referencing_file}
```

---

## 폴더별 이동 매트릭스

| From → To | users | channels | projects | tasks | decisions | meetings | misc |
|-----------|-------|----------|----------|-------|-----------|----------|------|
| **users** | - | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **channels** | ❌ | - | ❌ | ✅ | ❌ | ❌ | ✅ |
| **projects** | ❌ | ❌ | - | ✅ | ✅ | ✅ | ✅ |
| **tasks** | ❌ | ❌ | ✅ | - | ✅ | ✅ | ✅ |
| **misc** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |

**✅ = 이동 가능**, **❌ = 이동 비권장**

---

## 실행 예시

### 예시 1: channels/ 정리

**현재 상태**:
```
channels/
├── C08G76BB8JK_my-daily-scrum.md
├── Confluence 멘션 후속 조치 완료 - 2025-12-08.md
├── Jira 티켓 조회 성공 - 전지호 님 할당 이슈.md
├── OpenAI KRAFTON 조직 초대 처리 - 전지호.md
├── 메일 조회 작업 성공 - 2025-12-08.md
└── KRIS API 식당 메뉴 조회 성공 사례.md
```

**실행**:
```bash
# 1. 오분류 탐지
misclassified = [
    "Confluence 멘션 후속 조치 완료 - 2025-12-08.md",
    "Jira 티켓 조회 성공 - 전지호 님 할당 이슈.md",
    "OpenAI KRAFTON 조직 초대 처리 - 전지호.md",
    "메일 조회 작업 성공 - 2025-12-08.md",
    "KRIS API 식당 메뉴 조회 성공 사례.md"
]

# 2. 이동
for file in misclassified:
    mv "channels/{file}" "tasks/{file}"

# 3. 메타데이터 업데이트
for file in moved_files:
    update_category_metadata(file, 'tasks')
```

**결과**:
```
channels/
└── C08G76BB8JK_my-daily-scrum.md  ← 채널 프로필만 남음

tasks/
├── (기존 파일들...)
├── Confluence 멘션 후속 조치 완료 - 2025-12-08.md
├── Jira 티켓 조회 성공 - 전지호 님 할당 이슈.md
├── OpenAI KRAFTON 조직 초대 처리 - 전지호.md
├── 메일 조회 작업 성공 - 2025-12-08.md
└── KRIS API 식당 메뉴 조회 성공 사례.md
```

---

### 예시 2: users/ 정리

**현재 상태**:
```
users/
├── 전지호 (Jiho Jeon).md                    ← 프로필 (유지)
├── 전지호 (Jiho Jeon) - 이메일 분석.md        ← 작업 기록
├── 전지호 - AI의 미래 질문 및 상세 보고서.md   ← 작업 기록
└── AI Future Discussion with Jiho Jeon.md  ← 작업 기록
```

**실행**:
```bash
# 프로필 파일 식별 (가장 기본적인 이름)
profile_file = "전지호 (Jiho Jeon).md"

# 나머지는 작업 기록 → tasks/로 이동
mv "users/전지호 (Jiho Jeon) - 이메일 분석.md" \
   "tasks/전지호 - 이메일 분석 2025-11-26.md"

mv "users/전지호 - AI의 미래 질문 및 상세 보고서.md" \
   "tasks/전지호 - AI 보고서 2025-12-08.md"

mv "users/AI Future Discussion with Jiho Jeon.md" \
   "misc/AI Future Discussion 2025-12-08.md"
```

**결과**:
```
users/
└── 전지호 (Jiho Jeon).md  ← 프로필만 남음

tasks/
├── 전지호 - 이메일 분석 2025-11-26.md
└── 전지호 - AI 보고서 2025-12-08.md

misc/
└── AI Future Discussion 2025-12-08.md
```

---

## 주의사항

### 이동 전 확인
- [ ] 다른 파일에서 `related_to`로 참조하고 있지 않은가?
- [ ] 이동할 폴더에 같은 파일명이 없는가?
- [ ] 파일 내용이 목적지 폴더에 적합한가?

### 이동 금지 케이스
- 확실하지 않은 경우
- `related_to`로 많이 참조되는 파일
- `important` 태그가 있는 파일

### 이동 후 필수 작업
- 메타데이터의 `category` 필드 업데이트
- `related_to`로 참조하던 파일들 경로 업데이트
- index.md 업데이트 
