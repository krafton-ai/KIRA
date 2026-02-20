# Perplexity Web Search

Integrating Perplexity API allows KIRA to search real-time web information.

## 📋 Prerequisites

- Perplexity API account
- API key

---

## 🔑 Step 1: Get API Key

### 1. Create Perplexity Account
1. Go to [Perplexity AI](https://www.perplexity.ai/)
2. Create account and log in

### 2. Generate API Key
1. Go to [Perplexity API page](https://www.perplexity.ai/settings/api)
2. Click **"Generate API Key"**
3. Copy API key (save for later)

::: tip API Pricing
Perplexity API charges based on usage.
Check free tier and paid plans.
:::

---

## ⚙️ Step 2: Configure KIRA

### 1. Launch KIRA App
Open the Environment Variables tab.

### 2. Find Perplexity Section
**MCP Settings** > **Perplexity**

### 3. Enable Setting
- Turn the toggle switch **ON**

### 4. Enter API Key
- **PERPLEXITY_API_KEY**: The API key you copied

### 5. Save Settings
- Click **"Save Settings"** button
- Restart server

---

## ✅ Step 3: Test

Ask KIRA on Slack:

```
What's the weather in Seoul today?
```

```
Search for recent AI news
```

KIRA will search real-time information and respond.

---

## 🎯 Usage Examples

### Weather Info
```
User: Tell me tomorrow's weather in New York
KIRA: [Perplexity search] Tomorrow New York will be sunny with a high of 65°F...
```

### Latest News
```
User: Summarize today's top news
KIRA: [Perplexity search] 1. ... 2. ... 3. ...
```

### Real-time Info
```
User: What's the current Bitcoin price?
KIRA: [Perplexity search] Current Bitcoin price is...
```

---

## 🔧 Troubleshooting

### "API key is invalid"
- Verify API key is entered correctly
- Check if API key is activated on Perplexity website

### "Rate limit exceeded"
- API usage limit exceeded
- Check usage on Perplexity dashboard
- Consider upgrading to paid plan

### No search results
- Verify PERPLEXITY_ENABLED is set to True
- Confirm server was restarted
- Check logs for error messages

---

## 💡 Tips

### Effective Search Queries
- ✅ "Seoul weather November 2024"
- ✅ "AI news from last week"
- ❌ "weather" (too vague)

### Cost Saving
- Only request web search when needed
- Simple questions can be answered with KIRA's built-in knowledge
