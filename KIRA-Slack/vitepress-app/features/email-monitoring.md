# Email Monitoring

KIRA automatically checks Outlook emails and executes assigned tasks.

::: tip Beta Feature
Email monitoring is currently in beta. Requires [MS365 Setup](/setup/ms365).
:::

## 📧 How It Works

### 1. Automatic Check
Automatically checks unread emails in inbox at configured intervals (default: 5 minutes).

### 2. Task Extraction
AI analyzes emails and extracts tasks assigned to KIRA.

**Extraction targets:**
- Meeting scheduling requests
- Document review/writing requests
- Feedback requests
- Research/information requests
- Approval requests

### 3. Task Execution
KIRA directly executes extracted tasks. Not just notifications, but actual work processing.

**Examples:**
- "Please schedule a meeting" → Check calendar and coordinate schedule
- "Please review the report" → Review document and write feedback
- "Please research this" → Web search and compile results

---

## ⚙️ Setup

### How to Enable
1. Complete [MS365 Setup](/setup/ms365)
2. KIRA App > Environment Variables
3. **Active Channel - Outlook** section
4. Turn on **Outlook Check Enabled** toggle
5. Save settings and restart server

---

## ❓ Next Steps

- [Jira Tracking](/features/jira) - Automatic Jira task execution
- [Confluence Tracking](/features/confluence) - Document update monitoring
- [Proactive Suggestions](/features/proactive) - AI auto-suggestions
