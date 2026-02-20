---
name: slack-memory-store
description: Comprehensive memory storage system for AI employees in IT companies who communicate via Slack. Automatically classifies and stores diverse information types (Slack messages, Confluence docs, emails, meetings, projects, decisions, feedback) in an organized folder structure with efficient indexing and retrieval. Use when managing or searching employee memory, storing conversations, documenting decisions, tracking projects, or organizing any work-related information.
---

# Slack Memory Store

This skill enables systematic memory management for AI employees operating in IT company environments, primarily through Slack communication.

## Core Capabilities

1. **Auto-classification** - Automatically categorize incoming information into appropriate folders
2. **Multi-format support** - Handle Slack messages, Confluence documents, emails, meeting notes, etc.
3. **Smart indexing** - Maintain up-to-date index.md for rapid information retrieval
4. **Flexible schemas** - Support structured metadata for each information type
5. **CRUD operations** - Create, read, update, and delete memory entries

## Quick Start

### Initialize Memory Structure

Before using the memory system for the first time, initialize the directory structure:

```bash
python scripts/init_memory.py /path/to/memory
```

This creates:
- All required directories (channels/, users/, projects/, etc.)
- Initial index.md with navigation
- Metadata tracking file

### Add New Information

The primary way to add information to memory:

```bash
python scripts/add_memory.py /path/to/memory "Title" "Content" '{"type":"channel", "channel_id":"C123"}'
```

The script will:
1. Analyze the content and metadata
2. Automatically classify into the appropriate directory
3. Generate a clean filename
4. Format with proper YAML frontmatter
5. Save to the correct location

### Update Index

After adding/modifying multiple entries, update the index:

```bash
python scripts/update_index.py /path/to/memory
```

This refreshes:
- Statistics (total channels, users, projects, etc.)
- Recent updates list (10 most recent changes)
- Navigation links

### Search Memory

To find information quickly:

```bash
# Search by content
python scripts/search_memory.py /path/to/memory content "프로젝트"

# Search by tag
python scripts/search_memory.py /path/to/memory tag urgent

# List files in category
python scripts/search_memory.py /path/to/memory category projects
```

## Memory Organization

### Directory Structure

```
memory/
├── index.md              # Main navigation and quick reference
├── channels/             # Slack channel information
│   └── C123_마케팅팀.md
├── users/                # Team member profiles
│   └── U456_김철수.md
├── projects/             # Project status and history
│   ├── 신제품런칭.md
│   └── archive/
├── tasks/                # Completed and ongoing tasks
│   ├── ongoing/
│   └── completed/
├── decisions/            # Decision points and rationale
├── meetings/             # Meeting notes and action items
├── feedback/             # User feedback and suggestions
├── announcements/        # Important announcements
├── resources/            # Internal docs, guides, manuals
├── external/             # External information
│   └── news/
└── misc/                 # Uncategorized information
```

### File Format

Each memory file follows this structure:

```markdown
---
type: channel
channel_id: C01234567
channel_name: "마케팅팀"
participants: [U01234567, U76543210]
tags: [marketing, important]
created: 2025-10-28 10:00:00
updated: 2025-10-28 15:30:00
---

# 마케팅팀 채널

## 커뮤니케이션 지침

- Tone: Professional but friendly
- Response time: Within 1 hour during business hours
- Key topics: Campaign planning, performance metrics

## Recent Discussions

...
```

## Storage Strategy: Hybrid Approach

**CRITICAL**: Use a hybrid strategy to optimize retrieval and file size:

### 1. Profile Files (One Per Entity - UPDATE, Don't Create New)
- **Purpose**: Persistent guidelines, preferences, static info
- **Action**: ALWAYS check if file exists first, then UPDATE it
- **Examples**:
  - `channels/C123_마케팅팀.md` - Channel guidelines, members, communication style
  - `users/U456_김철수.md` - User profile, preferences, work style

### 2. Topic Files (Multiple - CREATE New or UPDATE Existing)
- **Purpose**: Conversations, projects, decisions, meetings
- **Action**: Create new file per topic, or update if same topic continues
- **Examples**:
  - `projects/신제품런칭.md` - Project discussions
  - `decisions/AWS전환_20251117.md` - Important decisions (date-stamped)
  - `meetings/2025-11-17-Q4전략회의.md` - Meeting notes
  - `misc/마케팅팀_일상_20251117.md` - Casual conversations

### 3. Decision Tree for Classification

```
Content type:
├─ Channel/User guidelines or preferences?
│  └─ YES → UPDATE channels/C123_채널명.md or users/U456_유저명.md
│
└─ NO → What's the main topic?
    ├─ Project discussion → projects/프로젝트명.md
    ├─ Important decision → decisions/주제_DATE.md
    ├─ Meeting notes → meetings/DATE-주제.md
    ├─ Casual conversation → misc/채널명_DATE.md (or skip if trivial)
    └─ Task/feedback/announcement → respective directories
```

## Handling Different Content Types

### Slack Conversations

When receiving Slack message threads:

1. **Identify context**: Channel, participants, date range
2. **Extract key info**: Decisions, action items, important discussions
3. **Classify using Hybrid Strategy** (see Decision Tree above):
   - Channel guidelines/preferences → **UPDATE** `channels/C123_채널명.md`
   - User preferences → **UPDATE** `users/U456_유저명.md`
   - Project-focused → **CREATE/UPDATE** `projects/프로젝트명.md`
   - Decision-focused → **CREATE** `decisions/주제_DATE.md`
   - Meeting notes → **CREATE** `meetings/DATE-주제.md`
   - Casual chat → **CREATE** `misc/채널명_DATE.md` (or skip if not important)
4. **Format**: Chronological order, preserve thread structure
5. **Metadata**: channel_id, participants, date_range, message_count, **related_to** (link to profile file)

Example usage:
```python
from scripts.add_memory import MemoryManager

manager = MemoryManager('/path/to/memory')

# Example 1: Topic file (project discussion)
manager.add_memory(
    title="Q4 전략 논의",
    content=formatted_slack_thread,
    metadata={
        'type': 'project',  # Will create projects/Q4전략논의.md
        'channel_id': 'C123',
        'channel_name': '마케팅팀',
        'participants': ['U01', 'U02'],
        'date_range': '2025-10-28',
        'message_count': 25,
        'tags': ['strategy', 'q4'],
        'related_to': ['channels/C123_마케팅팀.md']  # Link to channel profile
    }
)

# Example 2: Profile file (channel guidelines update)
manager.add_memory(
    title="마케팅팀",
    content="Channel guidelines: Professional tone, quick response expected",
    metadata={
        'type': 'channel',  # Will update channels/C123_마케팅팀.md
        'channel_id': 'C123',
        'channel_name': '마케팅팀',
        'guidelines': {'tone': 'professional', 'response_time': '1시간 이내'}
    }
)
```

### Confluence Documents

When importing Confluence documentation:

1. **Convert format**: HTML → Markdown
2. **Preserve structure**: Headers, lists, tables
3. **Add metadata**: source_url, space, last_updated
4. **Classify**: Usually → `resources/` or `projects/`

### Email Threads

When storing email conversations:

1. **Thread structure**: Maintain reply chain
2. **Extract metadata**: From, To, Subject, Date
3. **Classify by content**:
   - Announcements → `announcements/`
   - Project updates → `projects/`
   - Feedback → `feedback/`

### Meeting Notes

When recording meetings:

1. **Structure**: Date, attendees, agenda, discussions, action items
2. **Always goes to**: `meetings/`
3. **Cross-reference**: Link to related projects/decisions
4. **Action items**: Extract and consider adding to `tasks/`

### External News

When saving external articles:

1. **Always goes to**: `external/news/`
2. **Add metadata**: source, source_url, date, relevance
3. **Summarize**: Focus on key points relevant to company
4. **Link**: Connect to related_project if applicable

## Automatic Classification

The system uses a multi-level classification strategy:

### Level 1: Explicit Metadata
If `type` field exists in metadata → use directly

### Level 2: Structural Indicators
- `channel_id` present → `channels/`
- `user_id` present → `users/`
- `project_id` present → `projects/`

### Level 3: Keyword Analysis
Scan content for keywords (see `references/classification-guide.md` for full list):
- "프로젝트", "project", "milestone" → `projects/`
- "결정", "decision", "승인" → `decisions/`
- "회의", "meeting" → `meetings/`
- etc.

### Level 4: Default
If no classification match → `misc/`

## Advanced Features

### Update Existing Memory

To update an existing file:

```python
manager = MemoryManager('/path/to/memory')
manager.update_memory(
    directory='projects',
    filename='신제품런칭.md',
    new_content=updated_content,
    new_metadata={'updated': '2025-10-28 16:00:00', 'status': 'completed'}
)
```

### Cross-referencing

Use `related_to` metadata to link related files:

```yaml
---
type: decision
related_to:
  - projects/신제품런칭.md
  - meetings/2025-10-28-전략회의.md
---
```

### Version Management

If a file with the same name exists, the system automatically:
1. Detects duplicate
2. Adds version suffix: `filename_v2.md`, `filename_v3.md`, etc.

### Search Tips

1. **Content search**: Case-insensitive by default
2. **Tag search**: Find all files with specific tag
3. **Category search**: List all files in a directory
4. **Index search**: Use browser Ctrl+F on index.md for quick keyword lookup

## Best Practices

### 1. Consistent Metadata

Always include at minimum:
- `type`: Content type
- `created`: Creation timestamp
- `tags`: Relevant tags for searchability

### 2. Descriptive Titles

Use clear, descriptive titles:
- ✅ "Q4 마케팅 전략 회의 - 2025-10-28"
- ❌ "미팅"

### 3. Regular Index Updates

Update index after:
- Multiple file additions
- File deletions
- Category changes
- Or at least once per hour

### 4. Use Tags Liberally

Tags improve discoverability:
```yaml
tags: [urgent, marketing, q4, strategy, approval-needed]
```

### 5. Link Related Information

When information is related, add cross-references:
```yaml
related_to:
  - projects/웹사이트리뉴얼.md
  - decisions/디자인시스템선택.md
```

## Reference Documents

For detailed information, see:

- **[data-schemas.md](references/data-schemas.md)** - Complete schemas for all memory types with examples
- **[classification-guide.md](references/classification-guide.md)** - Detailed classification rules and content handling strategies

## Workflow Examples

### Example 1: Storing Slack Discussion

```python
# 1. Format the Slack thread
slack_content = """
## Participants
- @chulsoo (PM)
- @sarah (Designer)

## Discussion
[10:30] chulsoo: 랜딩 페이지 디자인 리뷰 부탁드립니다
[10:35] sarah: 확인했습니다. 전반적으로 좋은데 CTA 버튼이 더 눈에 띄었으면 좋겠어요
...
"""

# 2. Add to memory
manager.add_memory(
    title="랜딩 페이지 디자인 리뷰",
    content=slack_content,
    metadata={
        'type': 'project',
        'channel_id': 'C123',
        'project': '신제품런칭',
        'participants': ['U01', 'U02'],
        'tags': ['design', 'review', 'landing-page']
    }
)

# 3. Update index
update_index()
```

### Example 2: Quick Information Lookup

```bash
# Find all files related to "신제품"
python scripts/search_memory.py /memory content "신제품"

# Results show:
# 1. projects/신제품런칭.md
# 2. meetings/2025-10-15-신제품기획회의.md
# 3. decisions/신제품가격결정.md
```

### Example 3: Tracking Project Progress

```python
# Initial project setup
manager.add_memory(
    title="신제품 런칭 프로젝트",
    content="""
## Overview
AI 기반 추천 시스템 개발 및 런칭

## Milestones
- [ ] MVP 개발 (2025-11-30)
- [ ] 베타 테스트 (2025-12-15)
- [ ] 정식 출시 (2025-12-31)
    """,
    metadata={
        'type': 'project',
        'status': 'in_progress',
        'priority': 'high',
        'participants': ['U01', 'U02', 'U03']
    }
)

# Later: Update progress
manager.update_memory(
    'projects',
    '신제품런칭프로젝트.md',
    updated_content_with_progress,
    {'updated': '2025-10-28', 'status': 'on_track'}
)
```

## Troubleshooting

### Issue: Files not found by search
**Solution**: Ensure filename ends with `.md` and is not `index.md`

### Issue: Wrong classification
**Solution**: Provide explicit `type` in metadata or add more specific keywords to content

### Issue: Index out of date
**Solution**: Run `update_index.py` manually

### Issue: Duplicate files
**Solution**: System automatically handles by adding version suffix (_v2, _v3, etc.)

## Performance Considerations

- **Index updates**: O(n) where n = total files. Run after batch operations, not after each file
- **Search**: O(n) linear scan. For large datasets (>1000 files), consider adding full-text search
- **File size**: Keep individual files under 100KB for optimal performance

## Integration Notes

This skill is designed to work seamlessly with:
- Slack API integrations for automatic message capture
- Confluence API for document import
- Gmail API for email archiving
- Calendar APIs for meeting notes
- Any custom data sources via the flexible add_memory interface

The memory structure is AI-agent-friendly: index.md provides rapid overview, and all content is in Markdown for easy parsing and understanding. 
