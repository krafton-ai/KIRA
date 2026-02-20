# Jira Tracking

KIRA automatically checks assigned Jira issues and executes tasks directly.

::: tip Beta Feature
Jira tracking is currently in beta. Requires [Atlassian Setup](/setup/atlassian).
:::

## 🐛 How It Works

### 1. Automatic Check
Automatically checks uncompleted Jira issues assigned to you at configured intervals (default: 30 minutes).

### 2. Task Extraction
AI analyzes tickets and extracts specific tasks to perform.

**Extraction targets:**
- Code review
- Test writing
- Bug fixing
- Documentation
- Deployment tasks

### 3. Task Execution
KIRA directly executes extracted tasks. Not just notifications, but actual work processing, and marks tickets as Done when complete.

**Examples:**
- "Code review request" → Review code and write feedback
- "Update documentation" → Modify Confluence document
- "Research materials" → Web search and compile results

---

## ⚙️ Setup

### How to Enable
1. Complete [Atlassian Setup](/setup/atlassian)
2. KIRA App > Environment Variables
3. **Active Channel - Jira** section
4. Turn on **Jira Check Enabled** toggle
5. Save settings and restart server

---

## ❓ Next Steps

- [Email Monitoring](/features/email-monitoring) - Automatic email task execution
- [Task Execution](/features/tasks) - Jira task automation
- [Proactive Suggestions](/features/proactive) - AI auto-suggestions
