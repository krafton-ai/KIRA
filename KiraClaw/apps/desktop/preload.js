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
  startDaemon() {
    return ipcRenderer.invoke("start-daemon");
  },
  stopDaemon() {
    return ipcRenderer.invoke("stop-daemon");
  },
  restartDaemon() {
    return ipcRenderer.invoke("restart-daemon");
  },
  getRuntime() {
    return request("/v1/runtime");
  },
  getWatches() {
    return request("/v1/watches");
  },
  getWatchRuns(limit = 50, watchId = "") {
    const query = new URLSearchParams();
    query.set("limit", String(limit));
    if (watchId) {
      query.set("watch_id", watchId);
    }
    return request(`/v1/watch-runs?${query.toString()}`);
  },
  saveWatch(payload) {
    return request("/v1/watches", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  deleteWatch(watchId) {
    return request(`/v1/watches/${encodeURIComponent(watchId)}`, {
      method: "DELETE",
    });
  },
  runWatchNow(watchId) {
    return request(`/v1/watches/${encodeURIComponent(watchId)}/run`, {
      method: "POST",
    });
  },
  runPrompt(payload) {
    return request("/v1/runs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
});
