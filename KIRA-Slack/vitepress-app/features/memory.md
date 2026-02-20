# Memory System

KIRA automatically remembers and utilizes important information.

## 🧠 Memory Structure

### Local File System
All memory is stored as Markdown files on your computer.

```
~/Documents/KIRA/memories/
├── channels/          # Per-channel conversation history
├── projects/          # Project information
├── users/            # Per-user information
├── decisions/        # Important decisions
└── index.md          # Auto-generated index
```

---

## 👤 Per-User Memory

### Personal Preferences
KIRA recognizes each user individually and remembers preferences.

### Per-User Work History
Manages each user's work history separately.

---

## 🤝 Context Sharing

### Team Collaboration Scenario
Everyone shares conversation context from channel discussions.

---

## 📚 Auto Save

### Auto Save During Conversation
Important information is automatically saved to memory during conversations.

**Auto-saved information:**
- Project-related discussions
- Important decisions
- User preferences
- Task assignments and schedules

---

## 🔍 Intelligent Search

### Auto-Reference During Task Execution
KIRA automatically finds and uses relevant memory when performing tasks.

```
User: Send status update email to project lead

KIRA: [Auto-search memory]
      - Project: Project Alpha
      - Lead: Bob Lee (bob@company.com)
      - Current status: Development phase

      Drafting status update email to Bob...
```

---

## 🔐 Data Security

### Local Storage
- All memory stored only on your computer
- Not transmitted to external servers
- Stored as files for easy backup and transfer

---

## 🚀 Memory Initialization Guide

Building memory systematically when first using KIRA makes it much more effective.

### Step 1: Save Team Member Info
Tag team members in a channel and KIRA auto-collects info:

```
User: @KIRA Remember our team members
      @John Doe @Jane Smith @Bob Lee

KIRA: [Collect info via Slack MCP]
      - Name, email, Slack ID
      - Profile photo, title (if available)

      Remembered 3 team members!
```

**Later usage:**
```
User: Send email to John

KIRA: [Auto-recognize from memory]
      I'll send email to john@company.com.
      What's the content?
```

### Step 2: Teach Organization Structure
Explain your organization structure and roles:

```
User: KIRA, remember our org structure
      - CEO: John Doe (john@company.com)
      - CTO: Jane Smith (jane@company.com)
      - Dev Lead: Bob Lee (bob@company.com)
      - I'm on the dev team

KIRA: Got it! I've recorded the org structure.
      [Saved to memory]
```

### Step 3: Share Project Info
Tell KIRA about ongoing projects:

```
User: KIRA, we're working on "Project Alpha"
      Team: Me and Bob
      Period: 2025-01-01 ~ 2025-03-31
      Goal: New feature development

KIRA: Recorded Project Alpha info!
```

### Step 4: Remember Confluence Docs
Share links and ask to remember important documents:

```
User: KIRA, read and remember this Confluence doc
      https://confluence.company.com/display/TEAM/API-Guidelines

KIRA: [Read doc via Confluence MCP]
      Read and saved API guidelines doc to memory.

      Key points:
      - REST API principles
      - Naming conventions
      - Error handling methods
      ...
```

::: tip Benefits of Building Memory
Building memory early enables:
- Recognize people without tagging
- "Send email to John" → auto-recognize email address
- Auto-reference project context
- Use info instantly without searching docs
:::

---

## 🛠️ Memory Management

### Edit Memory
Fix incorrect or changed information:

```
User: KIRA, update John's email
      Old: john@company.com
      New: john.doe@newcompany.com

KIRA: Updated John Doe's email address.
      john@company.com → john.doe@newcompany.com
```

### Delete Memory
Remove unnecessary information:

```
User: KIRA, Bob left the company. Remove from memory

KIRA: Removed Bob Lee's info from memory.
```

### Query Memory
Check stored information:

```
User: KIRA, tell me about Project Alpha

KIRA: [Memory search]
      Project Alpha:
      - Team: You, Bob
      - Period: 2025-01-01 ~ 2025-03-31
      - Goal: New feature development
      - Status: In progress
```

---

## 💬 Memory Usage Examples

Once memory is built up, KIRA automatically understands context and works smarter.

### Using Team Member Info
```
User: Ask John if he can attend today's meeting

KIRA: [Auto-search John Doe from memory]
      I'll send a Slack DM to John Doe.

      "Hi John, are you available for today's meeting?"

      Should I send it?
```

### Using Project Context
```
User: What was decided in last week's meeting?

KIRA: [Search Project Alpha related memory]
      Last week's meeting (Dec 10) decisions:
      1. API design confirmed as REST
      2. 1st milestone extended to Dec 31
      3. Bob reassigned to frontend
```

### Using Organization Structure
```
User: Who do I need approval from for this?

KIRA: [Reference org structure memory]
      The approver for Project Alpha is
      CTO Jane Smith.

      Should I send an approval request email to Jane?
```

### Using Document Info
```
User: What was the API error code convention again?

KIRA: [Reference saved API guidelines]
      API error code conventions:
      - 4xx: Client errors
      - 5xx: Server errors
      - Custom codes start from 1000

      (Source: API-Guidelines doc)
```

---

## 🧹 Memory Cleanup

Over time, duplicate or outdated information can accumulate. Use the memory cleanup feature to keep things organized.

### Request Memory Cleanup
```
User: KIRA, clean up memory

KIRA: I'll analyze and organize your memory.

      Cleanup results:
      - Merged 3 duplicate files
      - Moved 2 misclassified files (users/ → tasks/)
      - Deleted 5 outdated temp files

      Total: 97 → 87 files
```

### Cleanup Specific Folder
```
User: Clean up just the users folder

KIRA: Analyzing users/ folder.

      Issues found:
      - 3 files for John Doe (1 profile + 2 task records)

      Should I move the 2 task records to tasks/ folder?
```

::: tip Memory Cleanup Principles
- **users/**: Keep only 1 profile file per person
- **channels/**: Keep only 1 file per channel
- **tasks/**: Store task records separately
- Confirm before deleting important info
:::

---

## 💡 Tips for Building Effective Memory

### 1. Use Slack Tags to Remember Team Members

**❌ Less effective:**
```
User: Remember John
```

**✅ More effective:**
```
User: Remember @John Doe. He's a backend developer on the dev team.

KIRA: [Auto-collect info from Slack]
      - Slack ID: U01234567
      - Email: john@company.com
      - Name: John Doe

      Saved John Doe's info!
```

::: tip Benefits of Slack Tags
Tagging auto-collects Slack ID and email, so later "Send email to John" automatically finds the address.
:::

### 2. Include Relationships and Context

```
User: KIRA, here's Project Beta info
      - Team: Me, John, Jane
      - John is PM, Jane is designer
      - Our Slack channel is #project-beta
      - Related docs: [Confluence link]
```

### 3. Be Clear When Updating

```
User: John moved from dev team to planning team.
      Update the memory.
```

### 4. Periodically Check Memory

```
User: KIRA, show me the team member info I told you
```

::: warning Memory Quality = Response Quality
KIRA's response quality is proportional to stored memory quality.
The more accurate and specific information you provide, the smarter it works.
:::

---

## ❓ Next Steps

- [Chat](/features/chat) - Effective communication
- [Task Execution](/features/tasks) - Tasks using memory
- [Proactive Suggestions](/features/proactive) - Memory-based auto suggestions
