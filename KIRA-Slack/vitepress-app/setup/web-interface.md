# Web Interface (Voice Input)

![Web Interface](/images/screenshots/web-interface-main.png)

Enabling the web interface allows you to chat with KIRA in a browser and input via voice.

::: tip Required Feature
Web interface is **required** for the following features:
- Voice input (using microphone)
- Clova Speech (meeting notes)
- X (Twitter) OAuth authentication
:::

## 📋 Prerequisites

- Microsoft 365 account or Slack account (for login)
- Browser (Chrome, Safari, Edge, etc.)

---

## ⚙️ Step 1: Configure KIRA

### 1. Launch KIRA App
Open the Environment Variables tab.

### 2. Find Web Server Section
Scroll to **Web Server / Voice Input** section

### 3. Enable Web Interface
- Turn the **Web Interface** toggle switch **ON**

::: info Web Server Info
- **Port**: 8000
- **Protocol**: HTTPS
- **URL**: `https://localhost:8000`
:::

### 4. Select Authentication Method
Choose from dropdown:
- **Microsoft 365**: Log in with company account
- **Slack**: Log in with Slack workspace account

::: tip Which authentication to choose?
- Using Microsoft 365 → **Microsoft 365**
- Using Slack only → **Slack**
- Using both → Choose your preference
:::

### 5. Slack Authentication (Optional)
If you selected Slack as authentication method:

1. Go to Slack App settings page
2. Click **"OAuth & Permissions"**
3. In **"Redirect URLs"** section, click **"Add New Redirect URL"**
4. Add this URL:
   ```
   http://localhost:8000/auth/callback
   ```
5. Click **"Save URLs"**
6. In **"Basic Information"** > **"App Credentials"**:
   - Copy **Client ID** → Enter in KIRA as `WEB_SLACK_CLIENT_ID`
   - Copy **Client Secret** → Enter in KIRA as `WEB_SLACK_CLIENT_SECRET`

::: warning Slack OAuth Setup
To use Slack as authentication method, you must add Redirect URL to Slack App.
If using Microsoft 365, skip this step.
:::

### 6. External Access URL (Optional)
**Base URL (for external access)**:
- Local use only: Leave empty
- External (internet) access: Enter URL like ngrok
  - Example: `https://abc123.ngrok-free.app`

### 7. Save Settings
- Click **"Save Settings"** button
- Restart server

---

## ✅ Step 2: Web Access and Login

### 1. Open Browser
1. Go to `https://localhost:8000` in browser
2. Security warning may appear (using self-signed certificate)
3. Click **"Advanced"** > **"Proceed"**

::: tip HTTPS Security Warning
KIRA uses a local HTTPS server, so browser shows security warning.
This is normal and safe to proceed.
:::

### 2. Login
Log in with your selected authentication method:

**Microsoft 365:**
1. Click **"Sign in with Microsoft"** button
2. Enter Microsoft account
3. Approve permissions
4. Login complete

**Slack:**
1. Click **"Sign in with Slack"** button
2. Select Slack workspace
3. Approve permissions
4. Login complete

### 3. Permission Check
- User must be registered in `BOT_AUTHORIZED_USERS`
- Access denied if not registered

---

## 🎤 Step 3: Using Voice Input

### 1. Allow Microphone Permission
1. Click **microphone button** on web page
2. Browser requests microphone permission
3. Click **"Allow"**

### 2. Speak
1. Microphone button turns red (recording)
2. Ask questions or make requests to KIRA
3. Auto-converts to text when done speaking
4. KIRA responds

### 3. Stop
- Click **stop button** to end recording

---

## 🎯 Usage Examples

### Voice Conversation
```
[Click microphone button]
"Hey KIRA, what's the weather like today?"

[KIRA responds]
"Hello! Seoul is sunny today with a high of 65°F."
```

### Meeting Notes (requires Clova Speech)
```
[Click microphone button]
"In today's meeting, we discussed the new project schedule.
The dev team will complete prototype by next week..."

[KIRA automatically organizes meeting notes]
```

### Long Message Input
```
Quickly input long content via voice when typing is inconvenient
```

---

## 🔧 Troubleshooting

### "Cannot connect to web server"
- Verify WEB_INTERFACE_ENABLED is on
- Verify KIRA server is running
- Check if port 8000 is used by another program

### HTTPS Security Warning
- **This is normal!** Using local self-signed certificate
- Click "Advanced" > "Proceed"
- Chrome: Type "thisisunsafe" (not visible on screen)

### Microphone Not Working
- Check microphone permissions in browser settings
- Chrome: Settings > Privacy and security > Site settings > Microphone
- Verify browser has microphone access in system settings

### "Permission denied"
- Verify your name is registered in BOT_AUTHORIZED_USERS
- Name must match Slack/Microsoft profile exactly
- Case-sensitive and spaces must match

### Slack Login Failed
- Verify WEB_SLACK_CLIENT_ID and WEB_SLACK_CLIENT_SECRET
- Confirm Slack App Redirect URL is set to `http://localhost:8000/auth/callback`
- Verify Slack App is installed in workspace

---

## 💡 Tips

### Improve Voice Recognition Accuracy
- Use in quiet environment
- Maintain 20-30cm from microphone
- Clear pronunciation
- Minimize background noise

### Access from External
ngrok usage example:
```bash
ngrok http 8000
```

Enter generated URL in KIRA settings **Base URL**:
```
https://abc123.ngrok-free.app
```

::: warning External Access Security
Be careful with security when enabling external access.
- Use strong authentication
- Only allow trusted users
- Recommended for temporary use only
:::

### Browser Compatibility
- ✅ Chrome / Edge (Chromium) - Recommended
- ✅ Safari - Compatible
- ✅ Firefox - Compatible
- ❌ IE - Not supported

### Mobile Usage
- Accessible from mobile browsers
- Voice input also works
- However, PC recommended due to small screen

---

## 🔐 Security

### Authentication System
- Uses Microsoft 365 or Slack OAuth
- Session-based authentication
- Only authorized users can access

### HTTPS Usage
- All communication is encrypted
- Uses self-signed certificate (local)
- Recommend using proper certificates (ngrok, etc.) for external access

### Data Security
- Voice data is processed immediately after server transmission
- Recording files are not stored
- All conversation content is stored only in memory

---

## ⚠️ Important Checklist

Before using web interface:

- [ ] WEB_INTERFACE_ENABLED enabled
- [ ] Authentication method selected (Microsoft 365 or Slack)
- [ ] Redirect URL set if using Slack
- [ ] Settings saved and server restarted
- [ ] `https://localhost:8000` accessible
- [ ] Login successful
- [ ] Microphone permission allowed
- [ ] Voice input test complete

After checking all items, use the web interface! 🎉
