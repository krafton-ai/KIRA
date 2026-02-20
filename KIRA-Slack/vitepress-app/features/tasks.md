# Task Execution

KIRA automates complex work by combining various tools.

## 🎁 Built-in Features (No Setup Required)

KIRA includes features that work out of the box without any additional setup.

### 📄 Document Creation

| Feature | Description | Example Request |
|---------|-------------|-----------------|
| **PDF** | Create, edit PDFs, extract text/tables | "Create meeting notes as PDF" |
| **Excel (xlsx)** | Create spreadsheets, formulas, data analysis | "Organize sales data in Excel" |
| **PowerPoint (pptx)** | Create presentations, edit slides | "Create a project intro PPT" |
| **Word (docx)** | Write documents, edit, format | "Write the report as a Word file" |

::: tip File Save Location
Created documents are saved to `~/Documents/KIRA/files/` and can be sent directly to Slack.
:::

### 🔍 Information Search Services

| Service | Description | Example Request |
|---------|-------------|-----------------|
| **Context7** | Latest library/framework documentation | "Tell me about React 19 new features" |
| **arXiv** | Analyze and summarize arXiv paper URLs | "Analyze this paper: arxiv.org/abs/..." |
| **YouTube Info** | YouTube video information | "Summarize this YouTube video" |
| **Steam Review** | Steam game review analysis | "Analyze reviews for this game" |
| **Airbnb** | Airbnb accommodation search | "Find accommodations near Gangnam, Seoul" |
| **Time** | Current time, timezone conversion | "What time is it in New York?" |

::: info No Additional Setup Required
These features are automatically included with KIRA installation - no API keys or configuration needed.
:::

---

## 🛠️ MCP Tools (Setup Required)

Additional tools are available with configuration. See the [Setup Guide](/setup/).

| Tool | Key Functions |
|------|--------------|
| **Perplexity** | Real-time web search, latest info lookup |
| **MS365** | Email read/send, calendar, OneDrive, SharePoint |
| **Confluence** | Document search/create/edit |
| **Jira** | Issue query/create/status change |
| **GitHub/GitLab** | Repository, issues, PR/MR management |
| **DeepL** | Document translation |
| **X (Twitter)** | Tweet creation/publishing |
| **Tableau** | Dashboard query, data visualization |
| **Clova Speech** | Speech→text conversion, meeting notes |

---

## 💡 Use Cases

### 📊 Weekly Task Automation

**Auto-generate weekly report every Friday**
```
User: Write weekly report every Friday at 5pm and share in team channel

KIRA: [Auto-run Friday 17:00]
      1. Query completed/in-progress issues from Jira
      2. Query merged MRs from GitLab this week
      3. Search key discussions from memory
      4. Compile weekly report
      5. Create Confluence page
      6. Share summary in Slack team channel
```

**Daily morning briefing**
```
User: Summarize today's tasks every day at 9am

KIRA: [Auto-run daily 09:00]
      1. Query today's schedule from Outlook
      2. Query issues assigned to me from Jira
      3. Check emails requiring replies
      4. Compile today's task list
      5. Send briefing via DM
```

---

### 📧 Email-Based Task Processing

**Email request → Jira ticket → Notify assignee**
```
User: Process bug report email from client

KIRA: 1. Query bug report email from Outlook
      2. Analyze content and create Jira issue
         - Title: [Client] Login error occurred
         - Priority: P1
         - Assignee: Dev team
      3. Notify assignee via Slack
      4. Send acknowledgment email to client
```

**Multilingual email auto-translation and reply**
```
User: Translate the English email and draft a reply in Korean

KIRA: 1. Query English email from Outlook
      2. Translate to Korean via DeepL
      3. Draft reply (Korean)
      4. Translate to English via DeepL
      5. Save as email draft
```

---

### 📄 Document Automation

**Meeting notes → Confluence → Jira action items**
```
[Upload meeting recording on web interface]

KIRA: 1. Convert speech to text via Clova Speech
      2. Format into meeting notes
         - Attendees, discussions, decisions
      3. Create Confluence meeting notes page
      4. Extract action items
      5. Create Jira issues for each assignee
      6. Share meeting notes link via Slack
```

**Confluence document translation and sharing**
```
User: Translate API docs to English and share with global team

KIRA: 1. Query API docs from Confluence
      2. Translate to English via DeepL
      3. Create English page on Confluence
      4. Share link in global team channel
```

---

### 🔍 Research and Information Gathering

**Competitor analysis report**
```
User: Research latest news about competitor A and summarize

KIRA: 1. Search competitor A news via Perplexity
      2. Summarize key content
      3. Update competitor analysis page on Confluence
      4. Notify relevant team via Slack
```

**Tech research and documentation**
```
User: Research Next.js 15 new features and document in team wiki

KIRA: 1. Search Next.js 15 features via Perplexity
      2. Organize official docs content
      3. Analyze applicable parts for our project
      4. Create tech research page on Confluence
```

---

### 📈 Data Analysis and Reporting

**Tableau dashboard analysis and sharing**
```
User: Capture this month's sales dashboard and report to executives

KIRA: 1. Query sales dashboard from Tableau
      2. Analyze key metrics (MoM, YoY)
      3. Generate dashboard image
      4. Compose email with analysis
      5. Send to executives via Outlook
```

---

### 🔄 Development Workflow

**PR review request automation**
```
User: Request review for my PR

KIRA: 1. Query my open MRs from GitLab
      2. Summarize changes
      3. Auto-assign reviewers (reference team info from memory)
      4. Send review request via Slack
```

**Post-deploy notification and doc update**
```
User: Handle post v2.0 deployment tasks

KIRA: 1. Query v2.0 tag and changes from GitLab
      2. Write release notes
      3. Update release docs on Confluence
      4. Mark related issues as Done in Jira
      5. Post deployment announcement in team channel
```

---

### 📱 Social Media Management

**Tweet series scheduling**
```
User: Create 3 tweets about new product launch and post tomorrow morning hourly

KIRA: 1. Query product info from memory
      2. Draft 3 tweets
      3. Register schedule:
         - 09:00 Tweet #1
         - 10:00 Tweet #2
         - 11:00 Tweet #3
      4. Slack notification after posting
```

---

### ⏰ Regular Task Schedule Examples

```
# Daily Tasks
Daily 09:00 - Today's schedule and task briefing
Daily 18:00 - Today's work summary

# Weekly Tasks
Every Monday 09:00 - Weekly planning (Jira + Calendar based)
Every Friday 17:00 - Weekly report writing and Confluence posting

# Monthly Tasks
1st of month 09:00 - Monthly KPI report (Tableau + Jira integration)
Last day of month 17:00 - Next month's goals summary

# Project-specific
Every Wednesday 14:00 - Project A progress check
1 day before deadline - Final review and risk analysis
```

---

## 🚀 Getting Started

1. Complete required [MCP Setup](/setup/)
2. Request desired tasks from KIRA in Slack
3. Automate repetitive tasks with scheduling

::: tip Request in Natural Language
Just say "Write weekly report every Friday" naturally.
KIRA will figure out which tools to combine and handle it.
:::

---

## ❓ Next Steps

- [Scheduling](/features/scheduling) - Automate repetitive tasks
- [Memory System](/features/memory) - Leverage context
- [Email Monitoring](/features/email-monitoring) - Auto task execution
