# DeepL (Document Translation)

Integrating DeepL API allows KIRA to translate documents with high quality.

## 📋 Prerequisites

- DeepL API account
- API key (Free or Pro)

---

## 🔑 Step 1: Get API Key

### 1. Create DeepL Account
1. Go to [DeepL API page](https://www.deepl.com/pro-api)
2. Click **"Sign up for free"**
3. Sign up with email

### 2. Choose API Plan
- **DeepL API Free**: 500,000 characters free per month
- **DeepL API Pro**: Paid (usage-based)

### 3. Copy API Key
1. Access dashboard after registration
2. Click **"API Keys"** tab
3. Copy **"Authentication Key"**

::: warning API Key Types
- **Free API**: Ends with `....:fx`
- **Pro API**: Regular string

KIRA supports both types.
:::

---

## ⚙️ Step 2: Configure KIRA

### 1. Launch KIRA App
Open the Environment Variables tab.

### 2. Find DeepL Section
**MCP Settings** > **DeepL**

### 3. Enable Setting
- Turn the toggle switch **ON**

### 4. Enter API Key
- **DEEPL_API_KEY**: The API key you copied

### 5. Save Settings
- Click **"Save Settings"** button
- Restart server

---

## ✅ Step 3: Test

Ask KIRA on Slack:

```
Translate "Hello, how are you?" to Korean
```

```
Translate "안녕하세요" to English
```

KIRA will translate using DeepL.

---

## 🎯 Usage Examples

### English → Korean
```
User: Translate "Machine learning is awesome" to Korean
KIRA: [DeepL translation] "머신러닝은 훌륭합니다"
```

### Korean → English
```
User: Translate this document to English: 안녕하세요...
KIRA: [DeepL translation] "Hello..."
```

### Multi-language Support
```
User: Translate "Bonjour" to Japanese
KIRA: [DeepL translation] "こんにちは"
```

Languages supported by DeepL:
- English, Korean, Japanese, Chinese
- German, French, Spanish, Italian
- Portuguese, Dutch, Polish, Russian
- And 30+ more languages

---

## 🔧 Troubleshooting

### "Invalid API key"
- Verify API key is entered correctly
- Check if Free API key ends with `:fx`
- Check API key status on DeepL dashboard

### "Quota exceeded"
- Monthly free limit (500,000 characters) exceeded
- Check usage on DeepL dashboard
- Consider upgrading to Pro plan

### Translation not working
- Verify DEEPL_ENABLED is set to True
- Confirm server was restarted
- Check logs for error messages

---

## 💡 Tips

### Effective Translation Requests
- ✅ "Translate this sentence to English: ..."
- ✅ "In Korean: Hello world"
- ✅ "Translate the following to Japanese: ..."

### Cost Saving (Free API)
- Check 500,000 character monthly limit
- Split long documents for translation
- Only request translation for needed parts

### Translation Quality
- DeepL provides more natural translations than Google Translate
- Particularly strong with European languages and Korean
- Technical terms may need context verification
