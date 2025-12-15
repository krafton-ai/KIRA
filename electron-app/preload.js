const { contextBridge, ipcRenderer } = require('electron');
const path = require('path');
const fs = require('fs');

// ============================================================================
// i18n - Load translations directly
// ============================================================================

function loadTranslations() {
  const translations = {};
  const localesPath = path.join(__dirname, 'locales');

  ['en', 'ko'].forEach(lang => {
    const filePath = path.join(localesPath, `${lang}.json`);
    try {
      if (fs.existsSync(filePath)) {
        translations[lang] = JSON.parse(fs.readFileSync(filePath, 'utf8'));
      }
    } catch (err) {
      console.error(`Failed to load ${lang}.json:`, err);
    }
  });

  return translations;
}

// ============================================================================
// Expose APIs to renderer
// ============================================================================

contextBridge.exposeInMainWorld('api', {
  // Config
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),

  // Server
  getServerStatus: () => ipcRenderer.invoke('get-server-status'),
  startServer: () => ipcRenderer.invoke('start-server'),
  stopServer: () => ipcRenderer.invoke('stop-server'),
  getVersion: () => ipcRenderer.invoke('get-version'),
  sendInput: (text) => ipcRenderer.invoke('send-input', text),

  // Language
  setLanguage: (lang) => ipcRenderer.invoke('set-language', lang),
  getLanguage: () => ipcRenderer.invoke('get-language'),

  // File system
  openDataFolder: (path) => ipcRenderer.invoke('open-data-folder', path),

  // Server logs
  onServerLog: (callback) => {
    ipcRenderer.on('server-log', (_event, data) => callback(data));
  },
  removeServerLogListener: () => {
    ipcRenderer.removeAllListeners('server-log');
  }
});

// Expose translations
contextBridge.exposeInMainWorld('i18n', {
  translations: loadTranslations()
});
