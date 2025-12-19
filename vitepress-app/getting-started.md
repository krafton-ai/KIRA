---
title: Getting Started with KIRA | Installation Guide
description: Step-by-step guide to install and set up KIRA, your AI virtual coworker. Learn how to connect Slack, configure tokens, and start chatting with your AI assistant in under 15 minutes.
head:
  - - meta
    - name: keywords
      content: KIRA installation, Slack bot setup, AI assistant guide, KIRA tutorial, AI virtual coworker setup
  - - meta
    - property: og:title
      content: Getting Started with KIRA | Installation Guide
  - - meta
    - property: og:description
      content: Install KIRA in 15 minutes. Complete guide for Slack app setup, token configuration, and starting your first conversation.
  - - meta
    - property: og:url
      content: https://kira.krafton-ai.com/getting-started
---

# Getting Started

Getting started with KIRA is really simple. Follow this guide and you'll be chatting with your own AI virtual coworker in under 15 minutes.

## 🎯 Choose Your Mode

KIRA can be used in two different modes. **Choose your preferred mode first.**

<img src="/images/screenshots/mode-comparison.png" alt="Bot Mode vs Virtual Coworker Mode" style="max-width: 550px; width: 100%;" />

::: info Mode Comparison
| Feature | Bot Mode | Virtual Coworker Mode |
|---------|----------|----------------------|
| **Installation** | Your computer | Dedicated computer/VM/server |
| **Slack Account** | Your account or bot app | Dedicated account for AI |
| **Token** | Bot Token (`xoxb-...`) | User Token (`xoxp-...`) |
| **Display** | Shows as a bot | Shows as a real user |
| **Uptime** | When your computer is on | 24/7 (always on) |
| **Operator** | You | Independent operation |
| **Setup** | Easy | Slightly complex |
:::

> 💡 **KRAFTON Use Case**: KRAFTON provides a dedicated company account and computer to run KIRA as a virtual coworker, just like onboarding a new hire.

### 🤖 Bot Mode

**Use KIRA as a personal AI assistant on your computer.**

- Install KIRA on **your computer**
- Use **your Slack account** or bot app
- You manage and operate it directly
- Stops when your computer is off

**Best for:**
- Personal work assistance
- Using AI assistant alone
- Quick and simple setup

### 👤 Virtual Coworker Mode

**Run KIRA as a team-shared AI coworker on a dedicated computer.**

- Install KIRA on a **dedicated computer** (or VM/server)
- Create a **dedicated Slack account** for the AI (e.g., "KIRA Kim")
- Runs 24/7 independently
- Participates in channels like a real team member

**Best for:**
- Team-wide shared AI coworker
- 24/7 always-on operation
- Operating like a real team member

::: warning Choose Your Mode Before Proceeding
This guide has different setup steps depending on your chosen mode. Follow the **Bot Mode** or **Virtual Coworker Mode** instructions at each step.
:::

---

## 📋 Prerequisites

Before you begin, you'll need:

### 1. Slack Workspace
- A personal workspace or one where you have admin permissions
- Free plan works fine

### 2. Node.js
- Node.js 18 or higher installed
- Required for Claude Code CLI
- [Download Node.js](https://nodejs.org/)

### 3. Computer Requirements
- **macOS**: 10.15 (Catalina) or later
- Free disk space: 500MB or more

### 4. Claude Pro Plan
- KIRA uses Claude Code internally, which requires a **Claude Pro plan or higher**
- [Learn more about Claude plans](https://www.anthropic.com/pricing)

---

## 🛠️ Step 1: Install Required Tools

Install the necessary tools before running the KIRA app.

### 1. Install Claude Code CLI

Run the following command in your terminal:

```bash
npm install -g @anthropic-ai/claude-code
```

::: danger Don't use sudo!
**Never use `sudo npm install -g`**. Using sudo can cause npm cache permission issues that will prevent MCP servers from connecting later.

If you get permission errors, fix permissions first:
```bash
sudo chown -R $(whoami) /usr/local/lib/node_modules
sudo chown -R $(whoami) /usr/local/bin
```
Then run `npm install -g` without sudo.

If you already installed with sudo, see [Troubleshooting - MCP Server Connection Issues](/troubleshooting#mcp-servers-show-failed-status).
:::

Verify installation:
```bash
claude --version
```

### 2. Install mcp-cache

Install mcp-cache for MCP server optimization:

```bash
npm install -g @hapus/mcp-cache
```

::: tip What is mcp-cache?
mcp-cache reduces startup time and cache size for MCP servers. It's required for GitLab, MS365, Atlassian, Tableau, and Computer Use (Playwright) features.
:::

### 3. Log in to Claude

**Important**: After installing Claude Code CLI, you must log in first:

```bash
claude
```

When you run the `claude` command:
1. A browser window will open automatically
2. Log in with your Anthropic account (or create one)
3. After authentication, you'll see a confirmation message in terminal
4. You can exit the terminal - your login session persists

::: warning First-Time Setup Required
KIRA uses the Claude Agent SDK internally, so you must complete this login step before starting KIRA. If you skip this step, KIRA won't be able to use Claude AI.
:::

::: tip What is Claude Code CLI?
It's the CLI tool used internally by the Claude Agent SDK, which powers KIRA's AI engine.
:::

### 4. uv (Python Package Manager) - Auto-installed

::: tip Automatic Installation
uv is **automatically installed** when you first start KIRA. If uv is not detected, a dialog will appear asking if you want to install it automatically.
:::

If automatic installation fails, you can install it manually:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify installation:
```bash
uv --version
```

::: info What is uv?
uv is a fast Python package manager. KIRA uses it to automatically install and manage required Python libraries.
:::

---

## 📥 Step 2: Download and Install KIRA

1. Download [KIRA for macOS (Apple Silicon)](https://kira.krafton-ai.com/download/KIRA-0.1.7-arm64.dmg)
2. Open the DMG file and drag KIRA.app to the Applications folder
3. Launch KIRA from the Applications folder

---

## 🔧 Step 3: Create a Slack App

KIRA needs a Slack App to communicate with Slack.

### 1. Create a Slack App
1. Go to [Slack API page](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Enter App name (e.g., "KIRA Bot")
5. Select your workspace

### 2. Enable Socket Mode
1. Click **"Socket Mode"** in the left menu
2. Turn on **"Enable Socket Mode"** toggle
3. Enter App-Level Token name (e.g., "kira-socket")
4. Select **`connections:write`** scope
5. Click **Generate**
6. Copy the generated token (save for later) → `xapp-...`

### 3. Set Up Event Subscriptions
1. Click **"Event Subscriptions"**
2. Turn on **"Enable Events"** toggle
3. Add events based on your chosen mode:

::: code-group
```txt [🤖 Bot Mode]
In "Subscribe to bot events" section, add:
- app_mention (App mention messages)
- file_shared (File share notifications)
- link_shared (Link share notifications)
- message.channels (Public channel messages)
- message.groups (Private channel messages)
- message.im (DM messages)
- message.mpim (Group DM messages)
```

```txt [👤 Virtual Coworker Mode]
In "Subscribe to events on behalf of users" section, add:
- file_shared (File share notifications)
- link_shared (Link share notifications)
- message.channels (Public channel messages)
- message.groups (Private channel messages)
- message.im (DM messages)
- message.mpim (Group DM messages)

※ app_mention is not supported for User Token
```
:::

4. Click **"Save Changes"**

::: tip Event Count
- Bot Mode: 7 events
- Virtual Coworker Mode: 6 events
Type event names in the search box to add them.
:::

### 4. Configure App Home
1. Click **"App Home"** in the left menu
2. In the **"Show Tabs"** section:
   - Check **"Messages Tab"**
   - ✅ **Must check "Allow users to send Slash commands and messages from the messages tab"**
3. Click **"Save Changes"**

::: warning Important
If you don't check "Allow users to send Slash commands and messages from the messages tab", users won't be able to DM the bot!
:::

### 5. Set Token Scopes
1. Click **"OAuth & Permissions"**
2. Add permissions based on your chosen mode:

::: code-group
```txt [🤖 Bot Mode]
In "Bot Token Scopes" section, add (21 total):

[Message related]
- app_mentions:read (Read @mention messages)
- channels:history (Read public channel messages)
- groups:history (Read private channel messages)
- im:history (Read DM messages)
- mpim:history (Read group DM messages)
- chat:write (Send messages)

[Channel info]
- channels:read (View public channel info)
- groups:read (View private channel info)
- im:read (View DM info)
- mpim:read (View group DM info)

[Start DMs]
- im:write (Start DMs)
- mpim:write (Start group DMs)

[Files and more]
- files:read (Read files)
- files:write (Upload/edit files)
- links:read (View URLs in messages)
- reactions:write (Add emoji reactions)

[User info]
- users:read (View workspace user info)
- users:read.email (View user email addresses)
- users.profile:read (View user profile details)
- users:write (Set bot status)
```

```txt [👤 Virtual Coworker Mode]
In "User Token Scopes" section, add (21 total):

[Message related]
- channels:history (Read public channel messages)
- groups:history (Read private channel messages)
- im:history (Read DM messages)
- mpim:history (Read group DM messages)
- chat:write (Send messages)

[Channel info]
- channels:read (View public channel info)
- groups:read (View private channel info)
- im:read (View DM info)
- mpim:read (View group DM info)

[Start DMs]
- im:write (Start DMs)
- mpim:write (Start group DMs)

[Files and more]
- files:read (Read files)
- files:write (Upload/edit files)
- links:read (View URLs in messages)
- reactions:write (Add emoji reactions)

[User info]
- users:read (View workspace user info)
- users:read.email (View user email addresses)
- users.profile:read (View user profile details)
- users.profile:write (Update user profile)
- users:write (Set user status)

※ app_mentions:read is not supported for User Token
```
:::

::: tip How to Add Permissions
Type permission names in the search box and click **"Add"**.
- Bot Mode: 21 permissions
- Virtual Coworker Mode: 21 permissions
:::

### 6. Install to Workspace
1. Click **"Install to Workspace"** at the top of the page
2. Authorize permissions
3. Copy the token based on your chosen mode:

::: code-group
```txt [🤖 Bot Mode]
Copy "Bot User OAuth Token" → xoxb-...
```

```txt [👤 Virtual Coworker Mode]
Copy "User OAuth Token" → xoxp-...
```
:::

### 7. Get Signing Secret
1. Click **"Basic Information"**
2. Find **Signing Secret** in the **"App Credentials"** section
3. Click **"Show"** and copy

---

## ⚙️ Step 4: Configure KIRA App

### 1. Launch KIRA App
The settings screen appears on first launch.

![KIRA Settings Screen](/images/screenshots/kira-settings-main.png)

### 2. Enter Required Settings

Now enter the tokens you copied from the Slack App into KIRA.

#### Slack Connection
- **SLACK_BOT_TOKEN**: The token you copied
  - Bot Mode: `xoxb-...` (Bot User OAuth Token)
  - Virtual Coworker Mode: `xoxp-...` (User OAuth Token)
- **SLACK_APP_TOKEN**: The `xapp-...` token you copied
- **SLACK_SIGNING_SECRET**: The Signing Secret
- **SLACK_TEAM_ID**: Workspace ID (optional)

::: tip Finding Workspace ID
In Slack web, click workspace name > "Settings & administration" > Check URL
Example: `T01234ABCDE` from `https://app.slack.com/client/T01234ABCDE/...`
:::

#### Bot Information

![Bot Info Settings](/images/screenshots/kira-settings-bot-info.png)

**BOT_NAME**
- **Description**: The name of the bot you created in Slack.
- **Usage**: Used by KIRA to identify itself.
- **Example**: `KIRA Bot`, `My Assistant`
- **Where to find**: Slack App Settings > Basic Information > Display Name

**BOT_EMAIL**
- **Description**: The bot admin (your) email address.
- **Usage**: Receive important notifications or error alerts.
- **Example**: `john@company.com`
- **Optional**: Currently required, but notification feature may not be active.

**AUTHORIZED_USERS**
- **Description**: List of users authorized to use KIRA.
- **Usage**: Restricts bot usage to specified users only.
- **Format**: Separate multiple names with commas (,)
- **Example**: `John Doe, Jane Smith, Sarah Kim`
- **Note**:
  - Must match the **Real Name** set in Slack profile exactly.
  - Case sensitive.
  - Spaces must match exactly.

::: tip Finding Slack Username
Click your profile in Slack > "View profile" > Check "Full name" field
Or check the name in workspace member list
:::

::: warning Authorization Note
Users not in AUTHORIZED_USERS won't receive responses from the bot.
Register all team members' names if the whole team needs access.
:::

### 3. Save Settings
- Click **"Save Settings"** after entering all required fields
- Settings are saved securely to `~/.kira/config.env`

---

## 🚀 Step 5: Start KIRA

### 1. Start Server
- Click **"Start"** button in the KIRA app
- Look for "✓ Slack connected" message in the log window

### 2. Invite Bot to Slack
1. Open your Slack workspace
2. Type `/invite @KIRA Bot` in a channel or DM
3. Or go to channel details > "Integrations" > "Add apps"

### 3. Start Your First Conversation
Send a simple greeting via DM:

```
Hello KIRA!
```

If KIRA responds, you're all set! 🎉

---

## 🧠 Build Memory (Recommended)

To use KIRA more effectively, it's recommended to build memory initially.

Pre-load team member info, organization structure, project info, Confluence documents, etc.:
- Auto-recognize email addresses without tagging team members
- Auto-reference project context
- Use information instantly without searching documents

::: tip Memory Initialization Guide
For detailed memory building instructions, see the [Memory System](/features/memory#memory-initialization-guide) page.
:::

---

## ✅ Test Checklist

Verify the following:

- [ ] KIRA app runs normally
- [ ] Log shows "Slack connected" without errors
- [ ] Can chat with KIRA via Slack DM
- [ ] KIRA responds when mentioned with `@KIRA` in channels
- [ ] Can have conversations in threads

---

## 🎯 Next Steps

After completing basic setup, try adding these features:

- [Perplexity Web Search](/setup/perplexity) - Real-time information search
- [MS365 Email Monitoring](/setup/ms365) - Auto task extraction and execution
- [Confluence Document Tracking](/setup/atlassian) - Document update notifications
- [Voice Input](/setup/voice) - Chat via voice

---

## 🆘 Having Problems?

Check the [Troubleshooting](/troubleshooting) page for common issues and solutions.

**Common Issues:**

### "Slack connection failed"
- Verify Bot Token and App Token are correct
- Check that Socket Mode is enabled
- Confirm the app is installed to the workspace

### "Bot doesn't respond"
- Check if bot is invited to the channel (`/invite @botname`)
- For DMs, bot should respond without mentions
- Check log for error messages

### "Server won't start"
- Check if port 8000 is in use
- Check KIRA app log window for detailed errors
- Try restarting the app

---

<div style="text-align: center; margin-top: 60px; padding: 30px; border-radius: 12px; border: 1px solid var(--vp-c-divider);">
  <h3>🎉 Congratulations!</h3>
  <p>You're now ready to work with your own AI virtual coworker, KIRA.</p>
  <p>Next, read the <a href="/features/chat">Chat Guide</a>.</p>
</div>
