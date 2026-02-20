# Confluence & Jira

Integrating Atlassian Rovo MCP allows KIRA to manage Confluence and Jira.

## 📋 Prerequisites

- Atlassian account
- Confluence and/or Jira access permissions

---

## 🎯 Key Features

### Confluence
- Read/search pages
- Create/edit pages
- View page history
- Manage attachments

### Jira
- Query/search issues
- Create/edit issues
- Add comments
- Change status

---

## ⚙️ Step 1: Configure KIRA

### 1. Launch KIRA App
Open the Environment Variables tab.

### 2. Find Atlassian Section
**MCP Settings** > **Atlassian (Jira/Confluence)**

### 3. Enable Setting
- Turn the toggle switch **ON**

### 4. Enter Site URLs

**ATLASSIAN_CONFLUENCE_SITE_URL**
- Enter your Confluence site URL
- Example: `https://your-company.atlassian.net`
- Or: `https://confluence.company.com` (Self-hosted)

**ATLASSIAN_JIRA_SITE_URL**
- Enter your Jira site URL
- Example: `https://your-company.atlassian.net`
- Or: `https://jira.company.com` (Self-hosted)

::: tip Cloud vs Self-hosted
- **Atlassian Cloud**: `https://yourname.atlassian.net` format
- **Self-hosted (Server/Data Center)**: Uses company domain
:::

**ATLASSIAN_CONFLUENCE_DEFAULT_PAGE_ID** (Optional)
- Default page ID for "put this on wiki" requests
- Find in Confluence page URL
- Example: `https://...atlassian.net/wiki/spaces/ABC/pages/782407271/...`
  - → Page ID: `782407271`

### 5. Save Settings
- Click **"Save Settings"** button
- Restart server

---

## ✅ Step 2: Complete Authentication with Test Question

After saving settings and starting the server, complete authentication by asking a **test question**.

### Test Question Example
Ask KIRA in Slack:

```
Show me recently updated Confluence pages
```

Or for Jira:
```
Show me my assigned Jira issues
```

### Authentication Process
1. When KIRA **first accesses** Atlassian, a browser opens automatically
2. **Log in with your account** on the Atlassian login page
3. **Permission approval screen**:
   - Confluence read/write
   - Jira read/write
4. Click **"Accept"**
5. After authentication, you can **close the browser**
6. Return to Slack and KIRA will respond with results

::: warning Authentication on KIRA's Computer
The browser opens on the **computer where KIRA is running**. If running on your own computer, you can authenticate directly.
:::

::: tip One-Time Authentication
OAuth tokens are stored securely, and authentication is automatic thereafter.
Tokens are auto-refreshed when expired.
:::

---

## 🎯 Usage Examples

### Confluence Page Search
```
User: Search Confluence for "API documentation"
KIRA: [Confluence search]
      1. API Usage Guide
      2. REST API Documentation
      3. GraphQL API Reference
```

### Confluence Page Read
```
User: Show me the "API Usage Guide" page content
KIRA: [Confluence query]
      # API Usage Guide

      ## Overview
      ...
```

### Confluence Page Creation
```
User: Create Confluence page
      Title: New Feature Description
      Content: ## Feature Overview...
KIRA: [Confluence created] Page created.
      https://...atlassian.net/wiki/spaces/.../pages/123456
```

### Jira Issue Query
```
User: Show me my assigned Jira issues
KIRA: [Jira query]
      1. ABC-123: Fix login bug
      2. ABC-124: New feature development
```

### Jira Issue Creation
```
User: Create Jira issue
      Project: ABC
      Title: UI improvement needed
      Description: Main page UI needs improvement
KIRA: [Jira created] Created issue ABC-125.
```

### Jira Issue Status Change
```
User: Change ABC-123 issue to "In Progress"
KIRA: [Jira update] Changed status of ABC-123.
```

---

## 🔧 Troubleshooting

### OAuth browser doesn't open
- Check firewall for port 8000 blocking
- Verify web interface is enabled
- Check logs for error messages

### "Site URL is invalid"
- Verify ATLASSIAN_CONFLUENCE_SITE_URL is correct
- Remove trailing slash (/) from URL
- Confirm protocol (https://) is included

### "Permission denied"
- Check Atlassian account permissions
- Verify Confluence/Jira access permissions
- Confirm OAuth approval is complete

### Cannot access specific Space/Project
- Verify you are a member of that Space/Project
- Check if you have read/write permissions
- Request permissions from administrator

---

## 💡 Tips

### Finding Page ID
1. Open Confluence page
2. Click **"..."** menu in top right
3. Click **"Page Information"**
4. Check Page ID in URL
   - Example: `.../pages/pageInfo.action?pageId=782407271`

### Finding Space Key
1. Open Confluence Space home
2. Check URL: `https://.../wiki/spaces/ABC/...`
   - Space Key: `ABC`

### Finding Project Key
1. Open Jira project
2. Check issue number: `ABC-123`
   - Project Key: `ABC`

### Effective Usage
- Specify page/issue titles clearly
- Use Space/Project Keys for faster search
- Use templates for consistency

### Rovo MCP Features
- **Unified Search**: Search Confluence and Jira together
- **Auto OAuth**: No separate token generation needed
- **Real-time Sync**: Latest data auto-reflected

---

## 🔐 Security & Permissions

### OAuth Scopes
Permissions requested by Atlassian Rovo MCP:
- **Confluence**:
  - `read:confluence-content.all`
  - `write:confluence-content`
  - `read:confluence-space.summary`
- **Jira**:
  - `read:jira-work`
  - `write:jira-work`
  - `read:jira-user`

### Permission Management
- Access only necessary Spaces/Projects
- Manage sensitive information separately
- Review OAuth tokens regularly

### Self-hosted
For internal Atlassian Server:
- Verify Server/Data Center version compatibility
- Check network access permissions
- Coordinate with IT administrator
