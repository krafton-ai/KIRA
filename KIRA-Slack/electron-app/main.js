/**
 * KIRA Electron Main Process
 *
 * This file manages:
 * 1. Python server lifecycle
 * 2. Claude CLI discovery (including nvm)
 * 3. uv package manager installation
 * 4. IPC communication with renderer
 * 5. Auto-updater functionality
 */

const { app, BrowserWindow, ipcMain, dialog, shell, Menu } = require('electron');
const { autoUpdater } = require('electron-updater');
const log = require('electron-log');
const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Platform utilities
const {
  isWindows,
  isMac,
  PATH_SEP,
  getUvPossiblePaths,
  getNpmPossiblePaths,
  getClaudeCliPossiblePaths,
  getStandardBinPaths,
  getNvmBasePath,
  getNpxName,
  getClaudeName,
  getWhichCommand,
  getUvInstallCommand,
  getUvBinDir,
} = require('./platform-utils');

// ============================================================================
// i18n - Internationalization
// ============================================================================

let translations = {};
let currentLang = 'en';

/**
 * Load translation files
 */
function loadTranslations() {
  try {
    const koPath = path.join(__dirname, 'locales', 'ko.json');
    const enPath = path.join(__dirname, 'locales', 'en.json');

    translations.ko = JSON.parse(fs.readFileSync(koPath, 'utf8'));
    translations.en = JSON.parse(fs.readFileSync(enPath, 'utf8'));

    log.info('Translations loaded successfully');
  } catch (err) {
    log.error('Failed to load translations:', err);
    translations = { en: {}, ko: {} };
  }
}

/**
 * Get nested value from object (e.g., "dialogs.uvRequired")
 */
function getNestedValue(obj, key) {
  return key.split('.').reduce((o, k) => (o && o[k] !== undefined) ? o[k] : null, obj);
}

/**
 * Translate a key with optional variable interpolation
 */
function t(key, options = {}) {
  let value = getNestedValue(translations[currentLang], key);

  // Fallback to English
  if (!value && currentLang !== 'en') {
    value = getNestedValue(translations['en'], key);
  }

  if (!value) return key;

  // Replace {{variable}} placeholders
  Object.keys(options).forEach(k => {
    value = value.replace(new RegExp(`{{${k}}}`, 'g'), options[k]);
  });

  return value;
}

/**
 * Get current language from localStorage (via config or default)
 */
function getCurrentLanguage() {
  // Try to read from a config file if needed, or default to 'en'
  // For now, we'll use 'en' as default, but this can be extended
  return currentLang;
}

// ============================================================================
// CONFIGURATION & CONSTANTS
// ============================================================================

const CONFIG_DIR = path.join(os.homedir(), '.kira');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.env');
const LOG_FILE = path.join(CONFIG_DIR, 'server.log');
const PID_FILE = path.join(CONFIG_DIR, 'server.pid');

// UV and npm paths are now provided by platform-utils
const UV_POSSIBLE_PATHS = getUvPossiblePaths();
const NPM_POSSIBLE_PATHS = getNpmPossiblePaths();

// ============================================================================
// GLOBAL STATE
// ============================================================================

let mainWindow = null;
let pythonProcess = null;

// Configure logging
autoUpdater.logger = log;
autoUpdater.logger.transports.file.level = 'info';

// Configure auto-updater for S3
if (app.isPackaged) {
  autoUpdater.setFeedURL({
    provider: 's3',
    bucket: 'kira-releases',
    region: 'ap-northeast-2',
    path: '/download'
  });
  log.info('Auto-updater configured for S3');
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Parse .env file into object
 */
function parseConfigFile(filePath) {
  const config = {};
  const content = fs.readFileSync(filePath, 'utf8');
  content.split('\n').forEach(line => {
    line = line.trim();
    if (line && !line.startsWith('#') && line.includes('=')) {
      const [key, ...valueParts] = line.split('=');
      let value = valueParts.join('=').replace(/^["']|["']$/g, '');
      // Restore escaped characters (reverse order of escaping)
      value = value.replace(/\\([\\"n])/g, (match, char) => {
        switch(char) {
          case '\\': return '\\';
          case '"': return '"';
          case 'n': return '\n';
          default: return match;
        }
      });
      config[key.trim()] = value;
    }
  });
  return config;
}

/**
 * Get Python project path based on environment
 */
function getPythonPath() {
  if (app.isPackaged) {
    return process.resourcesPath;
  }
  return path.join(__dirname, '..');
}

// ============================================================================
// UV PACKAGE MANAGER
// ============================================================================

/**
 * Find uv executable in system
 */
function findUvPath() {
  // Check known filesystem paths first
  for (const uvPath of UV_POSSIBLE_PATHS) {
    try {
      if (fs.existsSync(uvPath)) {
        log.info('Found uv at:', uvPath);
        return uvPath;
      }
    } catch (err) {
      // Continue checking
    }
  }

  // Try 'which' (Unix) or 'where' (Windows) command as fallback
  try {
    const findCmd = getWhichCommand();
    const result = execSync(`${findCmd} uv`, { encoding: 'utf8' }).trim();
    // 'where' on Windows can return multiple lines, take first
    const firstPath = result.split('\n')[0].trim();
    if (firstPath) {
      log.info('Found uv via PATH at:', firstPath);
      return firstPath;
    }
  } catch (err) {
    log.warn('uv not found in PATH');
  }

  return null;
}

/**
 * Check if uv is installed
 */
async function checkUvInstalled() {
  const uvPath = findUvPath();
  if (!uvPath) {
    return false;
  }

  return new Promise((resolve) => {
    const proc = spawn(uvPath, ['--version'], { stdio: 'pipe' });
    proc.on('close', (code) => {
      resolve(code === 0);
    });
    proc.on('error', () => {
      resolve(false);
    });
  });
}

/**
 * Install uv automatically
 */
async function installUv() {
  log.info('Installing uv package manager...');

  return new Promise((resolve, reject) => {
    const installConfig = getUvInstallCommand();
    const proc = spawn(installConfig.command, installConfig.args, { stdio: 'pipe' });

    proc.stdout.on('data', (data) => {
      log.info('uv install:', data.toString());
    });

    proc.stderr.on('data', (data) => {
      log.error('uv install error:', data.toString());
    });

    proc.on('close', (code) => {
      if (code === 0) {
        log.info('uv installed successfully');
        // Add to PATH for current session
        const uvBinDir = getUvBinDir();
        process.env.PATH = `${uvBinDir}${PATH_SEP}${process.env.PATH}`;
        resolve(true);
      } else {
        log.error('uv installation failed with code:', code);
        reject(new Error('uv installation failed'));
      }
    });
  });
}

/**
 * Ensure uv is installed (show dialog if not)
 */
async function ensureUv() {
  const isInstalled = await checkUvInstalled();

  if (isInstalled) {
    log.info('uv is already installed');
    return true;
  }

  // Show dialog to user
  const result = await dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: t('dialogs.uvRequired'),
    message: t('dialogs.uvMessage'),
    buttons: [t('dialogs.autoInstall'), t('dialogs.cancel')],
    defaultId: 0,
    cancelId: 1
  });

  if (result.response === 0) {
    try {
      await installUv();
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: t('dialogs.installComplete'),
        message: t('dialogs.uvInstallSuccess')
      });
      return true;
    } catch (error) {
      dialog.showMessageBox(mainWindow, {
        type: 'error',
        title: t('dialogs.installFailed'),
        message: `${t('dialogs.uvInstallFailed')}\n\n${error.message}`
      });
      return false;
    }
  }

  return false;
}

// ============================================================================
// CLAUDE CLI DISCOVERY
// ============================================================================

/**
 * Find Claude CLI in various locations including nvm
 * @param {Object} env - Environment variables object to modify
 * @returns {boolean} - Whether Claude CLI was found
 */
function setupClaudeCLI(env) {
  const claudeName = getClaudeName();

  // Get platform-specific possible paths
  const possiblePaths = getClaudeCliPossiblePaths();

  // Try to find npm and get its global bin
  try {
    for (const npmPath of NPM_POSSIBLE_PATHS) {
      if (fs.existsSync(npmPath)) {
        const globalNpmRoot = execSync(`"${npmPath}" root -g`, { encoding: 'utf8' }).trim();
        // On Windows: C:\Users\...\AppData\Roaming\npm\node_modules -> C:\Users\...\AppData\Roaming\npm
        // On Unix: /usr/local/lib/node_modules -> /usr/local/bin
        let globalNpmBin;
        if (isWindows) {
          globalNpmBin = path.dirname(globalNpmRoot);  // Remove node_modules
        } else {
          globalNpmBin = globalNpmRoot.replace('/lib/node_modules', '/bin');
        }
        possiblePaths.unshift(path.join(globalNpmBin, claudeName));
        log.info('Found npm global bin:', globalNpmBin);
        break;
      }
    }
  } catch (e) {
    log.warn('Could not execute npm root -g:', e.message);
  }

  // Check each possible path for Claude CLI
  for (const claudePath of possiblePaths) {
    if (fs.existsSync(claudePath)) {
      env.CLAUDE_CODE_CLI_PATH = claudePath;
      env.PATH = `${path.dirname(claudePath)}${PATH_SEP}${env.PATH}`;
      log.info('Found Claude CLI at:', claudePath);
      return true;
    }
  }

  // Check nvm installation
  const nvmBase = getNvmBasePath();
  if (fs.existsSync(nvmBase)) {
    try {
      const versions = fs.readdirSync(nvmBase);
      // On Windows nvm, versions are like v18.17.0
      // On Unix nvm, versions are like v18.17.0
      for (const version of versions) {
        let nvmClaudePath;
        if (isWindows) {
          // nvm-windows: NVM_HOME/v18.17.0/claude.cmd
          nvmClaudePath = path.join(nvmBase, version, claudeName);
        } else {
          // Unix nvm: ~/.nvm/versions/node/v18.17.0/bin/claude
          nvmClaudePath = path.join(nvmBase, version, 'bin', 'claude');
        }
        if (fs.existsSync(nvmClaudePath)) {
          env.CLAUDE_CODE_CLI_PATH = nvmClaudePath;
          env.PATH = `${path.dirname(nvmClaudePath)}${PATH_SEP}${env.PATH}`;
          log.info('Found Claude CLI via nvm:', nvmClaudePath);
          return true;
        }
      }
    } catch (e) {
      log.warn('Error reading nvm versions:', e.message);
    }
  }

  log.warn('Claude CLI not found in any standard location');
  return false;
}

/**
 * Setup Node.js/npm/npx in PATH for MCP servers
 * GUI apps don't inherit shell PATH, so we need to find npx manually
 * @param {Object} env - Environment variables object to modify
 * @returns {boolean} - Whether npx was found
 */
function setupNodePath(env) {
  const npxName = getNpxName();

  // Standard locations to check for npx
  const standardPaths = getStandardBinPaths();

  for (const binPath of standardPaths) {
    const npxPath = path.join(binPath, npxName);
    if (fs.existsSync(npxPath)) {
      // Check if binPath is already in PATH (exact match)
      const pathDirs = (env.PATH || '').split(PATH_SEP);
      if (!pathDirs.includes(binPath)) {
        env.PATH = `${binPath}${PATH_SEP}${env.PATH}`;
        log.info('Added to PATH for npx:', binPath);
      } else {
        log.info('PATH already contains:', binPath);
      }
      log.info('Found npx at:', npxPath);
      return true;
    }
  }

  // Check nvm installation
  const nvmBase = getNvmBasePath();
  if (fs.existsSync(nvmBase)) {
    try {
      const versions = fs.readdirSync(nvmBase);
      versions.sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));

      for (const version of versions) {
        let nvmBinPath;
        let nvmNpxPath;
        if (isWindows) {
          // nvm-windows: NVM_HOME/v18.17.0/npx.cmd
          nvmBinPath = path.join(nvmBase, version);
          nvmNpxPath = path.join(nvmBinPath, npxName);
        } else {
          // Unix nvm: ~/.nvm/versions/node/v18.17.0/bin/npx
          nvmBinPath = path.join(nvmBase, version, 'bin');
          nvmNpxPath = path.join(nvmBinPath, 'npx');
        }
        if (fs.existsSync(nvmNpxPath)) {
          env.PATH = `${nvmBinPath}${PATH_SEP}${env.PATH}`;
          log.info('Found npx via nvm:', nvmNpxPath);
          return true;
        }
      }
    } catch (e) {
      log.warn('Error reading nvm versions:', e.message);
    }
  }

  log.warn('npx not found - MCP servers using npx will fail');
  return false;
}

// ============================================================================
// PYTHON SERVER MANAGEMENT
// ============================================================================

/**
 * Start Python server with proper environment
 */
async function startServer() {
  // Ensure config directory exists
  if (!fs.existsSync(CONFIG_DIR)) {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
  }

  // Check config file
  // In development mode, prioritize ~/.kira/config.env if it exists
  let configFile;
  if (app.isPackaged) {
    configFile = CONFIG_FILE;
  } else {
    // Development mode: use ~/.kira/config.env if exists, otherwise use dev.env
    configFile = fs.existsSync(CONFIG_FILE)
      ? CONFIG_FILE
      : path.join(__dirname, '..', 'app', 'config', 'env', 'dev.env');
  }

  if (!fs.existsSync(configFile)) {
    const errorMsg = app.isPackaged
      ? 'Config file not found. Please configure first.'
      : `Config file not found: ${configFile}`;
    log.error(errorMsg);
    return { success: false, message: errorMsg };
  }

  log.info(`[CONFIG] Using config file: ${configFile}`);

  // Load environment
  const env = { ...process.env };
  const config = parseConfigFile(configFile);
  Object.assign(env, config);

  // Windows: Set UTF-8 encoding for Python subprocess (fixes Korean characters)
  if (process.platform === 'win32') {
    env.PYTHONIOENCODING = 'utf-8';
  }

  // Debug: Log WEB_INTERFACE_AUTH_PROVIDER
  log.info(`[CONFIG] WEB_INTERFACE_AUTH_PROVIDER from config: ${config.WEB_INTERFACE_AUTH_PROVIDER || 'NOT SET'}`);

  // Setup Node.js/npx for MCP servers (must be before setupClaudeCLI)
  setupNodePath(env);

  // Setup Claude CLI
  setupClaudeCLI(env);

  // Set APP_ENV
  if (app.isPackaged) {
    env.APP_ENV = 'production';
  } else if (!env.APP_ENV) {
    env.APP_ENV = 'dev';
  }

  // Find uv
  const uvPath = findUvPath();
  if (!uvPath) {
    log.error('uv executable not found');
    return { success: false, message: 'uv not found. Please install uv first.' };
  }

  log.info('Starting Python server with uv at:', uvPath);

  // Start Python process
  const appPath = getPythonPath();
  const logStream = fs.createWriteStream(LOG_FILE, { flags: 'a' });

  // ============ TEMPORARY TEST MODE ============
  // Options: 'test_sdk.py', 'test_cli_direct.py', 'test_agent.py', 'test_slack_bolt_context.py', or null
  // const TEST_SCRIPT = 'test_slack_bolt_context.py';  // Test sequential SDK calls
  const TEST_SCRIPT = null;  // Test sequential SDK calls
  // =============================================

  const pythonArgs = TEST_SCRIPT
    ? ['run', 'python', TEST_SCRIPT]
    : ['run', 'python', '-m', 'app.main'];

  log.info('Python args:', pythonArgs);

  pythonProcess = spawn(uvPath, pythonArgs, {
    cwd: appPath,
    env: env,
    detached: process.platform !== 'win32'  // Create process group on Unix
  });

  // Save PID to file for reliable cleanup
  try {
    fs.writeFileSync(PID_FILE, pythonProcess.pid.toString());
    log.info('Saved server PID to file:', pythonProcess.pid);
  } catch (err) {
    log.error('Failed to save PID file:', err.message);
  }

  // Pipe logs
  pythonProcess.stdout.pipe(logStream);
  pythonProcess.stderr.pipe(logStream);

  // Send logs to renderer with parsed log level
  const parseLogLevel = (logLine) => {
    // Parse Python logging format: "ERROR:", "WARNING:", "INFO:", "DEBUG:", "CRITICAL:"
    if (logLine.includes('ERROR:') || logLine.includes('CRITICAL:')) {
      return 'error';
    } else if (logLine.includes('WARNING:')) {
      return 'warning';
    } else {
      return 'info';
    }
  };

  pythonProcess.stdout.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    lines.forEach(logLine => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('server-log', {
          type: parseLogLevel(logLine),
          message: logLine
        });
      }
    });
  });

  pythonProcess.stderr.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    lines.forEach(logLine => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('server-log', {
          type: parseLogLevel(logLine),
          message: logLine
        });
      }
    });
  });

  // Handle process exit
  pythonProcess.on('exit', (code) => {
    log.info(`Python process exited with code ${code}`);
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('server-stopped');
    }
    pythonProcess = null;
  });

  return { success: true, message: 'Server started' };
}

/**
 * Stop Python server and cleanup all child processes
 */
function stopServer() {
  if (!pythonProcess) {
    console.log('Server not running');
    return;
  }

  console.log('Stopping Python server...');
  const pid = pythonProcess.pid;

  // Clear reference immediately
  pythonProcess = null;

  if (isWindows) {
    // Windows: Kill by PID tree first, then kill orphaned processes by project path
    // Step 1: Try to kill process tree by PID
    try {
      execSync(`taskkill /PID ${pid} /T /F`, { stdio: 'ignore' });
      console.log('Taskkill /T executed for PID', pid);
    } catch (err) {
      // Process may already be gone
    }

    // Step 2: Kill orphaned python processes that belong to THIS project
    // Find processes by project path, then recursively kill them and their children
    const appPath = getPythonPath().replace(/\\/g, '\\\\');  // Escape backslashes for regex
    const killOrphanScript = `
      function Kill-Tree($id) {
        Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $id } | ForEach-Object {
          Kill-Tree $_.ProcessId
          Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
      }
      Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq 'python.exe' -and $_.CommandLine -match '${appPath}'
      } | ForEach-Object {
        Kill-Tree $_.ProcessId
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
      }
    `;

    try {
      execSync(`powershell -NoProfile -Command "${killOrphanScript}"`, { stdio: 'ignore' });
      console.log('Killed orphaned Python processes for project:', appPath);
    } catch (err) {
      // No orphaned processes or PowerShell failed
    }

    // Cleanup PID file
    try {
      if (fs.existsSync(PID_FILE)) {
        fs.unlinkSync(PID_FILE);
      }
    } catch (err) {
      // Ignore cleanup errors
    }
  } else {
    // Unix: Kill process group (safe - only kills our processes)
    const killCommand = `kill -TERM -${pid} 2>/dev/null || kill -TERM ${pid} 2>/dev/null || true`;

    try {
      const killProc = spawn('sh', ['-c', killCommand]);
      killProc.on('close', () => {
        console.log('Sent SIGTERM to process group', pid);
      });
    } catch (err) {
      console.error('Error sending SIGTERM:', err);
    }

    // Force kill after 2 seconds if still running
    setTimeout(() => {
      const forceKillCommand = `kill -KILL -${pid} 2>/dev/null || kill -KILL ${pid} 2>/dev/null || true`;

      try {
        const forceKillProc = spawn('sh', ['-c', forceKillCommand]);
        forceKillProc.on('close', () => {
          console.log('Force killed process group', pid);
        });
      } catch (err) {
        console.error('Error during force kill:', err);
      }

      // Cleanup PID file
      try {
        if (fs.existsSync(PID_FILE)) {
          fs.unlinkSync(PID_FILE);
        }
      } catch (e) {
        // Ignore cleanup errors
      }
    }, 2000);
  }
}

/**
 * Check if server is running
 */
function isServerRunning() {
  return pythonProcess !== null && pythonProcess.exitCode === null;
}

// ============================================================================
// ELECTRON WINDOW MANAGEMENT
// ============================================================================

/**
 * Create the main application window
 */
function createMainWindow() {
  // Base window options
  const windowOptions = {
    width: 900,
    height: 620,
    minWidth: 800,
    minHeight: 520,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,  // Allow fs/path in preload for i18n
      preload: path.join(__dirname, 'preload.js')
    }
  };

  // Platform-specific window styling
  if (isMac) {
    // macOS: Use hidden title bar with traffic light controls
    windowOptions.titleBarStyle = 'hiddenInset';
    windowOptions.trafficLightPosition = { x: 20, y: 20 };
  } else if (isWindows) {
    // Windows: Use default frame
    windowOptions.frame = true;
  }

  mainWindow = new BrowserWindow(windowOptions);

  mainWindow.loadFile('renderer/index.html');

  // Open DevTools in development
  if (!app.isPackaged) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ============================================================================
// IPC HANDLERS
// ============================================================================

/**
 * Register all IPC handlers
 */
function registerIPCHandlers() {
  // Config management
  ipcMain.handle('get-config', async () => {
    if (!fs.existsSync(CONFIG_FILE)) {
      return {};
    }
    return parseConfigFile(CONFIG_FILE);
  });

  ipcMain.handle('save-config', async (_event, config) => {
    // Ensure directory exists
    if (!fs.existsSync(CONFIG_DIR)) {
      fs.mkdirSync(CONFIG_DIR, { recursive: true });
    }

    // Build config sections
    const sections = {
      'Slack 연동': ['SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'SLACK_SIGNING_SECRET', 'SLACK_TEAM_ID'],
      '봇 정보': ['BOT_NAME', 'BOT_EMAIL', 'BOT_ORGANIZATION', 'BOT_TEAM', 'BOT_AUTHORIZED_USERS_EN', 'BOT_AUTHORIZED_USERS_KR', 'BOT_ROLE', 'FILESYSTEM_BASE_DIR'],
      'AI 모델 설정': ['MODEL_FOR_SIMPLE', 'MODEL_FOR_MODERATE', 'MODEL_FOR_COMPLEX'],
      'MCP 설정 - Perplexity': ['PERPLEXITY_ENABLED', 'PERPLEXITY_API_KEY'],
      'MCP 설정 - DeepL': ['DEEPL_ENABLED', 'DEEPL_API_KEY'],
      'MCP 설정 - GitHub': ['GITHUB_ENABLED', 'GITHUB_PERSONAL_ACCESS_TOKEN'],
      'MCP 설정 - GitLab': ['GITLAB_ENABLED', 'GITLAB_API_URL', 'GITLAB_PERSONAL_ACCESS_TOKEN'],
      'MCP 설정 - Microsoft 365 (Lokka)': ['MS365_ENABLED', 'MS365_CLIENT_ID', 'MS365_TENANT_ID'],
      'MCP 설정 - Atlassian Rovo': ['ATLASSIAN_ENABLED', 'ATLASSIAN_CONFLUENCE_SITE_URL', 'ATLASSIAN_JIRA_SITE_URL', 'ATLASSIAN_CONFLUENCE_DEFAULT_PAGE_ID'],
      'MCP 설정 - Tableau': ['TABLEAU_ENABLED', 'TABLEAU_SERVER', 'TABLEAU_SITE_NAME', 'TABLEAU_PAT_NAME', 'TABLEAU_PAT_VALUE'],
      'MCP 설정 - X (Twitter)': ['X_ENABLED', 'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET', 'X_OAUTH2_CLIENT_ID', 'X_OAUTH2_CLIENT_SECRET'],
      'MCP 설정 - Clova Speech': ['CLOVA_ENABLED', 'CLOVA_INVOKE_URL', 'CLOVA_SECRET_KEY'],
      'MCP 설정 - Remote MCP': ['REMOTE_MCP_SERVERS'],
      'Computer Use': ['CHROME_ENABLED', 'CHROME_ALWAYS_PROFILE_SETUP'],
      '웹 서버 / 음성 수신 채널': ['WEB_INTERFACE_ENABLED', 'WEB_INTERFACE_AUTH_PROVIDER', 'WEB_INTERFACE_URL', 'WEB_SLACK_CLIENT_ID', 'WEB_SLACK_CLIENT_SECRET', 'WEB_MS365_CLIENT_ID', 'WEB_MS365_CLIENT_SECRET', 'WEB_MS365_TENANT_ID'],
      '능동 수신 채널 - Outlook': ['OUTLOOK_CHECK_ENABLED', 'OUTLOOK_CHECK_INTERVAL'],
      '능동 수신 채널 - Confluence': ['CONFLUENCE_CHECK_ENABLED', 'CONFLUENCE_CHECK_INTERVAL', 'CONFLUENCE_CHECK_HOURS'],
      '능동 수신 채널 - Jira': ['JIRA_CHECK_ENABLED', 'JIRA_CHECK_INTERVAL'],
      '선제적 제안 기능': ['DYNAMIC_SUGGESTER_ENABLED', 'DYNAMIC_SUGGESTER_INTERVAL'],
      '디버그': ['DEBUG_SLACK_MESSAGES_ENABLED']
    };

    // Default values for int fields (matching settings.py defaults)
    const intDefaults = {
      'OUTLOOK_CHECK_INTERVAL': '5',
      'CONFLUENCE_CHECK_INTERVAL': '60',
      'CONFLUENCE_CHECK_HOURS': '1',
      'JIRA_CHECK_INTERVAL': '30',
      'DYNAMIC_SUGGESTER_INTERVAL': '15'
    };

    // Write config file
    let content = '';
    for (const [section, vars] of Object.entries(sections)) {
      content += `# ============== ${section} ==============\n`;
      for (const varName of vars) {
        let value = config[varName] || '';
        // Use default value for empty int fields
        if (!value && intDefaults[varName]) {
          value = intDefaults[varName];
        }
        // Escape special characters for .env format
        value = value.replace(/\\/g, '\\\\');  // Escape backslashes first
        value = value.replace(/"/g, '\\"');    // Escape double quotes
        value = value.replace(/\n/g, '\\n');   // Escape newlines
        content += `${varName}="${value}"\n`;
      }
      content += '\n';
    }

    fs.writeFileSync(CONFIG_FILE, content);
    return { success: true };
  });

  // Server management
  ipcMain.handle('start-server', async () => {
    if (isServerRunning()) {
      return { success: false, message: 'Server already running' };
    }

    const uvInstalled = await ensureUv();
    if (!uvInstalled) {
      return { success: false, message: 'uv installation required' };
    }

    return await startServer();
  });

  ipcMain.handle('stop-server', async () => {
    stopServer();
    return { success: true };
  });

  ipcMain.handle('get-server-status', async () => {
    return { running: isServerRunning() };
  });

  // Version info
  ipcMain.handle('get-version', async () => {
    return app.getVersion();
  });

  // User input handling
  ipcMain.handle('send-input', async (_event, text) => {
    if (pythonProcess && pythonProcess.stdin) {
      try {
        pythonProcess.stdin.write(text + '\n');
        log.info('Sent input to Python process:', text);
        return { success: true };
      } catch (err) {
        log.error('Failed to send input to Python process:', err);
        return { success: false, error: err.message };
      }
    } else {
      log.warn('Python process not running or stdin not available');
      return { success: false, error: 'Server not running' };
    }
  });

  // Language change
  ipcMain.handle('set-language', async (_event, lang) => {
    if (['en', 'ko'].includes(lang)) {
      currentLang = lang;
      log.info('Language changed to:', lang);
      return { success: true };
    }
    return { success: false, error: 'Invalid language' };
  });

  ipcMain.handle('get-language', async () => {
    return currentLang;
  });

  ipcMain.handle('open-data-folder', async (_event, folderPath) => {
    try {
      // Expand home directory if path starts with ~
      let expandedPath = folderPath;
      if (folderPath.startsWith('~')) {
        expandedPath = path.join(os.homedir(), folderPath.slice(1));
      }

      // Create directory if it doesn't exist
      if (!fs.existsSync(expandedPath)) {
        fs.mkdirSync(expandedPath, { recursive: true });
      }

      // Open the folder in Finder/Explorer
      shell.openPath(expandedPath);

      return { success: true };
    } catch (error) {
      log.error('Error opening data folder:', error);
      return { error: error.message };
    }
  });
}

// ============================================================================
// AUTO-UPDATER EVENT HANDLERS
// ============================================================================

/**
 * Handle auto-update events
 */
function setupAutoUpdater() {
  // Checking for updates
  autoUpdater.on('checking-for-update', () => {
    log.info('Checking for updates...');
  });

  // Update available
  autoUpdater.on('update-available', (info) => {
    log.info('Update available:', info.version);
    if (mainWindow && !mainWindow.isDestroyed()) {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: t('dialogs.updateAvailable'),
        message: t('dialogs.updateAvailableMessage', { version: info.version }),
        buttons: [t('dialogs.ok')]
      });
    }
  });

  // No update available
  autoUpdater.on('update-not-available', (info) => {
    log.info('Using latest version:', info.version);
  });

  // Download in progress
  autoUpdater.on('download-progress', (progressObj) => {
    const logMessage = `Download speed: ${progressObj.bytesPerSecond} - ${progressObj.percent}% complete (${progressObj.transferred}/${progressObj.total})`;
    log.info(logMessage);
  });

  // Download complete
  autoUpdater.on('update-downloaded', (info) => {
    log.info('Update downloaded:', info.version);
    if (mainWindow && !mainWindow.isDestroyed()) {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: t('dialogs.updateReady'),
        message: t('dialogs.updateReadyMessage', { version: info.version }),
        buttons: [t('dialogs.restartNow'), t('dialogs.later')],
        defaultId: 0,
        cancelId: 1
      }).then((result) => {
        if (result.response === 0) {
          log.info('User chose to restart now');
          // Stop server before installing update
          if (isServerRunning()) {
            stopServer();
            setTimeout(() => {
              autoUpdater.quitAndInstall(false, true);
            }, 500);
          } else {
            autoUpdater.quitAndInstall(false, true);
          }
        } else {
          log.info('User chose to update later');
        }
      });
    }
  });

  // Error handling
  autoUpdater.on('error', (err) => {
    log.error('Auto-update error:', err);
    // Log error silently (don't interrupt user)
  });
}

// ============================================================================
// APPLICATION LIFECYCLE
// ============================================================================

app.whenReady().then(() => {
  // Load translations
  loadTranslations();

  createMainWindow();
  registerIPCHandlers();
  // 메뉴 완전 제거
  Menu.setApplicationMenu(null);
  // Setup and check for updates
  if (app.isPackaged) {
    setupAutoUpdater();
    // Check for updates 5 seconds after app start (don't interrupt initial loading)
    setTimeout(() => {
      autoUpdater.checkForUpdatesAndNotify();
    }, 5000);
  }
});

app.on('window-all-closed', () => {
  if (isServerRunning()) {
    stopServer();
  }
  app.quit();
});

app.on('before-quit', (event) => {
  if (isServerRunning()) {
    event.preventDefault();
    stopServer();
    setTimeout(() => {
      app.quit();
    }, 500); // Give time for cleanup
  }
});

app.on('will-quit', () => {
  if (isServerRunning()) {
    stopServer();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  }
});