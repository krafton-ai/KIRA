# Memory Retrieval Patterns

이 문서는 다양한 상황에서 메모리를 효과적으로 조회하는 패턴을 제공합니다.

## Pattern 1: Context-Based Retrieval

사용자의 질문이나 요청에 따라 필요한 컨텍스트를 파악하고 조회합니다.

### Step 1: 컨텍스트 분석

대화에서 다음 정보를 추출:
- **채널 정보**: channel_id, channel_name
- **언급된 사람**: 유저 이름, @mentions
- **프로젝트**: 프로젝트명, 약어
- **키워드**: 중요 주제, 작업명

### Step 2: Index 우선 확인

항상 먼저 `index.md`를 읽어서:
```bash
view {memories_path}/index.md
```

확인 사항:
- 전체 메모리 구조 파악
- 관련 카테고리 식별
- Recent Updates에서 최근 관련 정보 확인

### Step 3: 관련 파일 조회

식별된 카테고리에서 파일 검색:
```bash
# 채널 정보가 필요한 경우
view {memories_path}/channels/

# 특정 프로젝트 정보
view {memories_path}/projects/프로젝트명.md

# 특정 유저 정보
view {memories_path}/users/U123_김철수.md
```

## Pattern 2: Channel-Specific Memory

채널별 대화에서 필요한 메모리 조회 패턴입니다.

### 시나리오: 채널에서 질문 받음

```
User (in #마케팅팀): "지난 Q4 전략 논의 내용 정리해줘"
```

### 조회 순서:

1. **채널 프로필 확인 (가이드라인, 멤버)**
```bash
view {memories_path}/channels/
# C123_마케팅팀.md 프로필 파일 찾기
view {memories_path}/channels/C123_마케팅팀.md
# → 채널 가이드라인, 커뮤니케이션 스타일 확인
```

2. **Q4 전략 관련 주제 파일 확인**
```bash
# 프로젝트 파일에서 Q4 전략 논의 내용 찾기
view {memories_path}/projects/Q4전략.md
# 또는 decisions/ 폴더 확인
view {memories_path}/decisions/
```

3. **관련 회의록 확인**
```bash
view {memories_path}/meetings/
# Q4, 전략 관련 파일 찾기
```

### 응답 구성:
채널 컨텍스트 + 프로젝트 정보 + 회의 내용을 종합하여 답변

## Pattern 3: User-Specific Memory

특정 유저와의 상호작용에서 메모리 활용 패턴입니다.

### 시나리오: DM에서 요청 받음

```
User (@chulsoo, DM): "내 업무 현황 알려줘"
```

### 조회 순서:

1. **유저 프로필 확인**
```bash
view {memories_path}/users/
# U123_김철수.md 파일 찾기
view {memories_path}/users/U123_김철수.md
```

확인 사항:
- communication_style (답변 톤 조정)
- role, team (컨텍스트 이해)
- preferences (답변 형식)

2. **할당된 작업 확인**
```bash
view {memories_path}/tasks/ongoing/
# assignee: U123 인 파일들 찾기
```

3. **참여 중인 프로젝트 확인**
```bash
view {memories_path}/projects/
# participants에 U123 포함된 파일들
```

### 응답 구성:
유저 맞춤 톤 + 진행 중인 작업 + 프로젝트 상태

## Pattern 4: Project-Based Memory

프로젝트 관련 질문에 대한 조회 패턴입니다.

### 시나리오: 프로젝트 상태 문의

```
User: "신제품 런칭 프로젝트 어디까지 진행됐어?"
```

### 조회 순서:

1. **프로젝트 파일 직접 확인**
```bash
view {memories_path}/projects/
# "신제품" 키워드로 파일 찾기
view {memories_path}/projects/신제품런칭.md
```

2. **관련 의사결정 확인**
```bash
view {memories_path}/decisions/
# related_project: 신제품런칭 인 파일들
```

3. **최근 회의록 확인**
```bash
view {memories_path}/meetings/
# 프로젝트명 포함된 최근 회의록
```

4. **완료된 작업 확인**
```bash
view {memories_path}/tasks/completed/
# related_project: 신제품런칭 인 파일들
```

### 응답 구성:
프로젝트 현황 + 주요 결정사항 + 진행 상황

## Pattern 5: Decision History Lookup

의사결정 배경이나 히스토리 조회 패턴입니다.

### 시나리오: 결정 배경 문의

```
User: "왜 AWS로 전환하기로 결정했었지?"
```

### 조회 순서:

1. **결정 파일 검색**
```bash
view {memories_path}/decisions/
# "AWS" 키워드로 파일 찾기
view {memories_path}/decisions/AWS전환결정.md
```

확인 사항:
- decision_makers (누가 결정)
- rationale (결정 이유)
- alternatives_considered (검토한 대안)
- date (결정 시기)

2. **관련 회의록 확인**
```bash
# decision 파일의 related_to 메타데이터 확인
view {memories_path}/meetings/인프라검토회의.md
```

### 응답 구성:
결정 배경 + 검토 과정 + 최종 판단 근거

## Pattern 6: Task History Lookup

작업 히스토리나 완료 내역 조회 패턴입니다.

### 시나리오: 이전 작업 확인

```
User: "지난주에 내가 뭐 했었지?"
```

### 조회 순서:

1. **완료된 작업 확인**
```bash
view {memories_path}/tasks/completed/
# assignee: 해당유저ID, completed_date: 지난주 범위
```

2. **작업별 상세 내용 확인**
```bash
# 각 작업 파일을 읽어서 내용 파악
view {memories_path}/tasks/completed/랜딩페이지작성.md
```

### 응답 구성:
작업 목록 + 각 작업 내용 요약 + 소요 시간

## Pattern 7: Feedback Collection

피드백이나 개선 제안 조회 패턴입니다.

### 시나리오: 피드백 검토 요청

```
User: "대시보드 관련 피드백 정리해줘"
```

### 조회 순서:

1. **피드백 파일 검색**
```bash
view {memories_path}/feedback/
# "대시보드" 키워드로 파일 찾기
```

2. **상태별 분류**
```bash
# 각 파일의 status 메타데이터 확인
# - submitted
# - under_review
# - accepted
# - rejected
```

### 응답 구성:
피드백 목록 (상태별 분류) + 각 피드백 요약

## Pattern 8: Cross-Reference Lookup

여러 정보를 연결하여 조회하는 패턴입니다.

### 시나리오: 복합 정보 요청

```
User: "Q4 전략 관련해서 우리가 논의한 내용, 결정사항, 진행 상황 모두 알려줘"
```

### 조회 순서:

1. **Index에서 관련 항목 파악**
```bash
view {memories_path}/index.md
# Recent Updates에서 "Q4", "전략" 키워드 확인
```

2. **각 카테고리별 조회**
```bash
# 프로젝트
view {memories_path}/projects/Q4전략.md

# 회의록
view {memories_path}/meetings/
# Q4 관련 회의록 모두 확인

# 결정사항
view {memories_path}/decisions/
# Q4 관련 결정 확인
```

3. **Cross-reference 추적**
```bash
# 각 파일의 related_to 메타데이터를 따라가며 연결된 정보 수집
```

### 응답 구성:
시간순 또는 카테고리별로 정리된 종합 정보

## Pattern 9: Quick Status Check

빠른 상태 확인을 위한 패턴입니다.

### 시나리오: 전체 현황 파악

```
User: "우리 팀 현재 상황 간단히 알려줘"
```

### 조회 순서:

1. **Index 통계 확인**
```bash
view {memories_path}/index.md
# Statistics 섹션 확인
# - Active Projects
# - Total Tasks
# - Recent Updates
```

2. **진행 중인 프로젝트만 확인**
```bash
view {memories_path}/projects/
# status: in_progress 인 파일들만
```

3. **최근 업데이트만 확인**
```bash
# Index의 Recent Updates 섹션 활용
# 최근 10개 업데이트만 확인
```

### 응답 구성:
간결한 요약 (프로젝트 수 + 주요 진행 사항 + 이슈)

## Pattern 10: Search and Filter

특정 조건으로 검색하는 패턴입니다.

### 시나리오: 조건부 검색

```
User: "긴급으로 표시된 항목들 보여줘"
```

### 조회 방법:

**Option A: 카테고리별 수동 검색**
```bash
# 각 카테고리 확인
view {memories_path}/projects/
view {memories_path}/tasks/
view {memories_path}/feedback/
# tags에 "urgent" 포함된 파일 찾기
```

**Option B: 전체 검색**
```bash
# grep 또는 전체 파일 스캔
bash: grep -r "urgent" {memories_path}/ --include="*.md"
```

### 응답 구성:
긴급 항목 목록 (카테고리별 그룹화) + 우선순위 순 정렬

## Best Practices

### 1. Always Start with Index

모든 조회는 index.md부터 시작:
- 전체 구조 파악
- 최근 업데이트 확인
- 통계로 현황 이해

### 2. Follow the Trail

메타데이터의 related_to를 따라가며 연결된 정보 수집:
```yaml
related_to:
  - projects/신제품.md
  - meetings/기획회의.md
```

### 3. Use Context Clues

대화 컨텍스트에서 힌트 활용:
- 채널 ID → channels/ 우선 확인
- @mention → users/ 확인
- 프로젝트명 언급 → projects/ 확인

### 4. Metadata is Your Friend

파일의 메타데이터를 적극 활용:
- `tags`: 빠른 주제 파악
- `status`: 현재 상태 확인
- `priority`: 중요도 판단
- `created/updated`: 시간 정보

### 5. Don't Over-fetch

필요한 정보만 조회:
- 전체 파일을 다 읽지 말고
- 메타데이터로 필터링 후
- 필요한 파일만 상세 확인

### 6. Synthesize Information

여러 파일의 정보를 종합:
- 단순 나열이 아닌
- 맥락을 이해하고
- 유의미한 인사이트 제공

## Performance Tips

### Tip 1: Index First, Details Later
```
❌ Bad: 모든 파일 읽기
✅ Good: Index → 관련 카테고리 → 필요한 파일만
```

### Tip 2: Use Directory Listings
```bash
# 파일명만으로도 많은 정보 파악 가능
view {memories_path}/projects/
# → 신제품런칭.md, 웹사이트리뉴얼.md 등 확인
```

### Tip 3: Leverage Recent Updates
```
Index의 Recent Updates는 10개만 표시
→ 최근 활동이 활발한 영역 빠르게 파악
```

### Tip 4: Smart Keyword Matching
```
User: "디자인 관련 피드백"
→ feedback/ 폴더에서 "디자인" 키워드 검색
→ tags에 "design" 포함된 파일 우선
``` 
