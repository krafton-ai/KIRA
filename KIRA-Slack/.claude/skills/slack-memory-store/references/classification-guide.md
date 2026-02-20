# Content Classification Guide

이 문서는 다양한 형태의 정보를 어떻게 자동으로 분류하고 저장하는지 설명합니다.

## Classification Strategy

정보는 다음 순서로 분류됩니다:

1. **명시적 메타데이터**: `type` 필드가 있으면 해당 타입 사용
2. **구조적 메타데이터**: channel_id, user_id 등 구조적 정보로 판단
3. **키워드 분석**: 내용의 키워드를 분석하여 자동 분류
4. **기본값**: 분류 불가능한 경우 `misc/`로 저장

## Content Type Mapping

| Content Type | Target Directory | Action | Triggers |
|-------------|------------------|--------|----------|
| Channel Profile | `channels/` | **UPDATE** existing | channel_id + type='channel' + guidelines/preferences |
| User Profile | `users/` | **UPDATE** existing | user_id + type='user' + profile/preferences |
| Project | `projects/` | CREATE/UPDATE | 프로젝트, project, 진행상황, milestone, 로드맵 |
| Decision | `decisions/` | CREATE (date-stamped) | 결정, decision, 승인, approval, 합의 |
| Task | `tasks/` | CREATE | 업무, task, 완료, completed, action item |
| Meeting | `meetings/` | CREATE (date-stamped) | 회의, meeting, 미팅, 논의 |
| Feedback | `feedback/` | CREATE | 피드백, feedback, 개선, 제안 |
| Announcement | `announcements/` | CREATE | 공지, announcement, 알림 |
| Resource | `resources/` | CREATE | 가이드, guide, 매뉴얼, documentation |
| News | `external/news/` | CREATE | 뉴스, news, 기사, 외부 |
| Misc | `misc/` | CREATE (date-stamped) | (기본값) casual conversations |

## Handling Different Content Sources

### 1. Slack Messages

**특징**: 대화형, 짧은 메시지, 스레드 구조

**처리 방법**:
```python
metadata = {
    'type': 'channel' if has_channel_context else 'misc',
    'channel_id': 'C01234567',
    'channel_name': '마케팅팀',
    'participants': ['U01', 'U02'],
    'message_count': 15,
    'date_range': '2025-10-28'
}

# 대화 내용을 시간순으로 정리
content = format_slack_thread(messages)
```

**저장 위치 결정 (Hybrid Strategy)**:
- **채널 가이드라인/규칙** → UPDATE `channels/C123_채널명.md` (프로필 파일)
- **프로젝트 논의** → CREATE `projects/프로젝트명.md`
- **의사결정 내용** → CREATE `decisions/주제_DATE.md`
- **회의 내용** → CREATE `meetings/DATE-주제.md`
- **일반 대화** → CREATE `misc/채널명_DATE.md` (or skip)

### 2. Confluence Documents

**특징**: 구조화된 문서, 긴 내용, 섹션 구조

**처리 방법**:
```python
metadata = {
    'type': 'resource',
    'source': 'confluence',
    'source_url': 'https://...',
    'space': 'Engineering',
    'last_updated': '2025-10-28'
}

# Confluence HTML을 Markdown으로 변환
content = convert_html_to_markdown(confluence_html)
```

**저장 위치 결정**:
- 가이드/매뉴얼 → `resources/`
- 프로젝트 문서 → `projects/`
- 회의록 → `meetings/`

### 3. Email Threads

**특징**: 형식적, 수신자/발신자 명확, 스레드 구조

**처리 방법**:
```python
metadata = {
    'type': 'auto-detect',  # 내용 기반 자동 판단
    'from': 'sender@company.com',
    'to': ['recipient@company.com'],
    'subject': '...',
    'date': '2025-10-28',
    'thread_length': 5
}

# 이메일 스레드를 시간순으로 정리
content = format_email_thread(emails)
```

**저장 위치 결정**:
- 공지 이메일 → `announcements/`
- 프로젝트 관련 → `projects/`
- 피드백 → `feedback/`
- 일반 → `misc/`

### 4. News Articles

**특징**: 외부 출처, URL 포함, 시간 민감

**처리 방법**:
```python
metadata = {
    'type': 'news',
    'source': 'TechCrunch',
    'source_url': 'https://...',
    'date': '2025-10-28',
    'relevance': 'high',
    'related_project': 'PROJ-001'
}

# 기사 본문 정리
content = clean_article_content(article_html)
```

**저장 위치**: 항상 `external/news/`

### 5. Meeting Transcripts

**특징**: 대화 형태, 참석자 정보, 액션 아이템

**처리 방법**:
```python
metadata = {
    'type': 'meeting',
    'date': '2025-10-28 14:00:00',
    'attendees': ['U01', 'U02'],
    'duration_minutes': 60
}

# 회의록 구조화
content = format_meeting_transcript(transcript)
```

**저장 위치**: 항상 `meetings/`

## Content Formatting Best Practices

### 제목 생성

```python
# 자동 제목 생성 규칙
if explicit_title:
    title = explicit_title
elif source == 'slack':
    title = f"{channel_name} - {date}"
elif source == 'confluence':
    title = confluence_page_title
elif source == 'email':
    title = email_subject
else:
    title = f"Note - {date}"
```

### 파일명 생성

```python
# 깔끔한 파일명 생성
filename = clean_title
    .replace('/', '-')
    .replace(' ', '_')
    .strip()
    [:50]  # 최대 50자

# 날짜 접두사 추가 (선택적)
if add_date:
    filename = f"{YYYYMMDD}_{filename}"

filename += '.md'
```

### 중복 방지

```python
# 동일한 파일이 있으면 버전 번호 추가
if file_exists(filename):
    base = filename.stem
    counter = 1
    while file_exists(f"{base}_v{counter}.md"):
        counter += 1
    filename = f"{base}_v{counter}.md"
```

## Metadata Enrichment

자동으로 추가되는 메타데이터:

1. **타임스탬프**:
   - `created`: 최초 생성 시각
   - `updated`: 마지막 수정 시각

2. **분류 정보**:
   - `category`: 저장된 디렉토리 (자동)
   - `type`: 콘텐츠 타입

3. **연결 정보**:
   - `related_to`: 관련 파일들 (자동 감지)
   - `related_project`: 관련 프로젝트
   - `related_channel`: 관련 채널

4. **검색 보조**:
   - `tags`: 자동 추출된 키워드
   - `keywords`: 중요 키워드

## Special Cases

### 1. 복합 정보 (Mixed Content)

여러 타입이 섞인 경우:

```python
# 주요 타입을 기준으로 분류
if primarily_about_project:
    directory = 'projects/'
elif primarily_about_decision:
    directory = 'decisions/'
else:
    # 가장 많이 언급된 키워드로 판단
    directory = classify_by_dominant_keywords(content)
```

### 2. 민감한 정보

개인 정보나 민감한 정보:

```python
metadata['sensitive'] = True
metadata['access_level'] = 'restricted'
# 파일 권한 설정 (선택적)
```

### 3. 임시 정보

임시로 저장하는 정보:

```python
metadata['temporary'] = True
metadata['expires'] = '2025-12-31'
# 만료일 이후 자동 삭제 가능
```

## Update vs. Create Logic

기존 파일을 업데이트할지 새로 만들 지 판단:

```python
# 동일한 내용 판단 기준
same_content = (
    same_title AND
    same_date AND
    same_source AND
    similar_content  # 90% 이상 유사
)

if same_content:
    update_existing_file()
else:
    create_new_file()
```

## Index Update Triggers

index.md를 업데이트해야 하는 시점:

1. 새 파일 생성 후
2. 파일 삭제 후
3. 카테고리 변경 후
4. 주기적 (예: 1시간마다)

```python
# 자동 업데이트
after_add_memory():
    update_index()

after_delete_memory():
    update_index()

scheduled_task():  # 1시간마다
    update_index()
``` 
