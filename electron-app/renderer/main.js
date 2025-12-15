// ============================================================================
// i18n - Simple translation system
// ============================================================================

let currentLang = 'ko';

// Get nested value from object (e.g., "nav.start" -> translations.nav.start)
function getNestedValue(obj, key) {
  return key.split('.').reduce((o, k) => (o && o[k] !== undefined) ? o[k] : null, obj);
}

// Translate a key, with optional {{variable}} interpolation
function t(key, options) {
  const translations = window.i18n?.translations || {};
  let value = getNestedValue(translations[currentLang], key);

  // Fallback to English
  if (!value && currentLang !== 'en') {
    value = getNestedValue(translations['en'], key);
  }

  if (!value) return key;

  // Replace {{variable}} placeholders
  if (options) {
    Object.keys(options).forEach(k => {
      value = value.replace(new RegExp(`{{${k}}}`, 'g'), options[k]);
    });
  }

  return value;
}

function getCurrentLanguage() {
  const saved = localStorage.getItem('kira-language');
  if (saved && ['en', 'ko'].includes(saved)) return saved;
  return 'en';
}

function changeLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('kira-language', lang);
  // Notify main process
  window.api.setLanguage(lang);
}

function updatePageTranslations() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const translated = t(el.getAttribute('data-i18n'));
    if (translated) el.textContent = translated;
  });
}

// Field IDs
const fields = [
  // 필수 - Slack
  'SLACK_BOT_TOKEN',
  'SLACK_APP_TOKEN',
  'SLACK_SIGNING_SECRET',
  'SLACK_TEAM_ID',
  // 필수 - 봇 정보
  'BOT_NAME',
  'BOT_EMAIL',
  'BOT_ORGANIZATION',
  'BOT_TEAM',
  'BOT_AUTHORIZED_USERS_EN',
  'BOT_AUTHORIZED_USERS_KR',
  'BOT_ROLE',
  'FILESYSTEM_BASE_DIR',
  // MCP 설정
  'PERPLEXITY_ENABLED',
  'PERPLEXITY_API_KEY',
  'DEEPL_ENABLED',
  'DEEPL_API_KEY',
  'GITHUB_ENABLED',
  'GITHUB_PERSONAL_ACCESS_TOKEN',
  'GITLAB_ENABLED',
  'GITLAB_API_URL',
  'GITLAB_PERSONAL_ACCESS_TOKEN',
  'MS365_ENABLED',
  'MS365_CLIENT_ID',
  'MS365_TENANT_ID',
  'ATLASSIAN_ENABLED',
  'ATLASSIAN_CONFLUENCE_SITE_URL',
  'ATLASSIAN_JIRA_SITE_URL',
  'ATLASSIAN_CONFLUENCE_DEFAULT_PAGE_ID',
  'TABLEAU_ENABLED',
  'TABLEAU_SERVER',
  'TABLEAU_SITE_NAME',
  'TABLEAU_PAT_NAME',
  'TABLEAU_PAT_VALUE',
  'X_ENABLED',
  'X_API_KEY',
  'X_API_SECRET',
  'X_ACCESS_TOKEN',
  'X_ACCESS_TOKEN_SECRET',
  'X_OAUTH2_CLIENT_ID',
  'X_OAUTH2_CLIENT_SECRET',
  'CLOVA_ENABLED',
  'CLOVA_INVOKE_URL',
  'CLOVA_SECRET_KEY',
  // Computer Use
  'CHROME_ENABLED',
  'CHROME_ALWAYS_PROFILE_SETUP',
  // 능동 수신 채널
  'OUTLOOK_CHECK_ENABLED',
  'OUTLOOK_CHECK_INTERVAL',
  'CONFLUENCE_CHECK_ENABLED',
  'CONFLUENCE_CHECK_INTERVAL',
  'CONFLUENCE_CHECK_HOURS',
  'JIRA_CHECK_ENABLED',
  'JIRA_CHECK_INTERVAL',
  // 음성 수신 채널
  'WEB_INTERFACE_ENABLED',
  'WEB_INTERFACE_AUTH_PROVIDER',
  'WEB_INTERFACE_URL',
  'WEB_SLACK_CLIENT_ID',
  'WEB_SLACK_CLIENT_SECRET',
  'WEB_MS365_CLIENT_ID',
  'WEB_MS365_CLIENT_SECRET',
  'WEB_MS365_TENANT_ID',
  // 선제적 제안 기능
  'DYNAMIC_SUGGESTER_ENABLED',
  'DYNAMIC_SUGGESTER_INTERVAL'
];

// MCP checkbox to fields mapping
const mcpMapping = {
  'PERPLEXITY_ENABLED': 'perplexity',
  'DEEPL_ENABLED': 'deepl',
  'GITHUB_ENABLED': 'github',
  'GITLAB_ENABLED': 'gitlab',
  'MS365_ENABLED': 'ms365',
  'ATLASSIAN_ENABLED': 'atlassian',
  'TABLEAU_ENABLED': 'tableau',
  'X_ENABLED': 'x',
  'CLOVA_ENABLED': 'clova'
};

// Voice channels checkbox to fields mapping
const voiceChannelMapping = {
  'WEB_INTERFACE_ENABLED': 'web'
};

// Suggester checkbox to fields mapping
const suggesterMapping = {
  'DYNAMIC_SUGGESTER_ENABLED': 'suggester'
};

let serverRunning = false;
let waitingForInput = false;
let currentBotName = 'KIRA';

// Update main message with translated text and bot name
function updateMainMessage(botName) {
  if (botName) {
    currentBotName = botName;
  }
  const mainMessageText = document.getElementById('mainMessageText');
  if (mainMessageText) {
    const message = t('landing.preparing', { botName: currentBotName });
    mainMessageText.innerHTML = message;
  }
}

// ============================================================================
// Terms Agreement Modal
// ============================================================================

function checkTermsAgreement() {
  const agreed = localStorage.getItem('kira-terms-agreed');
  return agreed === 'true';
}

function showTermsModal() {
  const modal = document.getElementById('termsModal');
  const agreeBtn = document.getElementById('termsAgreeBtn');
  const declineBtn = document.getElementById('termsDeclineBtn');

  modal.style.display = 'flex';

  agreeBtn.addEventListener('click', () => {
    localStorage.setItem('kira-terms-agreed', 'true');
    modal.style.display = 'none';
  });

  declineBtn.addEventListener('click', () => {
    window.close();
  });
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  // Initialize i18n
  currentLang = getCurrentLanguage();
  updatePageTranslations();

  // Check terms agreement on first run
  if (!checkTermsAgreement()) {
    showTermsModal();
  }

  // Sync language with main process
  window.api.setLanguage(currentLang);

  // Language toggle buttons
  const langBtns = document.querySelectorAll('.lang-btn');
  langBtns.forEach(btn => {
    // Set initial active state
    if (btn.dataset.lang === currentLang) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }

    btn.addEventListener('click', () => {
      const lang = btn.dataset.lang;
      changeLanguage(lang);

      // Update button states
      langBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      updatePageTranslations();
      updateMainMessage();
      updateServerStatus();
    });
  });

  // Load config
  const config = await window.api.getConfig();

  // Populate fields
  fields.forEach(field => {
    const element = document.getElementById(field);
    if (element) {
      if (element.type === 'checkbox') {
        element.checked = config[field] === 'True' || config[field] === true;
      } else if (config[field]) {
        element.value = config[field];
      }
    }
  });

  // Display bot name on landing screen
  const botNameDisplay = document.getElementById('botNameDisplay');
  if (config.BOT_NAME) {
    botNameDisplay.textContent = config.BOT_NAME;
  }

  // Update main message with bot name
  updateMainMessage(config.BOT_NAME);

  // Check server status
  updateServerStatus();

  // Setup navigation
  setupNavigation();

  // Setup event listeners
  setupEventListeners();

  // Initialize MCP field visibility
  initializeMcpFields();

  // Initialize External Channel checkbox dependencies
  initializeExternalChannelFields();

  // Initialize Voice Channel field visibility
  initializeVoiceChannelFields();

  // Initialize Suggester field visibility
  initializeSuggesterFields();

  // Initialize Auth fields visibility (Slack/MS365)
  initializeAuthFields();

  // Initialize Remote MCP section
  initializeRemoteMcpSection(config);

  // Add password visibility toggles
  initializePasswordToggles();

  // Display version
  displayVersion();
});

// Navigation
function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const views = document.querySelectorAll('.view');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const viewName = item.dataset.view;

      // Update active nav item
      navItems.forEach(nav => nav.classList.remove('active'));
      item.classList.add('active');

      // Update active view
      views.forEach(view => view.classList.remove('active'));
      document.getElementById(`${viewName}-view`).classList.add('active');
    });
  });
}

// Event Listeners
function setupEventListeners() {
  // Save button
  document.getElementById('saveBtn').addEventListener('click', saveConfig);

  // Server controls
  document.getElementById('startServerBtn').addEventListener('click', startServer);
  document.getElementById('stopServerBtn').addEventListener('click', stopServer);

  // Open data folder button
  const openDataFolderBtn = document.getElementById('open-data-folder');
  if (openDataFolderBtn) {
    openDataFolderBtn.addEventListener('click', async () => {
      const dataPath = document.getElementById('FILESYSTEM_BASE_DIR').value;
      if (dataPath) {
        const result = await window.api.openDataFolder(dataPath);
        if (result.error) {
          console.error('Error opening folder:', result.error);
          // Could show user-friendly error message here
        }
      } else {
        // Path is empty, maybe show a message to user
        console.log('Please enter a data storage path first');
      }
    });
  }

  // MCP checkbox toggles
  Object.keys(mcpMapping).forEach(checkboxId => {
    const checkbox = document.getElementById(checkboxId);
    if (checkbox) {
      checkbox.addEventListener('change', () => {
        toggleMcpFields(checkboxId, checkbox.checked);

        // Disable dependent checkers when MCP is disabled
        if (checkboxId === 'MS365_ENABLED') {
          const outlookCheckbox = document.getElementById('OUTLOOK_CHECK_ENABLED');
          const outlookWarning = document.getElementById('OUTLOOK_CHECK_WARNING');
          if (outlookCheckbox) {
            if (!checkbox.checked) {
              outlookCheckbox.checked = false;
              outlookCheckbox.disabled = true;
              if (outlookWarning) outlookWarning.style.display = 'block';
            } else {
              outlookCheckbox.disabled = false;
              if (outlookWarning) outlookWarning.style.display = 'none';
            }
          }
        }

        if (checkboxId === 'ATLASSIAN_ENABLED') {
          const confluenceCheckbox = document.getElementById('CONFLUENCE_CHECK_ENABLED');
          const jiraCheckbox = document.getElementById('JIRA_CHECK_ENABLED');
          const confluenceWarning = document.getElementById('CONFLUENCE_CHECK_WARNING');
          const jiraWarning = document.getElementById('JIRA_CHECK_WARNING');
          if (!checkbox.checked) {
            if (confluenceCheckbox) {
              confluenceCheckbox.checked = false;
              confluenceCheckbox.disabled = true;
              if (confluenceWarning) confluenceWarning.style.display = 'block';
            }
            if (jiraCheckbox) {
              jiraCheckbox.checked = false;
              jiraCheckbox.disabled = true;
              if (jiraWarning) jiraWarning.style.display = 'block';
            }
          } else {
            if (confluenceCheckbox) {
              confluenceCheckbox.disabled = false;
              if (confluenceWarning) confluenceWarning.style.display = 'none';
            }
            if (jiraCheckbox) {
              jiraCheckbox.disabled = false;
              if (jiraWarning) jiraWarning.style.display = 'none';
            }
          }
        }
      });
    }
  });

  // External channel checkbox toggles
  const externalChannelCheckboxes = ['OUTLOOK_CHECK_ENABLED', 'CONFLUENCE_CHECK_ENABLED', 'JIRA_CHECK_ENABLED'];
  externalChannelCheckboxes.forEach(checkboxId => {
    const checkbox = document.getElementById(checkboxId);
    if (checkbox) {
      checkbox.addEventListener('change', () => {
        toggleExternalChannelFields(checkboxId, checkbox.checked);
      });
    }
  });

  // Voice channel checkbox toggles
  Object.keys(voiceChannelMapping).forEach(checkboxId => {
    const checkbox = document.getElementById(checkboxId);
    if (checkbox) {
      checkbox.addEventListener('change', () => {
        toggleVoiceChannelFields(checkboxId, checkbox.checked);
      });
    }
  });

  // Suggester checkbox toggles
  Object.keys(suggesterMapping).forEach(checkboxId => {
    const checkbox = document.getElementById(checkboxId);
    if (checkbox) {
      checkbox.addEventListener('change', () => {
        toggleSuggesterFields(checkboxId, checkbox.checked);
      });
    }
  });

  // WEB_INTERFACE_AUTH_PROVIDER 변경 시 인증 필드 표시/숨김
  const authProviderSelect = document.getElementById('WEB_INTERFACE_AUTH_PROVIDER');
  if (authProviderSelect) {
    authProviderSelect.addEventListener('change', () => {
      toggleAuthFields(authProviderSelect.value);
    });
  }

  // Terminal-style input: listen for Enter key globally when waiting for input
  document.addEventListener('keydown', handleKeyPress);
}

// Toggle MCP fields visibility
function toggleMcpFields(checkboxId, enabled) {
  const mcpType = mcpMapping[checkboxId];
  const fieldsContainer = document.querySelector(`[data-mcp="${mcpType}"]`);

  if (fieldsContainer) {
    fieldsContainer.style.display = enabled ? 'block' : 'none';
  }
}

// Initialize MCP field visibility based on checkbox state
function initializeMcpFields() {
  Object.keys(mcpMapping).forEach(checkboxId => {
    const checkbox = document.getElementById(checkboxId);
    if (checkbox) {
      toggleMcpFields(checkboxId, checkbox.checked);
    }
  });
}

// Toggle External Channel fields visibility
function toggleExternalChannelFields(checkboxId, enabled) {
  const channelMapping = {
    'OUTLOOK_CHECK_ENABLED': 'outlook',
    'CONFLUENCE_CHECK_ENABLED': 'confluence',
    'JIRA_CHECK_ENABLED': 'jira'
  };

  const channelType = channelMapping[checkboxId];
  const fieldsContainer = document.querySelector(`[data-channel="${channelType}"]`);

  if (fieldsContainer) {
    fieldsContainer.style.display = enabled ? 'block' : 'none';
  }
}

// Initialize External Channel checkbox state based on MCP dependencies
function initializeExternalChannelFields() {
  // Check MCP dependencies first
  const ms365Enabled = document.getElementById('MS365_ENABLED')?.checked;
  const atlassianEnabled = document.getElementById('ATLASSIAN_ENABLED')?.checked;

  const outlookCheckbox = document.getElementById('OUTLOOK_CHECK_ENABLED');
  const confluenceCheckbox = document.getElementById('CONFLUENCE_CHECK_ENABLED');
  const jiraCheckbox = document.getElementById('JIRA_CHECK_ENABLED');

  const outlookWarning = document.getElementById('OUTLOOK_CHECK_WARNING');
  const confluenceWarning = document.getElementById('CONFLUENCE_CHECK_WARNING');
  const jiraWarning = document.getElementById('JIRA_CHECK_WARNING');

  // Outlook Checker depends on MS365 MCP
  if (outlookCheckbox) {
    if (!ms365Enabled) {
      outlookCheckbox.checked = false;
      outlookCheckbox.disabled = true;
      if (outlookWarning) outlookWarning.style.display = 'block';
    } else {
      outlookCheckbox.disabled = false;
      if (outlookWarning) outlookWarning.style.display = 'none';
    }
    toggleExternalChannelFields('OUTLOOK_CHECK_ENABLED', outlookCheckbox.checked && !outlookCheckbox.disabled);
  }

  // Confluence/Jira Checkers depend on Atlassian MCP
  if (confluenceCheckbox) {
    if (!atlassianEnabled) {
      confluenceCheckbox.checked = false;
      confluenceCheckbox.disabled = true;
      if (confluenceWarning) confluenceWarning.style.display = 'block';
    } else {
      confluenceCheckbox.disabled = false;
      if (confluenceWarning) confluenceWarning.style.display = 'none';
    }
    toggleExternalChannelFields('CONFLUENCE_CHECK_ENABLED', confluenceCheckbox.checked && !confluenceCheckbox.disabled);
  }

  if (jiraCheckbox) {
    if (!atlassianEnabled) {
      jiraCheckbox.checked = false;
      jiraCheckbox.disabled = true;
      if (jiraWarning) jiraWarning.style.display = 'block';
    } else {
      jiraCheckbox.disabled = false;
      if (jiraWarning) jiraWarning.style.display = 'none';
    }
    toggleExternalChannelFields('JIRA_CHECK_ENABLED', jiraCheckbox.checked && !jiraCheckbox.disabled);
  }
}

// Toggle Slack Auth fields visibility based on AUTH_PROVIDER
function toggleAuthFields(provider) {
  // Slack 인증 필드 표시/숨김
  const slackAuthFields = document.querySelectorAll('[data-slack-auth]');
  const shouldShowSlack = provider === 'slack';
  slackAuthFields.forEach(field => {
    field.style.display = shouldShowSlack ? 'block' : 'none';
  });

  // MS365 인증 필드 표시/숨김
  const microsoftAuthFields = document.querySelectorAll('[data-microsoft-auth]');
  const shouldShowMicrosoft = provider === 'microsoft';
  microsoftAuthFields.forEach(field => {
    field.style.display = shouldShowMicrosoft ? 'block' : 'none';
  });
}

// Toggle Voice Channel fields visibility
function toggleVoiceChannelFields(checkboxId, enabled) {
  const channelType = voiceChannelMapping[checkboxId];
  const fieldsContainer = document.querySelector(`[data-voice="${channelType}"]`);

  if (fieldsContainer) {
    fieldsContainer.style.display = enabled ? 'block' : 'none';
  }
}

// Initialize Voice Channel field visibility based on checkbox state
function initializeVoiceChannelFields() {
  Object.keys(voiceChannelMapping).forEach(checkboxId => {
    const checkbox = document.getElementById(checkboxId);
    if (checkbox) {
      toggleVoiceChannelFields(checkboxId, checkbox.checked);
    }
  });
}

// Toggle Suggester fields visibility
function toggleSuggesterFields(checkboxId, enabled) {
  const suggesterType = suggesterMapping[checkboxId];
  const fieldsContainer = document.querySelector(`[data-suggester="${suggesterType}"]`);

  if (fieldsContainer) {
    fieldsContainer.style.display = enabled ? 'block' : 'none';
  }
}

// Initialize Auth fields visibility based on AUTH_PROVIDER
function initializeAuthFields() {
  const authProviderSelect = document.getElementById('WEB_INTERFACE_AUTH_PROVIDER');
  if (authProviderSelect) {
    toggleAuthFields(authProviderSelect.value);
  }
}

// Initialize Suggester field visibility based on checkbox state
function initializeSuggesterFields() {
  Object.keys(suggesterMapping).forEach(checkboxId => {
    const checkbox = document.getElementById(checkboxId);
    if (checkbox) {
      toggleSuggesterFields(checkboxId, checkbox.checked);
    }
  });
}

// ============================================================================
// Remote MCP Management
// ============================================================================

// Create a Remote MCP item element
function createRemoteMcpItem(server = { name: '', url: '', instruction: '' }, index = 0) {
  const item = document.createElement('div');
  item.className = 'remote-mcp-item';
  item.dataset.index = index;

  item.innerHTML = `
    <div class="remote-mcp-header">
      <span class="remote-mcp-number">#${index + 1}</span>
      <button type="button" class="btn-remove-mcp" title="Remove">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
    <div class="form-group">
      <label>${t('remoteMcp.name')}</label>
      <input type="text" class="remote-mcp-name" value="${escapeHtml(server.name)}" placeholder="e.g., myserver">
      <small class="form-hint">${t('remoteMcp.nameHint')}</small>
    </div>
    <div class="form-group">
      <label>${t('remoteMcp.url')}</label>
      <input type="text" class="remote-mcp-url" value="${escapeHtml(server.url)}" placeholder="https://mcp.example.com/v1/sse">
    </div>
    <div class="form-group">
      <label>${t('remoteMcp.instruction')}</label>
      <input type="text" class="remote-mcp-instruction" placeholder="${t('remoteMcp.instructionPlaceholder')}" value="${escapeHtml(server.instruction)}">
      <small class="form-hint remote-mcp-tool-hint">${server.name ? t('remoteMcp.toolHintFormat').replace('{name}', server.name).replace('{instruction}', server.instruction || '...') : t('remoteMcp.toolHint')}</small>
    </div>
  `;

  // Add remove button handler
  item.querySelector('.btn-remove-mcp').addEventListener('click', () => {
    item.remove();
    updateRemoteMcpNumbers();
  });

  // Update tool hint when name or instruction changes
  const nameInput = item.querySelector('.remote-mcp-name');
  const instructionInput = item.querySelector('.remote-mcp-instruction');
  const toolHint = item.querySelector('.remote-mcp-tool-hint');

  const updateToolHint = () => {
    const name = nameInput.value.trim();
    const instruction = instructionInput.value.trim();
    if (name) {
      toolHint.textContent = t('remoteMcp.toolHintFormat').replace('{name}', name).replace('{instruction}', instruction || '...');
    } else {
      toolHint.textContent = t('remoteMcp.toolHint');
    }
  };

  nameInput.addEventListener('input', updateToolHint);
  instructionInput.addEventListener('input', updateToolHint);

  return item;
}

// Escape HTML for safe display
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Update Remote MCP item numbers after removal
function updateRemoteMcpNumbers() {
  const items = document.querySelectorAll('.remote-mcp-item');
  items.forEach((item, index) => {
    item.dataset.index = index;
    item.querySelector('.remote-mcp-number').textContent = `#${index + 1}`;
  });
}

// Get Remote MCP servers as JSON array
function getRemoteMcpServers() {
  const items = document.querySelectorAll('.remote-mcp-item');
  const servers = [];

  items.forEach(item => {
    const name = item.querySelector('.remote-mcp-name').value.trim();
    const url = item.querySelector('.remote-mcp-url').value.trim();
    // Remove newlines from instruction to prevent JSON parsing issues
    const instruction = item.querySelector('.remote-mcp-instruction').value.trim().replace(/[\r\n]+/g, ' ');

    // Only add if name and url are provided
    if (name && url) {
      servers.push({ name, url, instruction });
    }
  });

  return servers;
}

// Initialize Remote MCP section
function initializeRemoteMcpSection(config) {
  const list = document.getElementById('remoteMcpList');
  const addBtn = document.getElementById('addRemoteMcpBtn');

  if (!list || !addBtn) return;

  // Clear existing items
  list.innerHTML = '';

  // Parse existing config
  let servers = [];
  if (config.REMOTE_MCP_SERVERS) {
    try {
      servers = JSON.parse(config.REMOTE_MCP_SERVERS);
    } catch (e) {
      console.error('Failed to parse REMOTE_MCP_SERVERS:', e);
    }
  }

  // Create items for existing servers
  servers.forEach((server, index) => {
    list.appendChild(createRemoteMcpItem(server, index));
  });

  // Add button handler
  addBtn.addEventListener('click', () => {
    const currentCount = list.querySelectorAll('.remote-mcp-item').length;
    list.appendChild(createRemoteMcpItem({}, currentCount));
  });
}

// Save Config
async function saveConfig() {
  const config = {};

  // Collect values
  fields.forEach(field => {
    const element = document.getElementById(field);
    if (element) {
      if (element.type === 'checkbox') {
        config[field] = element.checked ? 'True' : 'False';
      } else if (element.value) {
        config[field] = element.value;
      }
    }
  });

  // Collect Remote MCP servers as JSON
  const remoteMcpServers = getRemoteMcpServers();
  config['REMOTE_MCP_SERVERS'] = JSON.stringify(remoteMcpServers);

  // Save config
  const result = await window.api.saveConfig(config);

  const status = document.getElementById('saveStatus');

  if (result.success) {
    status.textContent = t('settings.saved');
    status.className = 'status success';

    // Update bot name display immediately after save
    const newBotName = document.getElementById('BOT_NAME')?.value;
    if (newBotName) {
      const botNameDisplay = document.getElementById('botNameDisplay');
      if (botNameDisplay) {
        botNameDisplay.textContent = newBotName;
      }
      updateMainMessage(newBotName);
    }

    setTimeout(() => {
      status.textContent = '';
    }, 3000);
  } else {
    status.textContent = t('settings.saveFailed');
    status.className = 'status error';
  }
}

// Start Server
async function startServer() {
  const startBtn = document.getElementById('startServerBtn');
  const mainLanding = document.getElementById('mainLanding');
  const serverScreen = document.getElementById('serverScreen');
  const logContainer = document.getElementById('logContainer');
  const status = document.getElementById('startServerStatus');

  startBtn.disabled = true;
  startBtn.textContent = t('server.starting');
  status.textContent = '';

  // Start server
  const result = await window.api.startServer();

  if (result.success) {
    serverRunning = true;

    // Hide landing, show server screen
    mainLanding.style.display = 'none';
    serverScreen.style.display = 'flex';

    // Clear previous logs
    logContainer.innerHTML = '';

    // Re-register log listener (in case it was removed on stop)
    window.api.onServerLog((data) => {
      appendLog(data);
    });

    updateServerStatus();
  } else {
    startBtn.disabled = false;
    startBtn.textContent = t('landing.startButton');

    // Show error message
    status.textContent = '✗ ' + result.message;
    status.className = 'status error';

    // Clear error after 5 seconds
    setTimeout(() => {
      status.textContent = '';
    }, 5000);
  }
}

// Stop Server
async function stopServer() {
  const stopBtn = document.getElementById('stopServerBtn');
  const mainLanding = document.getElementById('mainLanding');
  const serverScreen = document.getElementById('serverScreen');
  const startBtn = document.getElementById('startServerBtn');

  stopBtn.disabled = true;
  stopBtn.textContent = t('server.stopping');

  // Stop server
  await window.api.stopServer();

  // Clean up log listeners to prevent memory leaks
  if (window.api.removeServerLogListener) {
    window.api.removeServerLogListener();
  }

  serverRunning = false;
  waitingForInput = false;

  // Show landing, hide server screen
  serverScreen.style.display = 'none';
  mainLanding.style.display = 'flex';

  // Reset both buttons
  startBtn.disabled = false;
  startBtn.textContent = t('landing.startButton');

  stopBtn.disabled = false;
  stopBtn.textContent = t('server.stop');

  updateServerStatus();
}

// Update Server Status
function updateServerStatus() {
  const statusEl = document.getElementById('serverStatus');

  if (serverRunning) {
    statusEl.textContent = t('server.statusRunning');
    statusEl.className = 'server-status running';
  } else {
    statusEl.textContent = t('server.statusStopped');
    statusEl.className = 'server-status stopped';
  }
}

// Append Log
function appendLog(data) {
  const logContainer = document.getElementById('logContainer');

  // Remove placeholder if exists
  const placeholder = logContainer.querySelector('.log-placeholder');
  if (placeholder) {
    placeholder.remove();
  }

  const logLine = document.createElement('div');
  logLine.className = 'log-line';

  // Apply styling based on log type
  if (data.type === 'stderr' || data.type === 'error') {
    logLine.classList.add('error');
  } else if (data.type === 'warning') {
    logLine.classList.add('warning');
  } else if (data.type === 'info') {
    logLine.classList.add('info');
  }

  logLine.textContent = data.message;
  logContainer.appendChild(logLine);

  // Auto-scroll to bottom
  logContainer.scrollTop = logContainer.scrollHeight;

  // Check if log contains input prompts
  checkForInputPrompt(data.message);
}

// Check for input prompts in logs
function checkForInputPrompt(message) {
  // Detect "Press ENTER to continue" pattern
  if (message.includes('Press ENTER to continue') ||
      message.includes('press ENTER') ||
      message.includes('Press ENTER')) {
    waitingForInput = true;

    // Add visual indicator to log
    const logContainer = document.getElementById('logContainer');
    const indicator = document.createElement('div');
    indicator.className = 'log-line input-waiting';
    indicator.textContent = t('server.waitingEnter');
    logContainer.appendChild(indicator);
    logContainer.scrollTop = logContainer.scrollHeight;

    // Focus log container for keyboard input
    logContainer.focus();
  }
}

// Handle keyboard input (terminal-style)
function handleKeyPress(e) {
  // Only handle Enter key when waiting for input and in server view
  if (e.key === 'Enter' && waitingForInput && serverRunning) {
    e.preventDefault();
    sendInputToPython();
  }
}

// Send input to Python process
async function sendInputToPython() {
  if (!waitingForInput) return;

  waitingForInput = false;

  try {
    const result = await window.api.sendInput('');
    if (result.success) {
      // Log the input in the UI
      const logContainer = document.getElementById('logContainer');
      const logLine = document.createElement('div');
      logLine.className = 'log-line user-input';
      logLine.textContent = '> (ENTER)';
      logContainer.appendChild(logLine);
      logContainer.scrollTop = logContainer.scrollHeight;
    } else {
      console.error('Failed to send input:', result.error);
    }
  } catch (error) {
    console.error('Error sending input:', error);
  }
}

// Initialize password visibility toggles
function initializePasswordToggles() {
  const passwordInputs = document.querySelectorAll('input[type="password"]');

  passwordInputs.forEach(input => {
    // Skip if already wrapped
    if (input.parentElement.classList.contains('input-with-toggle')) {
      return;
    }

    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'input-with-toggle';

    // Insert wrapper before input
    input.parentNode.insertBefore(wrapper, input);

    // Move input into wrapper
    wrapper.appendChild(input);

    // Create toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'toggle-visibility';
    toggleBtn.innerHTML = `
      <svg class="eye-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
      </svg>
      <svg class="eye-slash-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="display: none;">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
      </svg>
    `;

    // Add click handler
    toggleBtn.addEventListener('click', () => {
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';

      const eyeIcon = toggleBtn.querySelector('.eye-icon');
      const eyeSlashIcon = toggleBtn.querySelector('.eye-slash-icon');

      if (isPassword) {
        eyeIcon.style.display = 'none';
        eyeSlashIcon.style.display = 'block';
      } else {
        eyeIcon.style.display = 'block';
        eyeSlashIcon.style.display = 'none';
      }
    });

    // Add button to wrapper
    wrapper.appendChild(toggleBtn);
  });
}

// Display version
async function displayVersion() {
  try {
    const version = await window.api.getVersion();
    const landingVersion = document.getElementById('landingVersion');

    const versionText = `v${version}`;

    if (landingVersion) {
      landingVersion.textContent = versionText;
    }
  } catch (error) {
    console.error('Failed to get version:', error);
  }
}

