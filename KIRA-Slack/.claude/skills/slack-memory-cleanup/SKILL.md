---
name: slack-memory-cleanup
description: Memory cleanup and organization skill for AI employees. Provides guidelines for detecting duplicates, fixing misclassified files, and removing stale information from memory storage.
---

# Memory Cleanup Guide

## Overview

AI 직원의 메모리는 시간이 지남에 따라 중복, 오분류, 오래된 정보가 쌓입니다. 이 skill은 메모리를 체계적으로 정리하는 가이드와 도구를 제공합니다.

**핵심 원칙:**
- 하드코딩된 보존 기간 없음 - LLM이 컨텍스트 기반으로 판단
- 프로필 파일(users/, channels/)은 1 entity = 1 file 원칙
- 확실하지 않으면 삭제보다 보존

**slack-memory-store 스킬과의 연동:**
- 이 skill은 `slack-memory-store` 스킬로 저장된 메모리를 정리합니다
- 폴더 구조, 메타데이터 스키마, type 필드가 일치합니다
- 프로필 파일 vs 토픽 파일 구분 원칙을 따릅니다

## Quick Start

```bash
# 1. 분석만 (dry-run, 변경 없음)
python scripts/cleanup_memory.py {memories_path}

# 2. 결과 확인 후 실제 정리 실행
python scripts/cleanup_memory.py {memories_path} --execute

# 3. 정리 후 인덱스 업데이트
python scripts/update_index.py {memories_path}
```

## Scripts

이 skill은 정리 작업을 돕는 스크립트를 제공합니다.

### cleanup_memory.py - 중복/오분류 탐지

메모리 폴더를 스캔하여 문제를 탐지합니다. 기본은 분석만 수행(dry-run)합니다.

```bash
# 전체 분석
python scripts/cleanup_memory.py {memories_path}

# 특정 폴더만 분석
python scripts/cleanup_memory.py {memories_path} --folder users
python scripts/cleanup_memory.py {memories_path} --folder channels

# 상세 디버그 출력
python scripts/cleanup_memory.py {memories_path} --verbose

# 실제 정리 실행 (오분류 파일 이동)
python scripts/cleanup_memory.py {memories_path} --execute
```

**출력 예시:**
```
============================================================
📊 메모리 정리 분석 결과
============================================================

## 🔴 중복 파일

### users/ 폴더 (동일인 중복)
  email:batteryho@krafton.com:
    - 전지호 (Jiho Jeon).md (✅ 프로필)
    - 전지호 (Jiho Jeon) - 이메일 분석.md (📝 작업기록)
    - 전지호_외부플랫폼초대_2025-12-08.md (📝 작업기록)

## 🟡 오분류 파일
  전지호 (Jiho Jeon) - 이메일 분석.md
    현재: users/ → 권장: tasks/
    이유: 파일명에 작업 키워드
  Jira 티켓 조회 성공.md
    현재: channels/ → 권장: tasks/
    이유: type이 'task_completed'

## 📈 요약
  - 중복 그룹: 3개
  - 오분류 파일: 5개
```

**주요 탐지 기능:**
- **프로필 vs 작업기록 구분**: users/ 중복에서 어떤 파일이 프로필이고 어떤 파일이 작업기록인지 표시
- **오분류 이유 표시**: 왜 해당 파일이 오분류로 판단되었는지 이유 제공
- **type 필드 활용**: 메타데이터의 `type` 필드를 확인하여 폴더와 불일치 탐지

### update_index.py - 인덱스 업데이트

정리 후 index.md를 갱신합니다.

```bash
python scripts/update_index.py {memories_path}
```

---

## 정리 워크플로우

### Step 1: 현황 파악

```bash
# 전체 메모리 구조 확인
ls -la {memories_path}/

# 각 폴더별 파일 수 확인
find {memories_path} -type f -name "*.md" | wc -l

# 폴더별 상세
ls -la {memories_path}/users/
ls -la {memories_path}/channels/
ls -la {memories_path}/tasks/
```

### Step 2: 문제 탐지

스크립트 또는 수동으로 다음 문제들을 탐지합니다:

1. **중복 파일** - 같은 entity가 여러 파일로 분산
2. **잘못된 분류** - 폴더와 내용 불일치
3. **휘발성 정보** - 오래되고 중요도 낮은 파일

### Step 3: 정리 실행

탐지된 문제에 따라 적절한 조치:
- **중복** → 병합 ([deduplication-rules.md](references/deduplication-rules.md) 참고)
- **오분류** → 이동 ([misclassification-rules.md](references/misclassification-rules.md) 참고)
- **휘발성** → 삭제 ([cleanup-patterns.md](references/cleanup-patterns.md) 참고)

### Step 4: 인덱스 업데이트

정리 후 반드시 인덱스 갱신:
```bash
python scripts/update_index.py {memories_path}
```

---

## 핵심 정리 대상

### 1. users/ 폴더

**정상 상태**: 1인당 1파일 (프로필)
```
users/
└── 전지호 (Jiho Jeon).md    ← 프로필 파일만
```

**문제 상태**: 1인이 여러 파일
```
users/
├── 전지호 (Jiho Jeon).md              ← 프로필 (유지)
├── 전지호 (Jiho Jeon) - 이메일 분석.md  ← tasks/로 이동
├── 전지호 - AI 보고서.md               ← tasks/ 또는 misc/로 이동
└── Serin_Kim_김세린.md                 ← 기존 김세린 파일과 병합
```

**판단 기준**:
- `email` 또는 `user_id`가 같으면 동일인
- 프로필 파일 1개만 users/에 유지
- 나머지는 내용에 따라 적절한 폴더로 이동

### 2. channels/ 폴더

**정상 상태**: 채널당 1파일 (채널 ID로 시작)
```
channels/
└── C08G76BB8JK_my-daily-scrum.md    ← 채널 프로필
```

**문제 상태**: 채널 정보가 아닌 파일들
```
channels/
├── C08G76BB8JK_my-daily-scrum.md      ← 유지
├── Jira 티켓 조회 성공.md              ← tasks/로 이동
└── 메일 조회 작업 성공.md              ← tasks/로 이동
```

**판단 기준**:
- `channel_id`가 있고 채널 가이드라인/정보면 유지
- 작업 결과, 성공 사례 등은 tasks/로 이동

### 3. tasks/ 폴더

**정상 상태**: 작업별 1파일
```
tasks/
├── KIRA 프로젝트 작업 완료 - 2025-11-25.md
└── Tableau 데이터 조회 - 2025-12-09.md
```

**문제 상태**: 유사 내용 중복
```
tasks/
├── 7개_이메일_분석_2025-12-08.md     ← 삭제 (더 완전한 버전 있음)
├── 8개_이메일_분석_2025-12-08.md     ← 삭제
├── 9개_이메일_분석_2025-12-08.md     ← 삭제
└── 10개_이메일_분석_2025-12-08.md    ← 유지 (최종 버전)
```

**판단 기준**:
- 같은 작업의 중간 결과들 → 최종 버전만 유지
- 같은 날짜에 유사 제목 → 가장 완전한 것만 유지

### 4. 기타 폴더

| 폴더 | 정리 기준 |
|------|-----------|
| `projects/` | 완료된 프로젝트 → archive/ 이동 가능 |
| `decisions/` | 중요, 장기 보존 |
| `meetings/` | 오래된 것 → 요약 후 삭제 가능 |
| `misc/` | 정리 1순위, 오래된 것 삭제 |
| `external/news/` | 시간 지나면 가치 하락, 삭제 가능 |
| `announcements/` | 오래된 공지 삭제 가능 |

---

## 중요도 판단 (LLM 기준)

하드코딩된 보존 기간 없이, LLM이 다음을 고려하여 판단합니다.

### 보존해야 하는 것
- 프로필 정보 (users/, channels/)
- 의사결정 기록 (decisions/)
- 진행 중인 프로젝트 (projects/)
- 최근 상호작용과 관련된 정보

### 삭제 가능한 것
- 중간 결과물 (최종본 있을 때)
- 오래된 일상 대화 (misc/)
- 시의성 지난 뉴스/공지
- 중복된 정보

### 판단 시 고려사항
- 마지막 수정일 (`updated` 메타데이터)
- 관련 프로젝트 상태 (진행 중 vs 완료)
- 파일 간 연결 관계 (`related_to`)
- 태그의 중요도 (urgent, important 등)

---

## 정리 실행 예시

### 예시 1: users/ 중복 정리

```
요청: "users 폴더 정리해줘"

1. 현황 파악
   - 전지호 관련 파일 6개 발견
   - 김세린 관련 파일 2개 발견

2. 분석
   - 전지호: 프로필 1개 + 작업 기록 5개
   - 김세린: 같은 사람 다른 이름 2개

3. 실행
   - 전지호 작업 기록 → tasks/로 이동
   - 김세린 파일 → 병합 후 1개만 유지

4. 결과 보고
   "users/ 정리 완료:
    - 전지호: 5개 파일 tasks/로 이동
    - 김세린: 2개 파일 1개로 병합"
```

### 예시 2: 전체 메모리 정리

```
요청: "메모리 전체 정리해줘"

1. 현황 파악
   - 총 120개 파일
   - users/: 47개 (중복 의심)
   - tasks/: 40개 (중복 의심)
   - channels/: 10개 (오분류 의심)

2. 폴더별 분석 및 정리

3. 결과 보고
   "메모리 정리 완료:
    - 삭제: 15개 (중복/중간결과)
    - 이동: 8개 (오분류 수정)
    - 병합: 5개 (동일인 중복)
    - 현재 총: 97개 파일"
```

---

## 안전 가이드라인

### 삭제 전 확인
- 중요 파일 삭제 전 사용자에게 확인
- `decisions/`, `projects/` 삭제 시 특히 주의
- 확실하지 않으면 삭제보다 이동

### 백업 권장
- 대량 정리 전 백업 제안
- `cp -r {memories_path} {memories_path}_backup_{date}`

### 롤백 가능성
- 삭제한 파일 목록 기록
- 이동한 파일의 원래 위치 기록

---

## Reference Documents

자세한 규칙은 다음 문서를 참고하세요:

- **[cleanup-patterns.md](references/cleanup-patterns.md)** - 정리 패턴 및 LLM 판단 기준
- **[deduplication-rules.md](references/deduplication-rules.md)** - 중복 탐지 및 병합 규칙
- **[misclassification-rules.md](references/misclassification-rules.md)** - 오분류 탐지 및 이동 규칙 
