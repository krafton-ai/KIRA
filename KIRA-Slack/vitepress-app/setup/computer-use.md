# Computer Use

KIRA can automatically control web browsers using Playwright.

## 📋 Overview

When Computer Use is enabled:
- Automatic website login
- Auto-fill web forms
- Data scraping
- Web UI automated testing
- Complex web task automation

---

## ⚙️ Setup

### 1. Launch KIRA App
Open the Environment Variables tab.

### 2. Find Computer Use Section
Scroll to **Computer Use** section

### 3. Enable Chrome
- Turn the **Chrome** toggle switch **ON**

::: tip Using Chrome Profile
When Chrome toggle is on, Playwright uses Chrome profile.
You can reuse already logged-in sessions without logging in each time.
:::

### 4. Always Open Profile Setup (Optional)
- Turn **"Always open profile setup"** toggle **ON** to:
  - Open browser every time server starts
  - Log in to new sites or change settings
  - For most cases, **OFF** is recommended

### 5. Save Settings
- Click **"Save Settings"** button

### 6. Server Start and Initial Setup

When you click **"Start"** button:

1. **Chrome browser opens automatically**
2. **Manually log in** to required websites (e.g., company SSO, Gmail, etc.)
3. Login info is saved to Chrome profile
4. **Close the browser**
5. Press **Enter key** in terminal/console
6. Python server starts normally

::: warning Initial Setup Required
When browser opens on first server start, log in to needed sites, close browser, then press Enter for server to start.
Once logged in, login state persists automatically.
:::

---

## 🎯 Usage Examples

### Automatic Website Login
```
User: Log in to example.com
      ID: user@email.com
      Password: ****
KIRA: [Playwright running]
      ✅ example.com login complete
```

### Fill Web Forms
```
User: Fill out this survey
      Name: John Doe
      Email: john@email.com
      Comment: Very satisfied
KIRA: [Playwright running]
      ✅ Survey completed
```

### Data Collection
```
User: Collect product price info from example.com
KIRA: [Playwright running]
      📊 Collection complete
      1. Product A: $10
      2. Product B: $20
      ...
```

### Web UI Testing
```
User: Test our site's login
KIRA: [Playwright running]
      ✅ Login page access successful
      ✅ ID/password input successful
      ✅ Login button click successful
      ✅ Dashboard navigation confirmed
```

---

## 💡 Chrome Profile Benefits

### Advantages of Using Profile
1. **Session persistence**: Log in once, stays logged in
2. **Cookie reuse**: Uses previous session info
3. **Extensions**: Can use installed Chrome extensions
4. **Settings preserved**: Uses browser settings as-is

### Login Session Persistence
Login info from initial server start is saved to Chrome profile:
- Auto-maintains login state on next server start
- No re-login needed when using Computer Use
- Cookies and session info auto-preserved

### Always Open Profile Setup
When this option is on:
- **Browser opens every time server starts**
- Can add logins to new sites
- Useful when wanting to change browser settings
- Can re-login to sites with expired sessions

---

## 🔧 Troubleshooting

### Chrome Won't Open
- Verify Chrome browser is installed
  - **macOS**: Check Chrome in Applications folder
  - **Windows**: Check Chrome in Program Files or via Start menu search
- Check if other Chrome processes are running

### "Timeout" Error
- Check network connection
- Website may take long to load
- Verify page actually exists

### Login Not Persisting
- Verify CHROME_ENABLED is on
- Check if Chrome profile was created properly
- Verify website doesn't block cookies

### "Element not found" Error
- Website structure may have changed
- Provide more specific description to KIRA
- Example: "The login button is in the top right of the page"

---

## ⚠️ Cautions

### Security
- Don't write sensitive info (passwords, etc.) directly in Slack
- Send via DM or store in environment variables
- Login info is stored in Chrome profile

### Performance
- Browser automation takes time
- Complex tasks may take 1-2 minutes
- Please be patient

### Limitations
- Sites with CAPTCHA are difficult to automate
- Some websites may block automation
- May be limited by anti-bot systems

### Legal Considerations
- Check website terms of service
- Don't use on sites that prohibit automation
- Recommended for personal use only

---

## 💡 Tips

### Effective Requests
✅ **Be specific**:
```
"The login button on example.com is in the top right.
The ID input field is labeled 'email'."
```

❌ **Too vague**:
```
"Log in"
```

### Break Complex Tasks into Steps
```
1. "Go to example.com"
2. "Go to login page"
3. "Enter ID user@email.com"
4. "Enter password"
5. "Click login button"
```

### Reset Profile
If Chrome profile has issues:
1. Stop KIRA server
2. Delete Chrome profile folder
3. Restart server
4. Log in again

---

## 🎓 Advanced Usage

### Periodic Task Automation
```
Every day at 9am:
- Access website A
- Collect data
- Send to Slack
```

### Complex Workflows
```
1. Download data from site A
2. Upload to site B
3. Confirm result and send Slack notification
```

### Multi-tab Operations
```
Open multiple sites and perform tasks simultaneously
```

Automate repetitive web tasks with Computer Use! 🚀
