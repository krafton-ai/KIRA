const { contextBridge, ipcRenderer } = require("electron");

const BASE_URL = "http://127.0.0.1:8787";
const DEFAULT_REQUEST_TIMEOUT_MS = 4000;
const RUN_PROMPT_TIMEOUT_MS = 5 * 60 * 1000;

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeoutMs = Number.isFinite(options.timeoutMs) ? options.timeoutMs : DEFAULT_REQUEST_TIMEOUT_MS;
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const { timeoutMs: _timeoutMs, signal: _externalSignal, ...requestOptions } = options;
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(requestOptions.headers || {}),
    },
    ...requestOptions,
    signal: controller.signal,
  });

  try {
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
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error(`Request timed out after ${timeoutMs}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

contextBridge.exposeInMainWorld("kiraclaw", {
  getDaemonBaseUrl() {
    return BASE_URL;
  },
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
  getFullDiskAccessStatus() {
    return ipcRenderer.invoke("get-full-disk-access-status");
  },
  openFullDiskAccessSettings() {
    return ipcRenderer.invoke("open-full-disk-access-settings");
  },
  getScreenRecordingAccessStatus() {
    return ipcRenderer.invoke("get-screen-recording-access-status");
  },
  openScreenRecordingSettings() {
    return ipcRenderer.invoke("open-screen-recording-settings");
  },
  relaunchApp() {
    return ipcRenderer.invoke("relaunch-app");
  },
  openPath(targetPath) {
    return ipcRenderer.invoke("open-path", targetPath);
  },
  openExternal(url) {
    return ipcRenderer.invoke("open-external", url);
  },
  resetAuthState(service, options = {}) {
    return ipcRenderer.invoke("reset-auth-state", service, options);
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
  getResources(kind = "") {
    const query = new URLSearchParams();
    if (kind) {
      query.set("kind", kind);
    }
    const suffix = query.toString();
    return request(`/v1/resources${suffix ? `?${suffix}` : ""}`);
  },
  getDaemonEvents(limit = 100, resourceKind = "", resourceId = "") {
    const query = new URLSearchParams();
    query.set("limit", String(limit));
    if (resourceKind) {
      query.set("resource_kind", resourceKind);
    }
    if (resourceId) {
      query.set("resource_id", resourceId);
    }
    return request(`/v1/daemon-events?${query.toString()}`);
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
      timeoutMs: RUN_PROMPT_TIMEOUT_MS,
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
