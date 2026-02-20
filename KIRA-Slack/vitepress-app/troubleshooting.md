# Troubleshooting

Problems and solutions you may encounter while using KIRA.

---

## 🛠️ Installation Issues

### "uv not found"

uv is not installed or not in PATH.

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart terminal and verify
uv --version
```

### "claude not found" / "Claude CLI not found"

Claude Code CLI is not installed.

**Solution:**
```bash
# Check if Node.js is installed
node --version

# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Verify
claude --version
```

### "npm not found"

Node.js is not installed.

**Solution:**
1. Download LTS version from [Node.js official site](https://nodejs.org/)
2. Restart terminal after installation
3. Verify with `node --version`

---

## 🚀 Server Startup Issues

### "Server won't start"

**Check:**
1. Check error messages in KIRA app log window
2. Verify uv and Claude CLI are installed
3. Try restarting the app

**Check for port conflicts:**
```bash
# Check processes using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### "Python related error"

**Solution:**
```bash
# Check Python version (3.10+ required)
python3 --version

# Reinstall dependencies with uv
cd /Applications/KIRA.app/Contents/Resources/app
uv sync
```

---

## 🔌 MCP Server Connection Issues

### "MCP servers show 'failed' status"

MCP servers using npx are failing to connect.

**Symptom:**
- Some MCP servers show `failed` while others show `connected`
- Local servers (slack, scheduler, files, deepl) work, but npx-based servers fail

**Cause:**
If you installed Claude Code with `sudo npm install -g`, the npm cache folder ownership changes to root, causing permission issues.

**Verify the issue:**
```bash
npx -y @mcpcentral/mcp-time
# If you see "EACCES: permission denied" error, this is the issue
```

**Solution:**
```bash
sudo chown -R $(whoami) ~/.npm
```

Then restart the KIRA app.

::: warning Prevent this issue
When installing global npm packages, avoid using `sudo`. If you get permission errors during `npm install -g`, fix permissions first:
```bash
sudo chown -R $(whoami) /usr/local/lib/node_modules
sudo chown -R $(whoami) /usr/local/bin
```
Then run `npm install -g` without sudo.
:::

::: tip Recommended: Use nvm
To avoid permission issues entirely, install Node.js using [nvm](https://github.com/nvm-sh/nvm):
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
npm install -g @anthropic-ai/claude-code  # No sudo needed
```
:::

---

## 💬 Slack Connection Issues

### "Slack connection failed"

**Check:**
1. Verify **Bot Token** (`xoxb-...`) is correct
2. Verify **App Token** (`xapp-...`) is correct
3. Confirm **Socket Mode** is enabled in Slack App
4. Confirm app is installed to workspace

**Reissue tokens:**
1. Go to [Slack API](https://api.slack.com/apps)
2. Select app > OAuth & Permissions > Reinstall to Workspace
3. Update KIRA settings with new tokens

### "Bot doesn't respond"

**Check:**
1. Is the bot invited to the channel? `/invite @botname`
2. Is your name in **AUTHORIZED_USERS**?
3. Does the name match your Slack profile **Real Name** exactly?
4. Check log for error messages

### "No response when mentioning in channel"

**Check:**
1. Confirm bot is invited to the channel
2. Verify `app_mention` event is registered in Slack App
3. Verify `message.channels` permission exists

### "Bot stopped receiving messages suddenly"

Event Subscriptions may have been disabled automatically.

**Cause:**
If KIRA is not terminated properly (force quit, crash, etc.), Slack may disable Event Subscriptions for the app.

**Solution:**
1. Go to [Slack API Apps](https://app.slack.com/apps) or [api.slack.com/apps](https://api.slack.com/apps)
2. Select your KIRA app
3. Go to **Event Subscriptions**
4. Check if the toggle is **OFF** - turn it back **ON**
5. Click **Save Changes**
6. Restart KIRA

::: warning Prevent this issue
Always stop KIRA properly using the Stop button before closing the app. Avoid force-quitting the application.
:::

---

## 🔄 Update Issues

### "Auto-update doesn't work"

**Manual update:**
1. Download latest version from [KIRA download page](https://kira.krafton-ai.com/)
2. Delete existing app and reinstall
3. Settings are preserved in `~/.kira/config.env`

---

## ⚡ Claude API Issues

### "Rate Limit Error (429)"

You've reached the Claude API request limit.

**Symptoms:**
- Bot doesn't respond
- Log shows `429 Too Many Requests` or `rate_limit_error` message

**Causes:**
- Claude API has per-minute/daily request limits
- Occurs when processing many messages simultaneously
- Limits vary by tier (Tier 1: 50 requests/min, Tier 4: 4,000 requests/min)

**Solutions:**
1. **Immediate**: Wait briefly and try again (usually resolves within 1 minute)
2. **Monitor usage**: Check current usage at [Anthropic Console](https://console.anthropic.com/settings/limits)
3. **Long-term solutions**:
   - Request tier upgrade from Anthropic
   - Disable unnecessary active receivers (Checkers)
   - Reduce message processing frequency

::: warning Note
Rate limits apply per API key. If multiple users share the same key, limits are reached faster.
:::

### "API Key authentication failed"

**Check:**
1. Verify `ANTHROPIC_API_KEY` environment variable is set
2. Confirm API key is valid at [Anthropic Console](https://console.anthropic.com/)
3. Ensure API key has sufficient credits

---

## 🔧 How to Check Logs

### KIRA App Logs
- View real-time in the app's log window
- File location: `~/.kira/server.log`

### Open Log Files
```bash
# Real-time log monitoring
tail -f ~/.kira/server.log

# View last 100 lines
tail -100 ~/.kira/server.log
```

### Filter Error Logs Only
```bash
grep -i "error\|exception" ~/.kira/server.log
```

---

## 📞 Additional Support

If the problem persists:

1. **Check logs**: Review error messages in `~/.kira/server.log`
2. **Verify settings**: Confirm all required settings are entered in KIRA app
3. **Restart**: Close and restart the app
4. **Reinstall**: Settings file (`~/.kira/config.env`) is preserved, so just reinstall the app

::: tip Backup Settings
Back up your settings before troubleshooting:
```bash
cp ~/.kira/config.env ~/Desktop/kira-config-backup.env
```
:::
