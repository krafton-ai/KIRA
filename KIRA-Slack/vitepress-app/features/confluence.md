# Confluence Tracking

KIRA automatically tracks Confluence document updates and saves important changes to memory.

::: tip Beta Feature
Confluence tracking is currently in beta. Requires [Atlassian Setup](/setup/atlassian).
:::

## 📄 How It Works

### 1. Automatic Check
Automatically checks recently updated Confluence pages at configured intervals (default: 60 minutes).

### 2. Importance Assessment
AI analyzes updated pages to determine if they contain important content.

**Importance criteria:**
- Project-related documents
- Technical specs/API documents
- Decision documents
- Team guidelines

### 3. Memory Storage
Important pages are summarized and saved to KIRA's memory. When related questions come up later, KIRA uses this stored information to respond.

---

## ⚙️ Setup

### How to Enable
1. Complete [Atlassian Setup](/setup/atlassian)
2. KIRA App > Environment Variables
3. **Active Channel - Confluence** section
4. Turn on **Confluence Check Enabled** toggle
5. Save settings and restart server

---

## ❓ Next Steps

- [Jira Tracking](/features/jira) - Automatic Jira task execution
- [Memory System](/features/memory) - How to use memory
- [Proactive Suggestions](/features/proactive) - AI auto-suggestions
