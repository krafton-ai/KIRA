# Clova Speech (Meeting Notes)

Integrating Naver Clova Speech API allows KIRA to convert speech to text for meeting notes.

::: danger Web Interface Required!
Clova Speech functionality **requires web interface to be enabled**.
This is because voice recording happens through the web browser and is sent to the KIRA server.

First complete [Web Interface Setup](/setup/web-interface), then return to this page.
:::

## 📋 Prerequisites

- Naver Cloud Platform account
- Clova Speech service application and approval
- ✅ **KIRA Web Interface enabled** (Required!)

---

## 🔑 Step 1: Apply for Clova Speech

### 1. Register for Naver Cloud Platform
1. Go to [Naver Cloud Platform](https://www.ncloud.com/)
2. Sign up and log in
3. Register payment method (required)

### 2. Apply for Clova Speech Service
1. Console > **AI·NAVER API** menu
2. Select **Clova Speech**
3. Click **"Apply for service"**
4. Agree to terms
5. Application complete (approval takes 1-2 business days)

::: tip Waiting for Approval
Clova Speech is available after approval.
You'll receive notification via email or SMS when approved.
:::

### 3. Generate Invoke URL
1. Console > **AI·NAVER API** > **Clova Speech**
2. Click **"Domain Registration"** tab
3. Click **"Domain Registration"** button
   - Domain: `localhost` (for testing) or actual domain
4. Copy **"Invoke URL"** after registration

Example:
```
https://clovaspeech-gw.ncloud.com/external/v1/13280/eda508206872...
```

### 4. Get Secret Key
1. Click **"Authentication Info"** tab on same page
2. Copy **Secret Key**

::: warning Secret Key Security
Keep your Secret Key secure and don't expose it.
Don't commit it to Git.
:::

---

## ⚙️ Step 2: Configure KIRA

### 1. Enable Web Interface First

::: danger Order is Important!
Enable web interface **before** Clova Speech setup.
:::

1. KIRA App > Environment Variables
2. Scroll to **"Web Server / Voice Input"** section
3. Turn **WEB_INTERFACE_ENABLED** toggle **ON**
4. Complete required web interface settings
5. Save settings and restart server
6. Verify web server is running at `http://localhost:8000`

See [Web Interface Setup Guide](/setup/web-interface) for details.

### 2. Find Clova Speech Section
**MCP Settings** > **Clova Speech**

### 3. Enable Setting
- Turn the toggle switch **ON**

### 4. Enter API Information
- **CLOVA_INVOKE_URL**: The Invoke URL you copied
- **CLOVA_SECRET_KEY**: Secret Key

### 5. Save Settings
- Click **"Save Settings"** button
- Restart server

---

## ✅ Step 3: Use in Web Interface

### 1. Access Web Browser
1. Go to `http://localhost:8000` in browser
2. Log in with Microsoft 365 or Slack account

### 2. Start Voice Recording
1. Click **"Microphone"** button on web page
2. Browser requests microphone permission
3. Click **"Allow"**
4. Recording starts (red dot indicator)

### 3. Speak Meeting Content
Record the meeting conversation as it happens:
```
Meeting attendees: John Doe, Jane Smith, Bob Lee
Meeting topic: Project status check

John: Let me share last week's work...
Jane: Backend API development is complete...
Bob: UI design review is needed...
```

### 4. Stop Recording
1. Click **"Stop"** button
2. KIRA automatically converts speech to text
3. Organizes into meeting notes format and sends to Slack

---

## 🎯 Usage Examples

### Auto Meeting Notes
```
[Record on web]
"In today's meeting, we discussed the new project schedule.
The dev team will complete the prototype by next week,
and the design team will prepare UI mockups."

[KIRA sends to Slack]
📝 Meeting Notes

**Date**: 2024-11-20 14:30
**Topic**: New project schedule discussion

**Discussion**:
- New project schedule discussion
- Dev team: Complete prototype by next week
- Design team: Prepare UI mockups

**Decisions**:
1. Prototype deadline: Next week
2. Prepare UI mockups
```

### Voice Memo
```
[Record on web]
"Need to prepare for client meeting tomorrow.
Check presentation materials and demo environment."

[KIRA saves memo and notifies]
✅ Voice memo saved

Tomorrow's tasks:
- Prepare for client meeting
- Prepare presentation materials
- Check demo environment
```

### Interview Transcription
```
[Record on web]
Record interview → Auto text conversion → Organized format delivered
```

---

## 🔧 Troubleshooting

### Microphone Permission Error
- Check microphone permissions in browser settings
- Chrome: Settings > Privacy and security > Site settings > Microphone
- Allow microphone permission for `localhost` or your site

### "Web Interface not enabled"
- Check WEB_INTERFACE_ENABLED in KIRA settings
- Verify web server is running (`http://localhost:8000`)
- Check logs for web server startup message

### "Invalid Invoke URL"
- Verify CLOVA_INVOKE_URL is correct
- Check URL again in Naver Cloud Console
- Make sure entire URL is copied (remove leading/trailing spaces)

### "Authentication failed"
- Verify CLOVA_SECRET_KEY is correct
- Check Secret Key again in Naver Cloud Console
- Regenerate key and enter again

### Voice Recognition is Inaccurate
- Record in quiet environment
- Maintain proper distance from microphone (20-30cm)
- Speak clearly
- Minimize background noise

### Language Recognition Settings
- Clova Speech is optimized for Korean
- English recognition is available but accuracy is higher for Korean

---

## 💡 Tips

### Effective Meeting Notes
- Mention attendees and topic at meeting start
- Use keywords like "Decision:", "Action item:" for important decisions
- Speak clearly to improve recognition accuracy

### Cost Management
Clova Speech pricing:
- Free: 100 minutes/month
- Paid: Charged per hour beyond free tier

Check usage:
- Naver Cloud Console > Usage > Details

### Improve Audio Quality
- External microphone recommended
- USB microphone or headset microphone
- Higher quality than built-in laptop microphone

### Long Meeting Recordings
- Split long meetings into multiple recordings
- Separate by topic for each session
- Recommended to split into 30-minute segments

---

## ⚠️ Important Checklist

Check before starting:

- [ ] Naver Cloud Platform registration complete
- [ ] Payment method registered
- [ ] Clova Speech service applied and approved
- [ ] Invoke URL generated
- [ ] Secret Key obtained
- [ ] **KIRA Web Interface enabled** ✅
- [ ] Web server running (`http://localhost:8000`)
- [ ] Clova Speech settings entered in KIRA
- [ ] Settings saved and server restarted
- [ ] Browser microphone permission allowed

After checking all items, use the voice recording feature! 🎤
