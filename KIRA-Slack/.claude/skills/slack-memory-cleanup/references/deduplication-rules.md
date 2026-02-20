# Deduplication Rules - 중복 탐지 및 병합 규칙

이 문서는 메모리 파일의 중복을 탐지하고 병합하는 규칙을 정의합니다.

## 중복 유형

### Type 1: 동일인 다른 파일명 (users/)

**예시**:
```
users/
├── 전지호 (Jiho Jeon).md        ← email: batteryho@krafton.com
├── 전지호 - 이메일 분석.md       ← email: batteryho@krafton.com
└── Jiho_Jeon.md                 ← email: batteryho@krafton.com
```

**탐지 기준**:
1. `email` 필드가 동일
2. `user_id` 필드가 동일
3. 이름이 유사 (한글명/영문명 매칭)

**탐지 방법**:
```python
# 메타데이터에서 email 추출
for file in users_folder:
    metadata = parse_yaml_frontmatter(file)
    email = metadata.get('email')
    # email 기준으로 그룹핑
```

---

### Type 2: 동일 채널 다른 파일명 (channels/)

**예시**:
```
channels/
├── C08G76BB8JK_my-daily-scrum.md   ← channel_id: C08G76BB8JK
└── my-daily-scrum 채널.md           ← channel_id: C08G76BB8JK
```

**탐지 기준**:
1. `channel_id` 필드가 동일
2. `channel_name`이 동일

---

### Type 3: 동일 내용 다른 파일명

**예시**:
```
projects/
├── PUBG 벤틀리 스페셜 차량 제작 스펙.md
└── Bentley Special Vehicle Production Specification.md
```

**탐지 기준**:
1. 파일 내용이 90% 이상 유사
2. 메타데이터의 `project_id`, `related_to` 등이 동일
3. 한글/영문 버전

---

### Type 4: 버전 중복

**예시**:
```
projects/
├── 프로젝트_계획.md
├── 프로젝트_계획_v1.md
└── 프로젝트_계획_v2.md
```

**탐지 기준**:
1. 파일명에 `_v{N}` 패턴
2. 기본 파일명이 동일

---

## 중복 탐지 알고리즘

### Step 1: 메타데이터 기반 그룹핑

```python
def find_duplicates_by_metadata(folder):
    groups = {}

    for file in folder:
        metadata = parse_frontmatter(file)

        # users/ 폴더
        if folder == 'users':
            key = metadata.get('email') or metadata.get('user_id')

        # channels/ 폴더
        elif folder == 'channels':
            key = metadata.get('channel_id')

        # projects/ 폴더
        elif folder == 'projects':
            key = metadata.get('project_id')

        if key:
            groups.setdefault(key, []).append(file)

    # 2개 이상인 그룹 = 중복
    return {k: v for k, v in groups.items() if len(v) > 1}
```

### Step 2: 파일명 패턴 분석

```python
def find_duplicates_by_filename(folder):
    import re

    patterns = {}

    for file in folder:
        # _v{N} 패턴 제거
        base_name = re.sub(r'_v\d+\.md$', '.md', file)
        # 날짜 패턴 제거 (선택적)
        base_name = re.sub(r'_\d{8}\.md$', '.md', base_name)

        patterns.setdefault(base_name, []).append(file)

    return {k: v for k, v in patterns.items() if len(v) > 1}
```

### Step 3: 내용 유사도 분석 (고급)

```python
def find_similar_content(folder, threshold=0.9):
    # 내용이 90% 이상 유사한 파일 찾기
    # 한글/영문 번역 버전 탐지
    pass
```

---

## 병합 규칙

### Rule 1: 프로필 파일 병합 (users/, channels/)

**원칙**: 1 entity = 1 file

**병합 순서**:
1. 가장 최근 `updated` 파일을 기준으로
2. 다른 파일들의 고유 정보를 추가
3. 메타데이터 병합 (최신 값 우선)

**예시**:
```yaml
# 파일 A (2025-12-08 업데이트)
---
email: batteryho@krafton.com
team: AI Service Dept
tags: [developer]
---
내용 A

# 파일 B (2025-11-26 업데이트)
---
email: batteryho@krafton.com
communication_style: Task-oriented
tags: [jira, confluence]
---
내용 B

# 병합 결과
---
email: batteryho@krafton.com
team: AI Service Dept  # A에서
communication_style: Task-oriented  # B에서 추가
tags: [developer, jira, confluence]  # 합집합
updated: 2025-12-08
---
내용 A
(필요시 내용 B의 고유 정보 추가)
```

---

### Rule 2: 작업 기록 분리 (users/ → tasks/)

**원칙**: 프로필이 아닌 작업 기록은 분리

**탐지 기준**:
- 파일명에 날짜가 포함
- 파일명에 "분석", "보고서", "작업" 등 포함
- 내용이 특정 날짜/작업에 대한 기록

**액션**:
```
users/전지호 - 이메일 분석.md
  ↓ 이동
tasks/전지호 - 이메일 분석.md
```

---

### Rule 3: 버전 파일 통합

**원칙**: 최신 버전만 유지

**액션**:
```
파일_v1.md → 삭제
파일_v2.md → 삭제
파일_v3.md → 파일.md로 이름 변경 (최신 버전)
```

**예외**:
- 이전 버전에만 있는 중요 정보가 있으면 최신 버전에 병합

---

### Rule 4: 한글/영문 버전 통합

**원칙**: 하나의 파일에 양쪽 내용 포함

**액션**:
```yaml
# 병합 결과
---
title: "PUBG 벤틀리 스페셜 차량 제작 스펙"
title_en: "Bentley Special Vehicle Production Specification"
---

# PUBG 벤틀리 스페셜 차량 제작 스펙
# Bentley Special Vehicle Production Specification

(한글 내용)

---

(영문 내용, 필요시)
```

---

## 병합 실행 가이드

### Step 1: 기준 파일 선정

다음 우선순위로 기준 파일 선정:
1. `updated` 타임스탬프가 가장 최신
2. 내용이 가장 완전 (파일 크기)
3. 메타데이터가 가장 풍부
4. 파일명이 가장 표준적 (예: `{ID}_{이름}.md`)

### Step 2: 메타데이터 병합

```yaml
# 병합 규칙
- 단일 값 필드: 기준 파일 값 사용, 없으면 다른 파일에서
- 리스트 필드 (tags, participants): 합집합
- 타임스탬프: created는 가장 오래된 것, updated는 현재 시각
```

### Step 3: 내용 병합

```markdown
# 기준 파일 내용 유지

## 추가 정보
(다른 파일에만 있는 고유 정보)
```

### Step 4: 원본 파일 처리

- 병합된 원본 파일들은 삭제
- 또는 백업 폴더로 이동: `{memories_path}/.archive/`

---

## 실제 예시

### 예시 1: 전지호 파일 정리

**Before**:
```
users/
├── 전지호 (Jiho Jeon).md              # 프로필
├── 전지호 (Jiho Jeon) - 이메일 분석.md  # 작업 기록
├── 전지호 - AI 보고서.md               # 작업 기록
└── AI Future Discussion with Jiho Jeon.md  # 작업 기록
```

**After**:
```
users/
└── 전지호 (Jiho Jeon).md              # 프로필 (병합된 메타데이터)

tasks/
├── 전지호 - 이메일 분석 2025-11-26.md
├── 전지호 - AI 보고서 2025-12-08.md
└── AI Future Discussion 2025-12-08.md
```

---

### 예시 2: 김세린 파일 병합

**Before**:
```yaml
# 김세린 (Serin Kim).md
---
email: serin.kim@krafton.com
team: Legal/Compliance Team
tags: [legal, compliance]
---

# Serin_Kim_김세린.md
---
email: 김세린@krafton.com  # 잘못된 이메일
role: Confluence 문서 관리자
tags: [confluence, documentation]
---
```

**After**:
```yaml
# 김세린 (Serin Kim).md
---
email: serin.kim@krafton.com  # 올바른 이메일 유지
team: Legal/Compliance Team
role: Confluence 문서 관리자  # 추가
tags: [legal, compliance, confluence, documentation]  # 합집합
updated: 2025-12-16
---

# 김세린 (Serin Kim)

## 기본 정보
(양쪽 파일의 정보 통합)

## 업무 특성
(양쪽 파일의 정보 통합)
```

---

## 주의사항

### 병합 전 확인
- [ ] 정말 같은 entity인가? (동명이인 주의)
- [ ] 양쪽 파일의 고유 정보를 모두 보존했는가?
- [ ] 메타데이터 충돌은 올바르게 해결했는가?

### 병합 금지 케이스
- 같은 이름이지만 다른 사람 (동명이인)
- email/user_id가 다른 경우
- 확실하지 않은 경우 → 사용자에게 확인 요청

### 병합 후 검증
- 결과 파일의 메타데이터가 유효한가?
- `related_to`로 참조하던 파일들 업데이트 필요한가?
- index.md 업데이트 필요 
