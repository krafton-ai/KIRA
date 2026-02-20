---
name: slack-proactive-intervention-patterns
description: 메모리에서 7가지 개입 기회 패턴을 감지하는 지식 베이스. 조사 제안, 스케줄링, 문서화, 초안 작성, 연결 조율, 예측적 제안, 루틴 자동화 패턴의 시그널과 점수 계산 방법.
---

# Slack Proactive Intervention Patterns

메모리에서 동료들에게 유용한 제안 기회를 감지하는 7가지 패턴.

## Overview

이 스킬은 **"어떤 상황을 발견하면 제안할 만한가?"**에 대한 지식을 제공합니다.

**포함 내용:**
- ✅ 7가지 패턴의 감지 시그널
- ✅ 점수 계산 공식
- ✅ 스캔 대상 파일
- ✅ Threshold 기준

**포함하지 않음:**
- ❌ 워크플로우 (프롬프트 역할)
- ❌ 도구 사용법 (프롬프트 역할)
- ❌ 실행 절차 (프롬프트 역할)

---

## Pattern 1: 조사/리서치 제안

### 언제 감지되나?

**스캔 대상:**
- `projects/*.md` (status: planning, in_progress)
- `decisions/*.md` (status: under_review)
- `meetings/*.md` (action_items 미해결)
- `misc/*.md` (최근 3일 업데이트)
- `channels/*.md` (프로필 파일 - 채널 가이드라인 참고용)

**시그널:**
```yaml
Primary Keywords:
  - "알아봐야", "조사 필요", "찾아봐야", "확인 필요"
  - "리서치", "검토", "파악"

Secondary Keywords:
  - "어떤 게", "뭐가", "무엇을", "어느 것"
  - "vs", "대", "비교", "중"
  - "좋을까", "나을까", "적합할까"

Question Markers:
  - 문장이 "?"로 끝남
  - 옵션 나열 ("A vs B", "A나 B", "A, B, C 중")

Status:
  - 질문 후 3시간 ~ 3일 경과
  - 답변 없음 or "나중에", "다음에" 같은 미뤄진 응답
```

### 점수 계산

```
Base Score: 2점 (키워드 명확할 때)

+ 질문 형태 ("?"): +1점
+ 옵션 나열 (vs, 나, 중): +1점

+ 시급성:
  - "긴급", priority: high → +2점
  - "중요", priority: medium → +1점

+ 영향도:
  - 3명 이상 관련 → +2점
  - 2명 관련 → +1점
  - 1명 → 0점

Threshold: 5점 이상
```

### 제안 메시지 가이드

```
점수 5-6 (보통):
"{topic} 조사해드릴까요? {옵션들} 비교해드릴게요"

점수 7-8 (중요):
"{topic} 리서치 필요해 보이는데, 장단점 비교 분석해드릴까요?"

점수 9+ (긴급):
"{topic} 결정 급하신 것 같아요. 빠르게 정리해드릴까요?"
```

---

## Pattern 2: 스케줄링 제안

### 언제 감지되나?

**스캔 대상:**
- `meetings/*.md` (status: proposed)
- `tasks/*.md` (type: meeting_needed)
- `misc/*.md` (최근 3일 - 회의 관련 대화)
- `channels/*.md` (프로필 파일 - 채널 가이드라인 참고용)

**시그널:**
```yaml
Meeting Keywords:
  - "회의", "미팅", "만남", "모임"
  - "논의", "상의", "협의", "검토"

Schedule Keywords:
  - "일정", "스케줄", "시간"
  - "잡아야", "정해야", "조율"
  - "다음주", "이번주", "조만간", "언제"

Participants:
  - 2명 이상 멘션 (@user1, @user2)
  - "팀", "전체", "같이", "함께"

Status:
  - 회의 필요 언급됨
  - meetings/에 등록 안 됨
  - 또는 status: proposed인데 3일+ 경과
```

### 점수 계산

```
Base Score: 2점

+ 참석자 언급: +1점

+ 참석자 수:
  - 5명 이상 → +4점
  - 3-4명 → +2점
  - 2명 → +1점

+ 시급성:
  - "오늘", "내일" → +2점
  - "이번주" → +1점

Threshold: 5점 이상
```

### 제안 메시지 가이드

```
점수 5-6:
"{topic} 회의 일정 잡아드릴까요? 희망 시간 알려주세요"

점수 7-8:
"{participants}님들 {topic} 논의 필요하신 것 같아요. 조율해드릴까요?"

점수 9+:
"{topic} 회의 {deadline} 전에 급하게 잡아야 할 것 같아요"
```

---

## Pattern 3: 문서화/정리 제안

### 언제 감지되나?

**스캔 대상:**
- `meetings/*.md` (회의록 없는 회의)
- `projects/*.md` (문서화 필요 프로젝트)
- `decisions/*.md` (문서화 필요 결정사항)
- `resources/*.md` (기존 문서 확인)
- `channels/*.md` (프로필 파일 - 채널 가이드라인 참고용)

**시그널:**
```yaml
Repeated Questions:
  - 같은 주제 2회 이상 질문
  - 다른 채널에서 유사 질문 (키워드 70%+ 중복)

Long Discussions:
  - 특정 스레드 20+ 메시지
  - 회의 있는데 회의록 없음

Documentation Hints:
  - "정리하면", "문서로", "정리 필요"
  - "가이드", "매뉴얼", "문서화"

Knowledge Gap:
  - 자주 묻는 질문인데 resources/에 없음
  - "어디서 봤는데", "전에 들었는데"
```

### 점수 계산

```
Base Score: 2점

+ 반복도:
  - 3회 이상 → +3점
  - 2회 → +2점

+ 대화 길이:
  - 30+ 메시지 → +2점
  - 20+ 메시지 → +1점

+ 영향도:
  - 여러 채널 → +2점
  - 여러 사람 → +1점

Threshold: 5점 이상
```

### 제안 메시지 가이드

```
점수 5-6:
"{topic} 질문이 여러 번 나왔는데, 가이드 문서 만들어드릴까요?"

점수 7-8:
"{channel}의 {topic} 논의 길어졌어요. 회의록 만들어드릴까요?"

점수 9+:
"{topic} 자주 나오는데 문서가 없네요. 팀 위키에 정리해드릴까요?"
```

---

## Pattern 4: 초안/템플릿 제안

### 언제 감지되나?

**스캔 대상:**
- `tasks/*.md` (status: not_started)
- `projects/*.md` (마감 임박)
- `misc/*.md` (최근 3일 - 작성 작업 언급)
- `channels/*.md` (프로필 파일 - 채널 가이드라인 참고용)

**시그널:**
```yaml
Writing Tasks:
  - "작성해야", "만들어야", "써야"
  - "제안서", "보고서", "프레젠테이션"
  - "문서", "자료", "초안"

Deadline:
  - due_date 3-7일 이내
  - status: not_started

Recurring:
  - "주간", "월간", "정기"
  - 과거 유사 작업 3회+

Project Phase:
  - status: planning → in_progress 전환 예정
  - 킥오프 임박
```

### 점수 계산

```
Base Score: 2점

+ 마감 시급성:
  - 1-2일 → +3점
  - 3-5일 → +2점
  - 6-7일 → +1점

+ 우선순위:
  - critical → +3점
  - high → +2점
  - medium → +1점

+ 준비도:
  - 참고 자료 있음 → +1점

Threshold: 5점 이상
```

### 제안 메시지 가이드

```
점수 5-6:
"{deadline}까지 {document} 작성하셔야 하는데, 초안 만들어드릴까요?"

점수 7-8:
"{project} {document} 곧 필요하실 것 같아요. 준비해드릴까요?"

점수 9+:
"{deadline} 임박한 {document} 아직 시작 안 하셨네요. 긴급 도와드릴까요?"
```

---

## Pattern 5: 연결/조율 제안

### 언제 감지되나?

**스캔 대상:**
- `projects/*.md` (협업 기회 - 유사 프로젝트 비교)
- `misc/*.md` (최근 대화 - 유사 주제 발견)
- `users/*.md` (전문성 파악 - 프로필)
- `channels/*.md` (채널별 가이드라인 - 프로필)

**시그널:**
```yaml
Similar Topics:
  - 다른 채널에서 유사 주제 논의
  - 키워드 중복도 70%+

Complementary Needs:
  - 한쪽: 전문성 필요 ("잘 아는 사람", "전문가")
  - 다른쪽: 전문가 존재 (users/ expertise)

Collaboration:
  - 비슷한 작업 중복 진행
  - 리소스 공유 가능

Isolated Struggle:
  - 혼자 고민하는데 해결책 있는 사람 존재
```

### 점수 계산

```
Base Score: 2점

+ 시너지:
  - 명확한 도움 가능 → +3점
  - 도움 가능성 있음 → +2점

+ 시급성:
  - 한쪽 blocked → +2점
  - 한쪽 struggling → +1점

+ 확실성:
  - 명확한 매칭 → +1점

Threshold: 5점 이상
```

### 제안 메시지 가이드

```
점수 5-6:
"{channel1}과 {channel2}에서 비슷한 주제 논의 중이에요"

점수 7-8:
"{person1}님이 {topic} 어려워하시는데, {person2}님이 전문가세요"

점수 9+:
"같은 작업 중복 진행 중이에요. 합동 작업 제안드릴까요?"
```

---

## Pattern 6: 예측적 제안

### 언제 감지되나?

**스캔 대상:**
- `meetings/*.md` (정기 패턴)
- `projects/*.md` (단계별 패턴)
- `tasks/*.md` (반복 작업)

**시그널:**
```yaml
Calendar Patterns:
  - 매주 X요일 Y 회의 → 전날 준비
  - 월말 리포트 → 일주일 전 초안

Project Phases:
  - 킥오프 3일 전 → 킥오프 자료
  - 스프린트 종료 2일 전 → 회고 준비

Regular Events:
  - 주간 회의 → 전날 아젠다
  - 월간 리뷰 → 일주일 전 데이터

Observation:
  - 과거 3회 이상 패턴 관찰됨
  - "보통 이 단계에서 ~필요"
```

### 점수 계산

```
Base Score: 2점

+ 확실성:
  - 3회+ 관찰 → +3점
  - 2회 관찰 → +2점

+ 가치:
  - 시간 크게 절약 → +2점
  - 시간 절약 → +1점

+ 타이밍:
  - 완벽한 타이밍 → +1점

Threshold: 5점 이상
```

### 제안 메시지 가이드

```
점수 5-6:
"매주 {day} {meeting} 있으신데, 미리 정리해드릴까요?"

점수 7-8:
"{project} {event}가 {date}인데, {materials} 준비해드릴까요?"

점수 9+:
"과거 패턴상 {materials} 필요하실 텐데 준비해드릴까요?"
```

---

## Pattern 7: 루틴 자동화 제안

### 언제 감지되나?

**스캔 대상:**
- `tasks/*.md` (반복 작업)
- `misc/*.md` (패턴화된 작업 언급)
- `channels/*.md` (프로필 파일 - 채널 가이드라인 참고용)

**시그널:**
```yaml
Repetitive Tasks:
  - 동일 작업 3회 이상 반복
  - 주기: 매일/매주/매월

Manual Routines:
  - "매번", "또", "또 해야"
  - 패턴화된 작업

Automation Opportunity:
  - 간단한 반복 작업
  - 템플릿화 가능
  - 데이터 수집/정리

Time Consuming:
  - "매번 30분", "시간 걸려"
  - 반복으로 시간 많이 소요
```

### 점수 계산

```
Base Score: 2점

+ 반복도:
  - 5회+ → +3점
  - 3-4회 → +2점

+ 시간 절약:
  - 주 2시간+ → +3점
  - 주 1시간+ → +2점

+ 자동화 가능성:
  - 쉽게 자동화 → +2점
  - 자동화 가능 → +1점

Threshold: 6점 이상 (더 높은 기준)
```

### 제안 메시지 가이드

```
점수 6-7:
"{task}를 매주 하시는데, 자동 초안 설정할까요?"

점수 8-9:
"{task} 매{frequency}마다 하시네요. 자동화해드릴까요? (주 {time} 절약)"

점수 10+:
"자동화하면 월 {total} 절약돼요. 설정해드릴까요?"
```

---

## Filtering Criteria

### 중복 확인

**체크 방법:**
```
misc/interventions/ 에서 최근 48시간 내 개입 확인
파일명: {pattern}_{topic}_{timestamp}.md

같은 pattern + topic 조합이면 → skip
```

### 우선순위 계산

**보너스 점수:**
```
긴급도:
- 마감 24시간 이내 → +3점
- 마감 3일 이내 → +2점

블로킹:
- 다른 작업 블로킹 → +2점
```

**선택:**
```
점수로 정렬 후 Top 1-3개만
```

---

## Pattern Detection Tips

### 독립적 체크

각 패턴은 독립적으로 확인:
```
for pattern in [1, 2, 3, 4, 5, 6, 7]:
    try:
        check_pattern(pattern)
    except:
        continue  # 하나 실패해도 계속
```

### 시간 윈도우

**Pattern 1 (조사):** 3시간 ~ 3일
**Pattern 2 (스케줄):** 즉시 ~ 7일
**Pattern 3 (문서화):** 즉시 ~ 무제한
**Pattern 4 (초안):** 3 ~ 7일
**Pattern 5 (연결):** 즉시 ~ 3일
**Pattern 6 (예측):** 패턴 기반
**Pattern 7 (자동화):** 3회+ 관찰 후

### 키워드 매칭

**Exact Match (정확):**
- "알아봐야", "회의", "작성해야"

**Fuzzy Match (유연):**
- "알아봐" vs "알아보자" vs "알아봐야"
- "회의" vs "미팅" vs "만남"

**Context (맥락):**
- 단순 키워드만이 아니라 주변 맥락 확인
- "회의" + "잡아야" = 스케줄링
- "회의" + "정리" = 문서화

---

## Threshold Guidelines

### 기본 Threshold

| Pattern | Threshold | 이유 |
|---------|-----------|------|
| 1-6 | 5점 | 일반적 개입 기준 |
| 7 | 6점 | 더 신중하게 (자동화는 영향 큼) |

### 튜닝 방법

```
수용률 < 30%: threshold +1~2점 (너무 적극적)
수용률 30-50%: threshold +0.5점 (약간 적극적)
수용률 50-70%: 유지 (적정)
수용률 > 70%: threshold -0.5~1점 (더 적극적 가능)
```

### 패턴별 독립 조정

성공률에 따라 각 패턴의 threshold 독립 조정 가능:

```python
pattern_thresholds = {
    'research': 4.5,      # 성공률 높음
    'scheduling': 5.0,    
    'documentation': 6.0, # 성공률 낮음
    'drafts': 5.0,
    'connections': 5.5,
    'predictive': 5.0,
    'automation': 7.0     # 매우 신중
}
```

---

## Edge Cases

### 경계선 점수 (정확히 threshold)

```
점수 = threshold 일 때:
→ 컨텍스트 추가 확인
→ priority/중요도 확인
→ high/critical → 제안
→ medium/low → skip
```

### 복수 패턴 매칭

```
하나의 상황이 여러 패턴에 해당:
→ 각각 독립적으로 점수 계산
→ 점수 높은 것 우선
→ 둘 다 threshold 넘으면 Top 2 선택
```

### 불완전한 정보

```
user_id를 찾을 수 없음:
→ 해당 제안 skip (추측 금지)

channel_id를 찾을 수 없음:
→ 해당 제안 skip

점수 계산에 필요한 정보 없음:
→ Base점수만으로 계산
```

---

## Reference Documents

더 자세한 내용:

- **[pattern-detection-guide.md](references/pattern-detection-guide.md)** - 각 패턴의 상세 감지 로직과 실제 예시
- **[scoring-examples.md](references/scoring-examples.md)** - 다양한 상황별 점수 계산 예시

---

## Summary

**이 스킬이 제공하는 것:**
- ✅ 7가지 패턴의 감지 시그널
- ✅ 점수 계산 공식
- ✅ Threshold 기준
- ✅ 메시지 가이드 (참고용)

**이 스킬이 제공하지 않는 것:**
- ❌ 실행 워크플로우 (→ 프롬프트)
- ❌ 도구 사용법 (→ 프롬프트)
- ❌ ID 확인 방법 (→ 프롬프트)
- ❌ 파일 접근 방법 (→ 프롬프트)

**사용 방법:**
1. 프롬프트가 메모리 스캔
2. 이 스킬의 패턴으로 매칭 여부 확인
3. 점수 계산
4. Threshold 이상이면 제안 기회
5. 프롬프트가 실제 처리 수행
