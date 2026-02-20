# Setup Guide

If you've completed the basic setup ([Slack connection](/getting-started#%EF%B8%8F-step-4-configure-kira-app)), you can now enable additional features.

::: tip Complete Basic Setup First!
If you haven't done the basic setup yet, please refer to the [Getting Started guide](/getting-started) first.
:::

## 📋 Configuration Structure

### 1. MCP Settings
MCP (Model Context Protocol) servers you can enable as needed.

- [Perplexity Web Search](/setup/perplexity) - Real-time web information search
- [DeepL (Document Translation)](/setup/deepl) - Document translation
- [GitHub](/setup/github) - GitHub repository integration
- [GitLab](/setup/gitlab) - GitLab repository integration
- [Microsoft 365 (Outlook/OneDrive/SharePoint)](/setup/ms365) - Email and file auto-management
- [Confluence & Jira](/setup/atlassian) - Document and issue tracking
- [Tableau](/setup/tableau) - BI dashboard integration
- [X (Twitter)](/setup/x) - Social media integration
- [Clova Speech (Meeting Notes)](/setup/voice) - Voice recording and meeting notes

### 2. Advanced Settings
Settings for advanced users.

- [Computer Use](/setup/computer-use) - Web browser automation
- [Web Interface (Voice Input)](/setup/web-interface) - Web-based interface and voice input

---

## ⚙️ Configuration Management

### Config File Location
All settings are saved at:
```
~/.kira/config.env
```

### Changing Settings
1. Launch KIRA app
2. Click **"Environment Variables"** tab at the top
3. Modify desired items
4. Click **"Save Settings"** button
5. Click **"Restart Server"** button (to apply changes)

### Backup Settings
Backing up the config file is useful for reinstallation:

```bash
cp ~/.kira/config.env ~/Desktop/kira-config-backup.env
```

---

## 🎯 Recommended Configurations

Recommended settings by work type.

### 💼 Business Users
```
✓ Slack Integration
✓ Perplexity Web Search
✓ DeepL Translation
✓ Outlook Email
```

### 📊 Project Managers
```
✓ Slack Integration
✓ Confluence & Jira
✓ Outlook Email
✓ Proactive Suggestions
```

### 💻 Developers
```
✓ Slack Integration
✓ GitHub / GitLab
✓ Confluence & Jira
✓ Perplexity Web Search
```

### 📱 Social Media Managers
```
✓ Slack Integration
✓ X (Twitter)
✓ Perplexity Web Search
✓ DeepL Translation
```

---

## 🔒 Security & Privacy

### Data Storage Locations

All KIRA data is stored on your local computer.

**App Settings:**
```
~/.kira/
├── config.env          # Environment variable settings file
└── server.log          # Server log file
```

**Data and Memory:**

Memory and databases are stored in the location set by the `FILESYSTEM_BASE_DIR` environment variable.

- **Default**: `~/Documents/KIRA/`
- **Custom**: Can be changed in environment variable settings

```
{FILESYSTEM_BASE_DIR}/
├── db/                # Database files
│   ├── waiting_answer.db  # Waiting answer DB
│   ├── confirm.db         # Pending approval DB
│   ├── email_tasks.db     # Email tasks DB
│   └── jira_tasks.db      # Jira tasks DB
└── memories/          # Memory (conversation history)
    ├── channels/      # Conversations by channel
    ├── projects/      # Project information
    ├── users/         # User information
    ├── decisions/     # Decisions
    └── index.md       # Auto-generated index
```

::: tip Changing Data Storage Location
Go to KIRA app > Environment Variables > Enter desired path in `FILESYSTEM_BASE_DIR`.
Example: `/Users/yourname/Dropbox/KIRA` (sync with Dropbox)
:::

### Authentication Protection
- All API keys and tokens are stored unencrypted in `config.env`
- File permissions are set so only the current user can read
- Never share the config file

### External Communications
KIRA only communicates with:
- Anthropic API (Claude)
- Enabled MCP servers (Slack, Outlook, Perplexity, etc.)

---

## ❓ Next Steps

1. Enable needed [MCP Settings](#1-mcp-settings)
2. Enable [Advanced Settings](#2-advanced-settings) if needed
3. Learn usage with the [Chat Guide](/features/chat)

If problems occur, refer to the [Troubleshooting](/troubleshooting) page.
