# X (Twitter) Integration

Integrating X (formerly Twitter) API allows KIRA to post and manage tweets.

::: danger Web Interface Required!
X (Twitter) functionality **requires web interface to be enabled**.
This is needed for OAuth 2.0 authentication callback URL (`http://localhost:8000/bot/auth/x/callback`).

First complete [Web Interface Setup](/setup/web-interface), then return to this page.
:::

## 📋 Prerequisites

- X (Twitter) account
- X Developer Account
- X Developer Portal access
- ✅ **KIRA Web Interface enabled** (Required!)

---

## 🔑 Step 1: Create X Developer App

### 1. Access X Developer Portal
1. Go to [X Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Log in with X account
3. Apply for Developer account if needed (takes a few minutes)

### 2. Create New App
1. Click **"Projects & Apps"** menu
2. Click **"+ Create App"**
3. Enter App name (e.g., `KIRA Bot`)
4. Select App environment: **"Production"**

### 3. Get API Keys (OAuth 1.0a)
Copy the keys shown after app creation:

- **API Key (Consumer Key)** → `X_API_KEY`
- **API Secret (Consumer Secret)** → `X_API_SECRET`
- **Bearer Token** (not used)

::: warning Shown only once!
API Secret is shown only once at creation. Be sure to copy it!
If needed later, you must **"Regenerate"** to create a new one.
:::

### 4. Generate Access Token (OAuth 1.0a)
1. Go to **"Keys and tokens"** tab in App settings
2. Find **"Access Token and Secret"** section
3. Click **"Generate"**
4. Copy generated tokens:
   - **Access Token** → `X_ACCESS_TOKEN`
   - **Access Token Secret** → `X_ACCESS_TOKEN_SECRET`

### 5. OAuth 2.0 Setup (Important!)

OAuth 2.0 is required for user authentication through the web interface.

1. Click **"Settings"** tab in App settings
2. Click **"Set up"** in **"User authentication settings"** section
3. Select **"App permissions"**:
   - ✅ **Read and write**
   - Or **Read and write and Direct message** if needed
4. Select **"Type of App"**:
   - ✅ **Web App, Automated App or Bot**
5. Enter **"App info"**:
   - **Callback URI / Redirect URL**:
     ```
     http://localhost:8000/bot/auth/x/callback
     ```
   - **Website URL**: `http://localhost:8000` (temporary)
6. Click **"Save"**

### 6. OAuth 2.0 Client ID and Secret
Copy values shown after setup:

- **OAuth 2.0 Client ID** → `X_OAUTH2_CLIENT_ID`
- **OAuth 2.0 Client Secret** → `X_OAUTH2_CLIENT_SECRET`

::: tip Why Callback URL Matters
X OAuth 2.0 authentication redirects users to X login page, then
returns to `http://localhost:8000/bot/auth/x/callback` after authentication.
Therefore, **KIRA web server (port 8000) must be running**.
:::

---

## ⚙️ Step 2: Configure KIRA

### 1. Enable Web Interface First

::: danger Order is Important!
Enable web interface **before** X setup.
:::

1. KIRA app > Environment Variables
2. Scroll to **"Web Server / Voice Input"** section
3. Turn **WEB_INTERFACE_ENABLED** toggle **ON**
4. Complete web interface settings
5. Save settings and restart server
6. Confirm web server is running at `http://localhost:8000`

See [Web Interface Setup Guide](/setup/web-interface) for details.

### 2. Find X Section
**MCP Settings** > **X (Twitter)**

### 3. Enable Setting
- Turn the toggle switch **ON**

### 4. Enter API Keys

**OAuth 1.0a (Basic API access):**
- **X_API_KEY**: API Key (Consumer Key)
- **X_API_SECRET**: API Secret (Consumer Secret)
- **X_ACCESS_TOKEN**: Access Token
- **X_ACCESS_TOKEN_SECRET**: Access Token Secret

**OAuth 2.0 (User authentication):**
- **X_OAUTH2_CLIENT_ID**: OAuth 2.0 Client ID
- **X_OAUTH2_CLIENT_SECRET**: OAuth 2.0 Client Secret

### 5. Save Settings
- Click **"Save Settings"** button
- Restart server

---

## ✅ Step 3: OAuth Authentication

### Browser Authentication

When KIRA first accesses X:

1. **Browser opens automatically**
2. X login page displayed
3. Log in with your account
4. **App authorization screen**:
   - KIRA Bot requests tweet read/write permissions
5. Click **"Authorize app"**
6. Automatically redirects to `http://localhost:8000/bot/auth/x/callback`
7. Confirm authentication complete message

::: tip Auto Authentication
- OAuth tokens are stored securely
- Subsequent access is automatic
- Tokens are automatically refreshed when expired
:::

---

## 🎯 Usage Examples

### Post Tweet
```
User: Post tweet on X: "AI automation with KIRA"
KIRA: [X tweet] Tweet posted.
      https://twitter.com/yourname/status/1234567890
```

### View Recent Tweets
```
User: Show my last 5 tweets
KIRA: [X query]
      1. "AI automation with..." - 2 hours ago
      2. "Starting AI automation" - 5 hours ago
      ...
```

### Check Mentions
```
User: Check my mentions
KIRA: [X query]
      1. @friend: "Hello!"
      2. @colleague: "Please share the meeting schedule"
```

### Search Tweets
```
User: Search for "AI" keyword on X
KIRA: [X search]
      1. @tech_user: "The future of AI..."
      2. @ai_news: "Latest AI news..."
```

---

## 🔧 Troubleshooting

### "Callback URL mismatch"
- Check Callback URI in X Developer Portal
- Enter exactly `http://localhost:8000/bot/auth/x/callback`
- Use **HTTP not HTTPS**
- Verify port number (8000)

### "Web Interface not enabled"
- Check WEB_INTERFACE_ENABLED in KIRA settings
- Verify web server is running (`http://localhost:8000`)
- Check logs for web server start message

### OAuth Browser Not Opening
- Check if firewall is blocking port 8000
- Verify web interface is properly enabled
- Manually access `http://localhost:8000/bot/auth/x/start`

### "Authentication failed"
- Verify API Keys are correct
- Check OAuth 2.0 Client ID/Secret
- Verify app is active in X Developer Portal
- Check App permissions (Read and write)

### "Rate limit exceeded"
- X API usage limit exceeded
- Check usage at [X Developer Portal](https://developer.twitter.com/en/portal/dashboard)
- Free tier: 500 tweets/month limit
- Consider paid plan

---

## 💡 Tips

### Understanding API Plans

**Free Tier:**
- 1,500 tweet reads/month
- 500 tweet writes/month
- Suitable for personal projects

**Basic ($100/month):**
- 10,000 tweet writes/month
- Advanced search features

**Pro ($5,000/month):**
- Unlimited API access
- Enterprise use

### Security Best Practices
- Store API Keys and Secrets securely
- Rotate OAuth 2.0 tokens regularly
- Grant only necessary permissions (separate Read/Write)

### Effective Usage
- Use tweet scheduling
- Auto-reply functionality
- Trend monitoring
- Auto-respond to mentions

### Port 8000 Already in Use?
KIRA uses port 8000 by default.
To use a different port:
1. Change port in web interface settings
2. Also change Callback URI in X Developer Portal
3. Example: `http://localhost:3000/bot/auth/x/callback`

---

## ⚠️ Important Checklist

Check before starting:

- [ ] X Developer Account created
- [ ] X App created and API Keys generated
- [ ] OAuth 2.0 setup complete (including Callback URI)
- [ ] **KIRA Web Interface enabled** ✅
- [ ] Web server running (`http://localhost:8000`)
- [ ] All 6 keys entered in KIRA
  - API Key, API Secret
  - Access Token, Access Token Secret
  - OAuth2 Client ID, OAuth2 Client Secret
- [ ] Settings saved and server restarted
- [ ] OAuth browser authentication complete

After checking all items, use X features! 🎉
