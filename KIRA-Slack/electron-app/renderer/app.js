// Field IDs
const fields = [
  'SLACK_BOT_TOKEN',
  'SLACK_APP_TOKEN',
  'SLACK_SIGNING_SECRET',
  'SLACK_TEAM_ID',
  'BOT_NAME',
  'BOT_EMAIL',
  'FILESYSTEM_BASE_DIR',
  'MS365_MCP_CLIENT_ID',
  'MS365_MCP_CLIENT_SECRET',
  'MS365_MCP_TENANT_ID',
  'DEEPL_API_KEY',
  'PERPLEXITY_API_KEY',
  'CONFLUENCE_SITE_URL',
  'CONFLUENCE_USER_EMAIL',
  'CONFLUENCE_API_TOKEN'
];

// Load config on page load
document.addEventListener('DOMContentLoaded', async () => {
  const config = await window.api.getConfig();

  // Populate fields
  fields.forEach(field => {
    const element = document.getElementById(field);
    if (element && config[field]) {
      element.value = config[field];
    }
  });

  // Setup log listener
  window.api.onServerLog((data) => {
    appendLog(data);
  });
});

// Append log to container
function appendLog(data) {
  const logContainer = document.getElementById('logContainer');
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
}

// Save button
document.getElementById('saveBtn').addEventListener('click', async () => {
  const config = {};

  // Collect values
  fields.forEach(field => {
    const element = document.getElementById(field);
    if (element && element.value) {
      config[field] = element.value;
    }
  });

  // Save config
  const result = await window.api.saveConfig(config);

  const status = document.getElementById('status');
  const saveBtn = document.getElementById('saveBtn');
  const startBtn = document.getElementById('startBtn');

  if (result.success) {
    status.textContent = '✓ Settings saved successfully!';
    status.className = 'status success';

    // Show start button, hide save button
    saveBtn.style.display = 'none';
    startBtn.style.display = 'block';
  } else {
    status.textContent = '✗ Failed to save settings';
    status.className = 'status error';
  }
});

// Start button
document.getElementById('startBtn').addEventListener('click', async () => {
  const status = document.getElementById('status');
  const startBtn = document.getElementById('startBtn');
  const logSection = document.getElementById('logSection');
  const logContainer = document.getElementById('logContainer');

  status.textContent = 'Starting server...';
  status.className = 'status';

  // Clear previous logs
  logContainer.innerHTML = '';

  // Show log section
  logSection.style.display = 'flex';

  // Start server
  const result = await window.api.startServer();

  if (result.success) {
    status.textContent = '✓ Server started successfully!';
    status.className = 'status success';
    startBtn.disabled = true;
    startBtn.textContent = 'Running...';
  } else {
    status.textContent = `✗ ${result.message}`;
    status.className = 'status error';
  }
});

// Cancel button
document.getElementById('cancelBtn').addEventListener('click', () => {
  window.close();
});
