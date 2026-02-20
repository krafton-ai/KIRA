# Tableau

Integrating Tableau MCP allows KIRA to manage Tableau dashboards and data.

## 📋 Prerequisites

- Tableau Server or Tableau Cloud account
- Personal Access Token (PAT) generation permissions

---

## 🎯 Key Features

### Data Query
- Workbook list query
- Dashboard query
- View (sheet) query
- Data Source information

### Data Management
- Workbook publishing
- Dashboard updates
- Permission management
- Metadata query

---

## ⚙️ Step 1: Generate Personal Access Token

### 1. Log in to Tableau Server
Log in to Tableau Server or Tableau Cloud in your browser.

### 2. Open Account Settings
- Click profile icon in top right
- Select **"My Account Settings"**

### 3. Go to Personal Access Tokens Section
- Click **"Personal Access Tokens"** in left menu

### 4. Create New Token
1. Click **"Create new token"** button
2. Enter **Token Name**
   - Example: `KIRA Bot Token`
3. Click **"Create"**
4. Copy **Token Secret**
   - ⚠️ Only viewable on this screen!
   - Store securely

::: warning Important
Token Secret is shown only once at creation. Must reissue if lost.
:::

---

## ⚙️ Step 2: Configure KIRA

### 1. Launch KIRA App
Open the Environment Variables tab.

### 2. Find Tableau Section
**MCP Settings** > **Tableau**

### 3. Enable Setting
- Turn the toggle switch **ON**

### 4. Enter Server Information

**TABLEAU_SERVER**
- Enter Tableau Server URL
- **Tableau Server**: `https://tableau.company.com`
- **Tableau Cloud**: `https://10ax.online.tableau.com`

::: tip URL Format
- Include protocol (`https://`)
- Remove trailing slash (`/`)
:::

**TABLEAU_SITE_NAME**
- Enter Site name
- **Default Site**: Leave empty
- **Specific Site**: Enter Site URL Name (e.g., `marketing`)
  - If Site URL is `https://tableau.com/#/site/marketing` → `marketing`

**TABLEAU_PAT_NAME**
- Enter Token Name created in Step 1
- Example: `KIRA Bot Token`

**TABLEAU_PAT_VALUE**
- Enter Token Secret copied in Step 1
- Example: `XYZ123...`

### 5. Save Settings
- Click **"Save Settings"** button
- Restart server

---

## 🎯 Usage Examples

### List Workbooks
```
User: Show me Tableau workbooks
KIRA: [Tableau query]
      1. Sales Dashboard
      2. Marketing Analytics
      3. HR Metrics
```

### Query Dashboard
```
User: Tell me about "Sales Dashboard"
KIRA: [Tableau query]
      Workbook: Sales Dashboard
      Owner: John Doe
      Created: 2024-01-15
      Views:
      - Sales Overview
      - Regional Performance
      - Monthly Trends
```

### Data Refresh
```
User: Refresh "Marketing Analytics" workbook
KIRA: [Tableau update] Workbook refreshed.
      Last updated: 2025-01-21 14:30:00
```

---

## 🔧 Troubleshooting

### "Invalid credentials"
- Verify **PAT Name** and **PAT Value** are correct
- Check if token was deleted on Tableau Server
- Check token expiration (reissue if needed)

### "Site not found"
- Verify **TABLEAU_SITE_NAME** is correct
- Leave empty for Default Site
- Check Site URL Name (not Display Name)

### "Permission denied"
- Check Tableau account permissions
- Verify Workbook/Dashboard access rights
- Check if operation requires Site Admin permissions

### "Server URL invalid"
- Verify TABLEAU_SERVER URL is correct
- Check protocol (`https://`) is included
- Check network/firewall settings

---

## 💡 Tips

### Finding Site Name
1. Log in to Tableau Server/Cloud
2. Check URL:
   - `https://tableau.com/#/site/marketing/home`
   - Site Name: `marketing`
3. Default Site has no `/site/` in URL

### Effective Usage
- Specify Workbook/Dashboard names accurately
- Use Project structure for organized management
- Set up regular data refresh schedules

### Personal Access Token Management
- **Expiration**: Can be set at token creation
- **Security**: Treat tokens like passwords
- **Revocation**: Can be immediately revoked on Tableau Server
- **Renewal**: Issue new tokens before expiration

---

## 🔐 Security & Permissions

### Token Permissions
Personal Access Token inherits all permissions of the issuing user:
- Workbook read/write
- Dashboard management
- Data Source access
- All permissions for user's Projects/Sites

### Principle of Least Privilege
- Recommend creating dedicated Tableau account for bot
- Grant only minimum required permissions
- Separate sensitive data into separate Projects

### Token Management
- Rotate tokens regularly (e.g., every 3 months)
- Delete unused tokens immediately
- Revoke and reissue immediately if token leak suspected

### Tableau Server vs Cloud
- **Tableau Server**: Internal company server, coordinate with IT team
- **Tableau Cloud**: Tableau hosted, requires internet connection

---

## 📚 References

- [Tableau REST API Documentation](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api.htm)
- [Personal Access Tokens Management](https://help.tableau.com/current/server/en-us/security_personal_access_tokens.htm)
- [Tableau MCP Server GitHub](https://github.com/tableau/mcp-server)
