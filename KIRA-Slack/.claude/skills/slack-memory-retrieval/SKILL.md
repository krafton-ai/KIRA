---
name: slack-memory-retrieval
description: Retrieve and utilize stored memories for AI employees in Slack environments. Efficiently searches and loads relevant context (channels, users, projects, decisions, meetings) from organized memory storage to inform responses. Use this when answering questions that require historical context, user preferences, project status, or any previously stored information. Works with slack-memory-store storage system.
---

# Slack Memory Retrieval

This skill enables AI employees to efficiently retrieve and utilize stored memories to provide context-aware responses in Slack conversations.

## Core Purpose

Retrieve relevant memories from `{memories_path}` to inform the next response with appropriate context about people, projects, decisions, preferences, and work history.

## Quick Start

### Basic Workflow

Every memory retrieval follows this pattern:

1. **Analyze context** - Extract channel, user, keywords from conversation
2. **Read index.md** - Get overview of available memories
3. **Identify relevant files** - Based on context and index
4. **Load memories** - Read specific files needed
5. **Synthesize response** - Combine memories with current context

### Example: Simple Query

```
User (in #마케팅팀): "Q4 전략 어떻게 되고 있어?"

Step 1: Context Analysis
- Channel: #마케팅팀 (C123)
- Keywords: Q4, 전략

Step 2: Read Index
view {memories_path}/index.md
→ See Recent Updates, locate Q4-related items

Step 3: Load Relevant Files
view {memories_path}/channels/C123_마케팅팀.md
view {memories_path}/projects/Q4전략.md
view {memories_path}/meetings/ (find Q4 meetings)

Step 4: Respond
Synthesize information from channel context, project status, and meeting notes
```

## Memory Structure

The memory system uses a **hybrid approach**:

### Profile Files (One Per Entity)
- `channels/C123_마케팅팀.md` - Channel guidelines, preferences, static info
- `users/U456_김철수.md` - User profile, communication style

### Topic Files (Multiple Per Category)
- `projects/신제품런칭.md` - Project discussions
- `decisions/AWS전환_20251117.md` - Important decisions
- `meetings/2025-11-17-Q4회의.md` - Meeting notes
- `misc/마케팅팀_일상_20251117.md` - Casual conversations

### Directory Structure

```
{memories_path}/
├── index.md              # START HERE - navigation and stats
├── channels/             # Channel profile files (one per channel)
├── users/                # User profile files (one per user)
├── projects/             # Project topic files (multiple)
├── tasks/                # Task records
├── decisions/            # Decision records (date-stamped)
├── meetings/             # Meeting notes (date-stamped)
├── feedback/             # User feedback
├── announcements/        # Important announcements
├── resources/            # Internal docs and guides
├── external/news/        # External information
└── misc/                 # Uncategorized conversations
```

## Essential Rules

### Always Start with Index

**CRITICAL**: Every retrieval session must begin by reading index.md:

```bash
view {memories_path}/index.md
```

The index provides:
- Navigation structure
- Statistics (total channels, users, active projects)
- Recent updates (10 most recent changes)
- Quick links to key information

This one-time read gives you the complete map of available memories.

### Context-Driven Retrieval

Extract context from the conversation:

**Channel Context:**
```
Message in #마케팅팀 
→ Load: {memories_path}/channels/C123_마케팅팀.md
→ Check related_to metadata for connected info
```

**User Context:**
```
DM from @chulsoo
→ Load: {memories_path}/users/U123_김철수.md
→ Get communication_style, preferences
```

**Project Context:**
```
Question about "신제품 런칭"
→ Load: {memories_path}/projects/신제품런칭.md
→ Check milestones, status, participants
```

**Keyword Context:**
```
Question mentions "결정", "승인"
→ Search: {memories_path}/decisions/
→ Find relevant decision files
```

### Efficient Loading Strategy

**Tier 1: Always Load (if relevant)**
- index.md (overview)
- Current channel file (if in channel)
- Current user file (if DM or mentioned)

**Tier 2: Load as Needed**
- Project files (if project mentioned)
- Decision files (if asking about decisions)
- Meeting notes (if asking about meetings)

**Tier 3: Load Selectively**
- Tasks (only if specifically asked)
- Resources (only if referenced)
- External news (only if relevant)

Don't over-fetch. Use directory listings first:
```bash
view {memories_path}/projects/
# See available projects before loading specific files
```

## Retrieval Patterns

### Pattern 1: Channel Response

When responding in a channel:

```bash
# 1. Load channel context
view {memories_path}/channels/{channel_id}_{channel_name}.md

# 2. Check for channel guidelines
# Extract: tone, response_time, key_topics

# 3. Apply guidelines to response
# Adjust tone, format based on channel preferences
```

### Pattern 2: User-Specific Response

When responding to a specific user:

```bash
# 1. Load user profile
view {memories_path}/users/{user_id}_{name}.md

# 2. Check communication_style
# Extract: tone, detail_level, preferences

# 3. Personalize response
# Match user's preferred style and detail level
```

### Pattern 3: Project Status Query

When asked about project status:

```bash
# 1. Find project file
view {memories_path}/projects/
view {memories_path}/projects/{project_name}.md

# 2. Check metadata
# status, priority, milestones, participants

# 3. Get related info
# Check related_to for decisions, meetings

# 4. Provide comprehensive update
# Current status + recent activity + next steps
```

### Pattern 4: Decision History

When asked about past decisions:

```bash
# 1. Search decisions
view {memories_path}/decisions/

# 2. Load relevant decision file
view {memories_path}/decisions/{decision_name}.md

# 3. Extract key info
# decision_makers, rationale, alternatives_considered

# 4. Explain context
# Why decision was made + alternatives + outcome
```

### Pattern 5: Task History

When asked about completed work:

```bash
# 1. Check completed tasks
view {memories_path}/tasks/completed/

# 2. Filter by assignee/date
# Look for relevant assignee, date range

# 3. Summarize work
# List tasks + effort + outcomes
```

## Advanced Techniques

### Cross-Referencing

Follow the trail of related information:

```yaml
# In project file:
---
related_to:
  - decisions/기술스택선택.md
  - meetings/2025-10-20-기획회의.md
---
```

Load related files to build complete context.

### Metadata Filtering

Use metadata to filter without reading entire files:

```bash
# List directory first
view {memories_path}/projects/

# Check filenames and metadata
# Only load files matching criteria:
# - status: in_progress
# - priority: high
# - participants: includes current_user
```

### Temporal Context

Consider time-sensitivity:

```bash
# Recent Updates in index.md
→ Shows 10 most recent changes
→ Focus on these for "latest" questions

# File metadata: created, updated
→ Check dates to prioritize fresh info
```

### Tag-Based Discovery

Use tags for discovery:

```yaml
tags: [urgent, marketing, q4, approval-needed]
```

When user asks about "urgent items":
- Scan files for tags: urgent
- Collect across categories
- Present by priority

## Response Construction

### Synthesize, Don't Dump

**❌ Bad:**
```
"According to channels/마케팅팀.md, the response time is 1 hour.
According to projects/Q4전략.md, the status is in_progress.
According to meetings/기획회의.md..."
```

**✅ Good:**
```
"Q4 마케팅 전략은 현재 진행 중이며, 지난 기획회의에서 
주요 방향을 확정했습니다. 현재 MVP 개발 단계에 있고..."
```

Synthesize information naturally without explicitly citing sources.

### Apply Context Appropriately

**Channel Guidelines:**
If channel specifies "간결한 답변", keep response concise.

**User Preferences:**
If user prefers "bullet points", format accordingly.

**Project Status:**
Include relevant status without over-explaining.

### Maintain Conversational Flow

Integrate memories seamlessly into natural conversation:

```
User: "이번 주 미팅 어땠어?"

Response: "화요일 기획회의에서 신규 기능 3개를 최종 확정했어요. 
전반적으로 개발 일정에 대한 우려가 있었지만, 리소스 조정으로 
해결 가능할 것으로 보입니다."

(Draws from: meetings/기획회의.md + projects/신규기능.md)
```

## Important Guardrails

### What to Retrieve

✅ **Do retrieve:**
- Channel communication guidelines
- User preferences and profiles
- Project status and history
- Decision rationale and history
- Meeting notes and action items
- Completed task history
- Feedback and suggestions
- Resource documents

### What NOT to Retrieve

❌ **Don't retrieve:**
- Information outside {memories_path}
- System configuration files
- Scheduling requests (handled by scheduler agent)
- Agent identity info (name, org, team)

### Privacy and Access

- Only access files within {memories_path}
- Don't share sensitive information inappropriately
- Respect access_level metadata if present

### Efficiency

- Don't load unnecessary files
- Use directory listings before file reads
- Start with index.md, not individual files
- Follow the efficient loading strategy (Tier 1 → Tier 2 → Tier 3)

## Troubleshooting

### Issue: Can't find relevant memory

**Solution:**
1. Check index.md for recent updates
2. Search broader category (e.g., misc/)
3. Check related_to in similar files
4. Inform user if information not available

### Issue: Conflicting information

**Solution:**
1. Prioritize newer information (check updated timestamp)
2. Consider context of each source
3. Mention both perspectives if relevant

### Issue: Too much information

**Solution:**
1. Prioritize by relevance to current question
2. Summarize rather than detail
3. Focus on actionable insights

### Issue: Memory seems outdated

**Solution:**
1. Check updated timestamp
2. Look for newer related files
3. Note timeframe in response
4. Suggest updating if critical

## Integration with Memory Management

This skill works in tandem with `slack-memory-store`:

**Memory Management (separate agent):**
- Stores new information
- Updates existing memories
- Maintains index

**Memory Retrieval (this skill):**
- Reads stored information
- Finds relevant context
- Informs responses

These are complementary skills for a complete memory system.

## Best Practices Summary

1. **Always start with index.md** - Get the map before exploring
2. **Extract context first** - Channel, user, keywords guide retrieval
3. **Load efficiently** - Directory listing → relevant files only
4. **Follow references** - Use related_to metadata
5. **Synthesize naturally** - Don't cite sources explicitly
6. **Apply preferences** - Use channel/user guidelines
7. **Stay current** - Prioritize recent updates
8. **Don't over-fetch** - Load what you need
9. **Respect guardrails** - Stay within {memories_path}
10. **Provide value** - Context-aware, relevant responses

## Reference Documents

For detailed retrieval patterns and techniques:

- **[retrieval-patterns.md](references/retrieval-patterns.md)** - 10 detailed patterns for different scenarios with step-by-step examples

## Example Workflows

### Example 1: Morning Briefing

```
User (DM): "오늘 뭐부터 시작하면 좋을까?"

# 1. Load user profile
view {memories_path}/users/U123_김철수.md
→ Get role: PM, team: Product

# 2. Load index
view {memories_path}/index.md
→ Check Recent Updates

# 3. Check ongoing tasks
view {memories_path}/tasks/ongoing/
→ Find tasks assigned to U123

# 4. Check active projects
view {memories_path}/projects/
→ Filter by participants including U123

Response: "오늘은 Q4 전략 최종안 검토가 가장 시급해 보입니다. 
오후 3시 승인 회의가 예정되어 있어서, 오전 중에 마무리하시면 좋을 것 같아요. 
그 외 신제품 기획서 작성도 진행 중이신데, 이번 주 금요일까지시니 여유가 있습니다."
```

### Example 2: Project Status Check

```
User (in #개발팀): "웹사이트 리뉴얼 어디까지 왔어?"

# 1. Load channel context
view {memories_path}/channels/C456_개발팀.md

# 2. Load index
view {memories_path}/index.md

# 3. Find project
view {memories_path}/projects/웹사이트리뉴얼.md
→ Get status, milestones, recent updates

# 4. Check related decisions
→ Follow related_to metadata

# 5. Check recent meetings
view {memories_path}/meetings/
→ Find recent discussions about this project

Response: "웹사이트 리뉴얼은 현재 70% 진행됐습니다. 
프론트엔드 개발은 완료됐고, 백엔드 API 통합 작업 중이에요. 
지난주 회의에서 디자인 시스템을 확정했고, 다음 주 화요일 
내부 테스트 예정입니다."
```

### Example 3: Decision Inquiry

```
User: "React vs Vue 어떻게 결정했었지?"

# 1. Load index
view {memories_path}/index.md

# 2. Search decisions
view {memories_path}/decisions/
→ Find "프론트엔드프레임워크선택.md"

# 3. Load decision file
view {memories_path}/decisions/프론트엔드프레임워크선택.md
→ Get decision_makers, alternatives, rationale

# 4. Check related meetings
→ Follow related_to for meeting notes

Response: "React를 선택했습니다. 9월 기술 검토 회의에서 
Vue도 고려했지만, 팀의 기존 React 경험과 생태계의 풍부함을 
이유로 React로 결정했어요. 특히 TypeScript 지원과 
대규모 커뮤니티가 주요 요인이었습니다."
```

## Performance Tips

**Tip 1: Batch Directory Reads**
```bash
# Once per session
view {memories_path}/projects/
view {memories_path}/channels/
# Then reference from memory
```

**Tip 2: Use Index Effectively**
```bash
# Index Recent Updates = quick scan of active areas
# No need to check every directory
```

**Tip 3: Smart Caching**
```bash
# Within a conversation:
# - Load channel context once
# - Load user profile once
# - Reuse for subsequent messages
```

**Tip 4: Selective Loading**
```bash
# If user asks "quick status":
# → Load index + 1-2 key files
# If user asks "detailed report":
# → Load index + multiple related files
```

---

This skill transforms stored memories into actionable context, enabling AI employees to provide informed, personalized, and context-aware responses in every interaction. 
