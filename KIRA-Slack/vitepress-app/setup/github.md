# GitHub Integration

Integrating GitHub API allows KIRA to manage code repositories.

## 📋 Prerequisites

- GitHub account
- Personal Access Token (Classic or Fine-grained)

---

## 🔑 Step 1: Generate Personal Access Token

### 1. Access GitHub
Log in to [GitHub.com](https://github.com)

### 2. Go to Settings
1. Click profile icon in top right
2. Select **"Settings"**
3. Click **"Developer settings"** at bottom of left menu

### 3. Create Token
1. Click **"Personal access tokens"** > **"Tokens (classic)"**
2. Select **"Generate new token"** > **"Generate new token (classic)"**

::: tip Fine-grained Token
Use **Fine-grained tokens** if you need more granular permission control.
:::

### 4. Configure Token (Classic)
- **Note**: `KIRA Bot` (any name you want)
- **Expiration**: Set expiration date (90 days recommended)
- **Select scopes**: Choose these permissions
  - ✅ `repo` - Full repository access
  - ✅ `read:packages` - Read packages
  - ✅ `read:org` - Read organization info (optional)
  - ✅ `workflow` - Manage GitHub Actions (optional)

### 5. Generate and Copy Token
1. Click **"Generate token"**
2. Copy generated token (starts with `ghp_`)
3. Store securely

::: warning Token Security
Personal Access Token is shown only once.
Store it safely as you cannot view it again.
:::

---

## ⚙️ Step 2: Configure KIRA

### 1. Launch KIRA App
Open the Environment Variables tab.

### 2. Find GitHub Section
**MCP Settings** > **GitHub**

### 3. Enable Setting
- Turn the toggle switch **ON**

### 4. Enter Information
- **GITHUB_PERSONAL_ACCESS_TOKEN**: The Personal Access Token you copied
  - Classic: `ghp_xxxxxxxxxxxx`
  - Fine-grained: `github_pat_xxxxxxxxxxxx`

### 5. Save Settings
- Click **"Save Settings"** button
- Restart server

---

## ✅ Step 3: Test

Ask KIRA on Slack:

```
Show me my GitHub repositories
```

```
Tell me recent issues in "myrepo" repository
```

KIRA will fetch information via GitHub API.

---

## 🎯 Usage Examples

### Repository Query
```
User: Show me my GitHub repository list
KIRA: [GitHub query]
      1. user/project-alpha
      2. user/project-beta
      3. user/my-app
```

### Issue Management
```
User: Create an issue in "my-app" repo: "Bug fix needed"
KIRA: [GitHub issue created] Created issue #42.
      https://github.com/user/my-app/issues/42
```

### Pull Request Query
```
User: Show me my PRs
KIRA: [GitHub query]
      1. PR #123: Feature improvement
         https://github.com/user/my-app/pull/123
      2. PR #124: Bug fix
         https://github.com/user/my-app/pull/124
```

### Commit Query
```
User: Show me last 5 commits in "my-app"
KIRA: [GitHub query]
      1. fix: Login bug fix (2 hours ago)
      2. feat: Add new feature (5 hours ago)
      3. docs: Update README (1 day ago)
      ...
```

### GitHub Actions Status
```
User: Tell me recent workflow status for "my-app"
KIRA: [GitHub Actions query]
      ✅ CI/CD: Success (10 min ago)
      ✅ Tests: Success (10 min ago)
      ❌ Deploy: Failed (5 min ago)
```

---

## 🔧 Troubleshooting

### "Authentication failed"
- Verify Personal Access Token is correct
- Check if token has expired
- Verify token is active on GitHub
- Confirm token starts with `ghp_` or `github_pat_`

### "Permission denied"
- Check token permissions (scopes)
- `repo` permission required
- Need appropriate permissions for private repository access

### "Repository not found"
- Enter repository name exactly (`owner/repo` format)
- Private repositories need token access permissions
- Check organization permissions for org repositories

### "Rate limit exceeded"
- GitHub API request limit exceeded
- Authenticated requests: 5,000 per hour
- Auto-resets after 1 hour
- [Check Rate Limit](https://api.github.com/rate_limit)

---

## 💡 Tips

### Minimize Token Permissions
Grant only necessary permissions:
- **Read-only**: `repo` (public only), `read:org`
- **Issue/PR management**: Full `repo`
- **Actions management**: Add `workflow`

### Token Management
- Set clear token name (`KIRA Bot`)
- Set expiration for security (90 days recommended)
- Rotate tokens regularly
- Delete unused tokens immediately

### Using Fine-grained Tokens
More granular permission control:
- Allow access to specific repositories only
- Separate read/write permissions
- Auto-renewal of expiration possible

### Effective Usage
- Specify repository names clearly in `owner/repo` format
- Quick lookup via issue/PR numbers (#123)
- Enter branch names exactly
- Use Labels and Milestones

### Security Recommendations
- Don't hardcode tokens in code
- Don't commit tokens to Git repositories
- Regenerate token immediately upon suspicious activity
- Check GitHub Security Log periodically

---

## 🔗 Related Links

- [GitHub Personal Access Tokens Creation](https://github.com/settings/tokens)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [GitHub Copilot MCP Server](https://github.com/github/github-mcp-server)
- [Check Rate Limits](https://api.github.com/rate_limit)
