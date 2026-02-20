/**
 * Platform Utilities for KIRA Electron App
 *
 * Cross-platform helpers for Windows, macOS, and Linux
 */

const os = require('os');
const path = require('path');

// Platform detection
const isWindows = process.platform === 'win32';
const isMac = process.platform === 'darwin';
const isLinux = process.platform === 'linux';

// PATH separator
const PATH_SEP = isWindows ? ';' : ':';

/**
 * Get possible UV package manager paths for current platform
 * @returns {string[]} Array of possible UV executable paths
 */
function getUvPossiblePaths() {
  const home = os.homedir();

  if (isWindows) {
    return [
      path.join(home, '.local', 'bin', 'uv.exe'),
      path.join(home, '.cargo', 'bin', 'uv.exe'),
      path.join(process.env.LOCALAPPDATA || '', 'uv', 'uv.exe'),
      path.join(process.env.APPDATA || '', 'uv', 'uv.exe'),
      path.join(process.env.LOCALAPPDATA || '', 'Programs', 'uv', 'uv.exe'),
    ];
  }

  // macOS/Linux
  return [
    path.join(home, '.cargo', 'bin', 'uv'),
    path.join(home, '.local', 'bin', 'uv'),
    '/usr/local/bin/uv',
    '/opt/homebrew/bin/uv',
  ];
}

/**
 * Get possible npm paths for current platform
 * @returns {string[]} Array of possible npm executable paths
 */
function getNpmPossiblePaths() {
  if (isWindows) {
    const programFiles = process.env['ProgramFiles'] || 'C:\\Program Files';
    const appData = process.env.APPDATA || '';
    const localAppData = process.env.LOCALAPPDATA || '';
    return [
      path.join(programFiles, 'nodejs', 'npm.cmd'),
      path.join(appData, 'npm', 'npm.cmd'),
      path.join(localAppData, 'npm', 'npm.cmd'),
    ];
  }

  return [
    '/usr/local/bin/npm',
    '/opt/homebrew/bin/npm',
  ];
}

/**
 * Get possible Claude CLI paths for current platform
 * @returns {string[]} Array of possible Claude CLI paths
 */
function getClaudeCliPossiblePaths() {
  const home = os.homedir();

  if (isWindows) {
    const appData = process.env.APPDATA || '';
    const programFiles = process.env['ProgramFiles'] || 'C:\\Program Files';
    return [
      path.join(appData, 'npm', 'claude.cmd'),
      path.join(programFiles, 'nodejs', 'claude.cmd'),
      path.join(home, '.npm-global', 'claude.cmd'),
    ];
  }

  return [
    '/usr/local/bin/claude',
    '/opt/homebrew/bin/claude',
    path.join(home, '.npm-global/bin/claude'),
  ];
}

/**
 * Get standard binary paths for current platform
 * @returns {string[]} Array of standard binary directories
 */
function getStandardBinPaths() {
  if (isWindows) {
    const programFiles = process.env['ProgramFiles'] || 'C:\\Program Files';
    const appData = process.env.APPDATA || '';
    return [
      path.join(programFiles, 'nodejs'),
      path.join(appData, 'npm'),
    ];
  }

  return [
    '/usr/local/bin',
    '/opt/homebrew/bin',
  ];
}

/**
 * Get nvm base directory for current platform
 * @returns {string} Path to nvm versions directory
 */
function getNvmBasePath() {
  const home = os.homedir();

  if (isWindows) {
    // nvm-windows stores versions in NVM_HOME or default location
    return process.env.NVM_HOME || path.join(process.env.APPDATA || '', 'nvm');
  }

  return path.join(home, '.nvm', 'versions', 'node');
}

/**
 * Get npx executable name for current platform
 * @returns {string} npx executable name (npx or npx.cmd)
 */
function getNpxName() {
  return isWindows ? 'npx.cmd' : 'npx';
}

/**
 * Get claude CLI executable name for current platform
 * @returns {string} claude executable name (claude or claude.cmd)
 */
function getClaudeName() {
  return isWindows ? 'claude.cmd' : 'claude';
}

/**
 * Get command to find executable in PATH
 * @returns {string} 'where' for Windows, 'which' for Unix
 */
function getWhichCommand() {
  return isWindows ? 'where' : 'which';
}

/**
 * Get uv installation command/arguments for current platform
 * @returns {{command: string, args: string[]}} Command and arguments for uv installation
 */
function getUvInstallCommand() {
  if (isWindows) {
    return {
      command: 'powershell',
      args: [
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-Command',
        'irm https://astral.sh/uv/install.ps1 | iex'
      ]
    };
  }

  return {
    command: 'sh',
    args: ['-c', 'curl -LsSf https://astral.sh/uv/install.sh | sh']
  };
}

/**
 * Get uv bin directory after installation
 * @returns {string} Path where uv is installed
 */
function getUvBinDir() {
  const home = os.homedir();

  if (isWindows) {
    return path.join(home, '.local', 'bin');
  }

  return path.join(home, '.cargo', 'bin');
}

module.exports = {
  isWindows,
  isMac,
  isLinux,
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
};
