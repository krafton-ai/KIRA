# Data Schemas for Memory Types

이 문서는 각 메모리 타입별로 권장되는 메타데이터 스키마를 정의합니다.

## Channel Schema

채널 정보를 저장할 때 사용하는 스키마:

```yaml
---
type: channel
channel_id: C01234567        # 슬랙 채널 ID
channel_name: "마케팅팀"      # 채널 이름
channel_type: public         # public, private, dm, group_dm
participants:                # 참여자 목록
  - U01234567
  - U76543210
guidelines:                  # 커뮤니케이션 지침
  tone: professional
  style: "간결하고 명확하게"
  response_time: "1시간 이내"
tags:
  - marketing
  - important
created: 2025-10-28 10:00:00
updated: 2025-10-28 15:30:00
---
```

## User Schema

팀원 정보를 저장할 때 사용하는 스키마:

```yaml
---
type: user
user_id: U01234567           # 슬랙 유저 ID
display_name: "김철수"        # 화면 표시명
real_name: "Kim Chul-soo"    # 실명
email: "chulsoo@company.com"
role: "Product Manager"
team: "Product Team"
profile:
  korean_name: "김철수"
  english_name: "Chul-soo Kim"
  timezone: "Asia/Seoul"
  working_hours: "09:00-18:00"
communication_style:
  tone: friendly
  detail_level: high
  prefers: "bullet points"
guidelines:
  - "데이터 기반 의사결정 선호"
  - "오전 중 미팅 선호"
tags:
  - pm
  - product
created: 2025-10-28 10:00:00
---
```

## Project Schema

프로젝트 정보를 저장할 때 사용하는 스키마:

```yaml
---
type: project
project_id: PROJ-001
project_name: "신제품 런칭"
status: in_progress          # planning, in_progress, completed, on_hold
priority: high               # low, medium, high, critical
participants:
  - U01234567
  - U76543210
start_date: 2025-09-01
target_date: 2025-12-31
milestones:
  - name: "MVP 완성"
    date: 2025-10-31
    status: completed
  - name: "베타 테스트"
    date: 2025-11-30
    status: in_progress
related_channels:
  - C01234567
tags:
  - launch
  - high-priority
created: 2025-09-01 10:00:00
updated: 2025-10-28 15:30:00
---
```

## Task Schema

업무 기록을 저장할 때 사용하는 스키마:

```yaml
---
type: task
task_id: TASK-001
title: "랜딩 페이지 카피 작성"
status: completed            # todo, in_progress, completed, cancelled
assignee: U01234567
requested_by: U76543210
priority: medium
related_project: PROJ-001
related_channel: C01234567
due_date: 2025-10-30
completed_date: 2025-10-28
effort_hours: 3
tags:
  - copywriting
  - marketing
created: 2025-10-25 10:00:00
completed: 2025-10-28 15:00:00
---
```

## Meeting Schema

회의록을 저장할 때 사용하는 스키마:

```yaml
---
type: meeting
meeting_id: MTG-001
title: "Q4 전략 회의"
date: 2025-10-28 14:00:00
duration_minutes: 60
attendees:
  - U01234567
  - U76543210
  - U11111111
location: "2층 회의실 A"
meeting_type: planning       # standup, planning, review, retrospective
related_project: PROJ-001
tags:
  - strategy
  - q4
created: 2025-10-28 14:00:00
---
```

## Decision Schema

의사결정을 저장할 때 사용하는 스키마:

```yaml
---
type: decision
decision_id: DEC-001
title: "AWS 전환 결정"
date: 2025-10-28
decision_makers:
  - U01234567
  - U76543210
outcome: approved
impact: high
related_project: PROJ-001
alternatives_considered:
  - "현재 인프라 유지"
  - "GCP 전환"
  - "AWS 전환 (선택됨)"
rationale: "비용 효율성과 확장성"
tags:
  - infrastructure
  - strategic
created: 2025-10-28 10:00:00
---
```

## Feedback Schema

피드백을 저장할 때 사용하는 스키마:

```yaml
---
type: feedback
feedback_id: FB-001
title: "대시보드 UX 개선 제안"
from: U01234567
feedback_type: improvement   # bug, improvement, feature_request
priority: medium
status: under_review         # submitted, under_review, accepted, rejected
related_feature: "관리자 대시보드"
tags:
  - ux
  - dashboard
created: 2025-10-28 10:00:00
---
```

## Resource Schema

참고자료/문서를 저장할 때 사용하는 스키마:

```yaml
---
type: resource
title: "슬랙 봇 개발 가이드"
resource_type: guide         # guide, documentation, template, policy
source: confluence
source_url: "https://..."
category: development
tags:
  - guide
  - slack
  - development
created: 2025-10-28 10:00:00
updated: 2025-10-28 15:00:00
---
```

## News/External Schema

외부 뉴스나 정보를 저장할 때 사용하는 스키마:

```yaml
---
type: news
title: "경쟁사 신제품 출시"
source: "TechCrunch"
source_url: "https://..."
date: 2025-10-28
relevance: high
related_project: PROJ-001
tags:
  - competitor
  - market
created: 2025-10-28 10:00:00
---
```

## Generic Metadata Fields

모든 타입에 공통적으로 사용할 수 있는 필드:

- `created`: 생성 일시 (YYYY-MM-DD HH:MM:SS)
- `updated`: 수정 일시 (YYYY-MM-DD HH:MM:SS)
- `tags`: 태그 배열 또는 쉼표로 구분된 문자열
- `related_to`: 관련된 다른 파일들의 경로
- `author`: 작성자
- `version`: 버전 번호 
