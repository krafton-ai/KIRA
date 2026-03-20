const { contextBridge, ipcRenderer } = require("electron");

const BASE_URL = "http://127.0.0.1:8787";

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const text = await response.text();
  let body;
  try {
    body = text ? JSON.parse(text) : {};
  } catch {
    body = { raw: text };
  }

  if (!response.ok) {
    const message = body.detail || body.error || body.raw || `HTTP ${response.status}`;
    throw new Error(message);
  }

  return body;
}

contextBridge.exposeInMainWorld("kiraclaw", {
  getAppMeta() {
    return ipcRenderer.invoke("get-app-meta");
  },
  getConfig() {
    return ipcRenderer.invoke("get-config");
  },
  saveConfig(config) {
    return ipcRenderer.invoke("save-config", config);
  },
  getDaemonStatus() {
    return ipcRenderer.invoke("get-daemon-status");
  },
  openChromeProfileSetup() {
    return ipcRenderer.invoke("open-chrome-profile-setup");
  },
  openFilesystemBaseDir(targetPath) {
    return ipcRenderer.invoke("open-filesystem-base-dir", targetPath);
  },
  openPath(targetPath) {
    return ipcRenderer.invoke("open-path", targetPath);
  },
  openExternal(url) {
    return ipcRenderer.invoke("open-external", url);
  },
  startDaemon() {
    return ipcRenderer.invoke("start-daemon");
  },
  stopDaemon() {
    return ipcRenderer.invoke("stop-daemon");
  },
  restartDaemon() {
    return ipcRenderer.invoke("restart-daemon");
  },
  getUpdaterState() {
    return ipcRenderer.invoke("get-updater-state");
  },
  checkForUpdates() {
    return ipcRenderer.invoke("check-for-updates");
  },
  downloadUpdate() {
    return ipcRenderer.invoke("download-update");
  },
  installUpdate() {
    return ipcRenderer.invoke("install-update");
  },
  getRuntime() {
    return request("/v1/runtime");
  },
  getSkills() {
    return request("/v1/skills");
  },
  getSchedules() {
    return request("/v1/schedules");
  },
  getRunLogs(limit = 50, sessionId = "") {
    const query = new URLSearchParams();
    query.set("limit", String(limit));
    if (sessionId) {
      query.set("session_id", sessionId);
    }
    return request(`/v1/run-logs?${query.toString()}`);
  },
  getDesktopMessages(sessionId = "desktop:local") {
    const query = new URLSearchParams();
    query.set("session_id", sessionId);
    return request(`/v1/desktop-messages?${query.toString()}`);
  },
  runPrompt(payload) {
    return request("/v1/runs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  startSlackRetrieveOAuth(payload) {
    return request("/v1/oauth/slack-retrieve/start", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getSlackRetrieveOAuthStatus() {
    return request("/v1/oauth/slack-retrieve/status");
  },
});
