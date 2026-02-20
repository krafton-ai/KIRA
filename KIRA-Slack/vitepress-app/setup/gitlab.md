# GitLab Integration

Integrating GitLab API allows KIRA to manage code repositories.

## 📋 Prerequisites

- GitLab account (gitlab.com or Self-hosted)
- Personal Access Token

---

## 🔑 Step 1: Generate Access Token

### 1. Access GitLab
- [GitLab.com](https://gitlab.com) or your company's GitLab server

### 2. Create Personal Access Token
1. Click profile icon in top right
2. Select **"Edit Profile"**
3. Click **"Access Tokens"** in left menu
4. Click **"Add new token"**

### 3. Configure Token
- **Token name**: `KIRA Bot` (any name you want)
- **Expiration date**: Set expiration (optional)
- **Select scopes**: Choose these permissions
  - ✅ `api` - Full API access
  - ✅ `read_repository` - Read repositories
  - ✅ `write_repository` - Write repositories

### 4. Generate and Copy Token
1. Click **"Create personal access token"**
2. Copy generated token (shown only once!)
3. Store securely

::: warning Token Security
Personal Access Token is shown only once.
Store it safely as you cannot view it again.
:::

---

## ⚙️ Step 2: Configure KIRA

### 1. Launch KIRA App
Open the Environment Variables tab.

### 2. Find GitLab Section
**MCP Settings** > **GitLab**

### 3. Enable Setting
- Turn the toggle switch **ON**

### 4. Enter Information
- **GITLAB_API_URL**: GitLab server URL
  - GitLab.com: `https://gitlab.com`
  - Self-hosted: `https://git.company.com`
- **GITLAB_PERSONAL_ACCESS_TOKEN**: The Access Token you copied

### 5. Save Settings
- Click **"Save Settings"** button
- Restart server

---

## ✅ Step 3: Test

Ask KIRA on Slack:

```
Show me my GitLab projects
```

```
Tell me recent commits for project "myapp"
```

KIRA will fetch information via GitLab API.

---

## 🎯 Usage Examples

### Project Query
```
User: Show me GitLab project list
KIRA: [GitLab query]
      1. project-alpha
      2. project-beta
      3. my-app
```

### Issue Management
```
User: Create an issue in "my-app" project: "Bug fix needed"
KIRA: [GitLab issue created] Created issue #42.
```

### Commit Query
```
User: Show me last 5 commits in "my-app"
KIRA: [GitLab query]
      1. fix: Login bug fix
      2. feat: Add new feature
      ...
```

### MR (Merge Request) Query
```
User: Show me my MRs
KIRA: [GitLab query]
      1. MR !123: Feature improvement
      2. MR !124: Bug fix
```

---

## 🔧 Troubleshooting

### "Authentication failed"
- Verify Access Token is correct
- Check if token has expired
- Verify token is active on GitLab

### "API URL is incorrect"
- Verify GITLAB_API_URL is correct
- For self-hosted, ensure URL is exact
- Check protocol inclusion (https://)

### "Permission denied"
- Check Access Token permissions (scopes)
- Need `api`, `read_repository`, `write_repository` permissions
- Verify project access permissions

### Cannot access specific project
- Confirm you're a member of that project
- Check permissions if project is Private

---

## 💡 Tips

### Self-hosted GitLab
When using internal company GitLab server:
- Enter company GitLab address in GITLAB_API_URL
- Example: `https://git.company.com`

### Token Management
- Set clear token name (`KIRA Bot`)
- Set expiration for security
- Rotate tokens regularly

### Minimize Permissions
Grant only necessary permissions:
- Read-only: Select only `read_repository`
- Need write: Add `write_repository`
- Full API: Select `api`

### Effective Usage
- Specify project names clearly
- Enter branch names exactly
- Quick lookup via issue numbers
