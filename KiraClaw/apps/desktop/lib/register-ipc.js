const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");
const { execFile } = require("child_process");
const { shell, systemPreferences } = require("electron");

function resolveUserPath(app, requestedPath) {
  const targetPath = String(requestedPath || "").trim();
  if (!targetPath) {
    return "";
  }
  if (targetPath === "~") {
    return app.getPath("home");
  }
  if (targetPath.startsWith("~/") || targetPath.startsWith("~\\")) {
    return path.join(app.getPath("home"), targetPath.slice(2));
  }
  return path.resolve(targetPath);
}

function execOpen(target) {
  return new Promise((resolve, reject) => {
    execFile("/usr/bin/open", [target], (error) => {
      if (error) {
        reject(error);
        return;
      }
      resolve();
    });
  });
}

function isPermissionDeniedError(error) {
  const code = String(error?.code || "").trim().toUpperCase();
  const message = String(error?.message || "").toLowerCase();
  return (
    code === "EPERM"
    || code === "EACCES"
    || message.includes("operation not permitted")
    || message.includes("permission denied")
  );
}

function getFullDiskAccessStatus() {
  if (process.platform !== "darwin") {
    return {
      supported: false,
      status: "unsupported",
      message: "Full Disk Access checks are available on macOS only.",
    };
  }

  const candidates = [
    path.join(os.homedir(), "Library", "Mail"),
    path.join(os.homedir(), "Library", "Messages"),
    path.join(os.homedir(), "Library", "Safari"),
    path.join(os.homedir(), "Library", "Calendars"),
    path.join(os.homedir(), "Library", "Application Support", "AddressBook"),
  ];

  let sawExistingCandidate = false;
  for (const candidate of candidates) {
    try {
      const stats = fs.statSync(candidate);
      sawExistingCandidate = true;
      if (stats.isDirectory()) {
        fs.readdirSync(candidate);
      } else {
        const fd = fs.openSync(candidate, "r");
        fs.closeSync(fd);
      }
      return {
        supported: true,
        status: "granted",
        message: "Full Disk Access appears to be enabled.",
        path: candidate,
      };
    } catch (error) {
      if (isPermissionDeniedError(error)) {
        return {
          supported: true,
          status: "not_granted",
          message: "Full Disk Access appears to be disabled.",
          path: candidate,
        };
      }
      if (String(error?.code || "").trim().toUpperCase() === "ENOENT") {
        continue;
      }
    }
  }

  return {
    supported: true,
    status: "unknown",
    message: sawExistingCandidate
      ? "KiraClaw could not confirm Full Disk Access from the current probe paths."
      : "No protected macOS probe path was found yet. Open Settings if you want to grant Full Disk Access.",
  };
}

function getScreenRecordingAccessStatus() {
  if (process.platform !== "darwin") {
    return {
      supported: false,
      status: "unsupported",
      message: "Screen Recording checks are available on macOS only.",
    };
  }

  try {
    const rawStatus = String(systemPreferences.getMediaAccessStatus("screen") || "").trim().toLowerCase();
    if (rawStatus === "granted") {
      return {
        supported: true,
        status: "granted",
        message: "Screen Recording access appears to be enabled.",
        rawStatus,
      };
    }
    if (["denied", "restricted", "not-determined", "not_determined"].includes(rawStatus)) {
      return {
        supported: true,
        status: "not_granted",
        message: "Screen Recording access appears to be disabled.",
        rawStatus,
      };
    }
    return {
      supported: true,
      status: "unknown",
      message: rawStatus
        ? `Screen Recording access returned an unrecognized status: ${rawStatus}.`
        : "KiraClaw could not confirm Screen Recording access yet.",
      rawStatus,
    };
  } catch (error) {
    return {
      supported: true,
      status: "unknown",
      message: error?.message || "KiraClaw could not read Screen Recording access.",
    };
  }
}

async function openFullDiskAccessSettings() {
  if (process.platform !== "darwin") {
    return {
      success: false,
      supported: false,
      message: "Full Disk Access settings are available on macOS only.",
    };
  }

  const urls = [
    "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles",
    "x-apple.systempreferences:com.apple.preference.security",
  ];

  let lastError = null;
  for (const url of urls) {
    try {
      await execOpen(url);
      return {
        success: true,
        supported: true,
        message: "Opened Full Disk Access settings.",
        url,
      };
    } catch (error) {
      lastError = error;
    }
  }

  return {
    success: false,
    supported: true,
    message: lastError?.message || "Failed to open Full Disk Access settings.",
  };
}

async function openScreenRecordingSettings() {
  if (process.platform !== "darwin") {
    return {
      success: false,
      supported: false,
      message: "Screen Recording settings are available on macOS only.",
    };
  }

  const urls = [
    "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
    "x-apple.systempreferences:com.apple.preference.security",
  ];

  let lastError = null;
  for (const url of urls) {
    try {
      await execOpen(url);
      return {
        success: true,
        supported: true,
        message: "Opened Screen Recording settings.",
        url,
      };
    } catch (error) {
      lastError = error;
    }
  }

  return {
    success: false,
    supported: true,
    message: lastError?.message || "Failed to open Screen Recording settings.",
  };
}

function unsupportedUpdaterState(app) {
  return {
    supported: false,
    status: "unsupported",
    version: app.getVersion(),
    progress: 0,
    message: "",
  };
}

function removePathIfExists(targetPath) {
  if (!targetPath || !fs.existsSync(targetPath)) {
    return false;
  }
  fs.rmSync(targetPath, { recursive: true, force: true });
  return true;
}

function pruneEmptyParents(startPath, stopPath) {
  let currentPath = startPath;
  const normalizedStopPath = path.resolve(stopPath);
  while (currentPath && currentPath.startsWith(normalizedStopPath) && currentPath !== normalizedStopPath) {
    if (!fs.existsSync(currentPath)) {
      currentPath = path.dirname(currentPath);
      continue;
    }
    const entries = fs.readdirSync(currentPath);
    if (entries.length > 0) {
      break;
    }
    fs.rmdirSync(currentPath);
    currentPath = path.dirname(currentPath);
  }
}

function normalizeAtlassianResource(resource) {
  const value = String(resource || "").trim();
  if (!value) {
    return "";
  }
  return `${value.replace(/\/+$/, "")}/`;
}

function getServerUrlHash(serverUrl, authorizeResource, headers = {}) {
  const parts = [serverUrl];
  if (authorizeResource) {
    parts.push(authorizeResource);
  }
  if (headers && Object.keys(headers).length > 0) {
    const sortedKeys = Object.keys(headers).sort();
    parts.push(JSON.stringify(headers, sortedKeys));
  }
  return crypto.createHash("md5").update(parts.join("|")).digest("hex");
}

function resetSlackRetrieveAuth({ configStore }) {
  const currentConfig = configStore.read();
  if (!currentConfig.SLACK_RETRIEVE_TOKEN) {
    return {
      success: true,
      removedCount: 0,
      service: "slack-retrieve",
    };
  }
  configStore.write({ SLACK_RETRIEVE_TOKEN: "" });
  return {
    success: true,
    removedCount: 1,
    service: "slack-retrieve",
  };
}

function resetMs365Auth() {
  const authRecordPath = path.join(os.homedir(), ".lokka", "auth-record.json");
  const removed = removePathIfExists(authRecordPath);
  if (removed) {
    pruneEmptyParents(path.dirname(authRecordPath), path.join(os.homedir(), ".lokka"));
  }
  return {
    success: true,
    removedCount: removed ? 1 : 0,
    service: "ms365",
    hasSystemCacheNote: true,
  };
}

function resetAtlassianAuth(options = {}) {
  const authRoot = path.join(os.homedir(), ".mcp-auth");
  const serverUrl = "https://mcp.atlassian.com/v1/sse";
  const hashes = new Set([
    getServerUrlHash(serverUrl, ""),
  ]);

  for (const resource of [
    normalizeAtlassianResource(options.confluenceSiteUrl),
    normalizeAtlassianResource(options.jiraSiteUrl),
  ]) {
    if (resource) {
      hashes.add(getServerUrlHash(serverUrl, resource));
    }
  }

  let removedCount = 0;
  if (fs.existsSync(authRoot)) {
    for (const entry of fs.readdirSync(authRoot, { withFileTypes: true })) {
      if (!entry.isDirectory() || !entry.name.startsWith("mcp-remote-")) {
        continue;
      }
      const versionDir = path.join(authRoot, entry.name);
      for (const fileName of fs.readdirSync(versionDir)) {
        if (![...hashes].some((hash) => fileName.startsWith(`${hash}_`))) {
          continue;
        }
        const filePath = path.join(versionDir, fileName);
        if (removePathIfExists(filePath)) {
          removedCount += 1;
        }
      }
      pruneEmptyParents(versionDir, authRoot);
    }
  }

  return {
    success: true,
    removedCount,
    service: "atlassian",
  };
}

function resetAuthState(deps, service, options = {}) {
  if (service === "slack-retrieve") {
    return resetSlackRetrieveAuth(deps);
  }
  if (service === "ms365") {
    return resetMs365Auth();
  }
  if (service === "atlassian") {
    return resetAtlassianAuth(options);
  }
  throw new Error(`Unknown auth reset service: ${service}`);
}

function registerIpcHandlers({ app, ipcMain, configStore, daemonController, getUpdaterState }) {
  ipcMain.handle("get-app-meta", async () => ({
    version: app.getVersion(),
    name: app.getName(),
  }));

  ipcMain.handle("get-config", async () => configStore.read());

  ipcMain.handle("save-config", async (_event, config) => {
    configStore.write(config);
    return { success: true, configFile: configStore.configFile };
  });
  ipcMain.handle("reset-auth-state", async (_event, service, options) => resetAuthState({ configStore }, String(service || "").trim(), options || {}));

  ipcMain.handle("get-daemon-status", async () => daemonController.getStatus());
  ipcMain.handle("open-chrome-profile-setup", async () => daemonController.openChromeProfileSetup());
  ipcMain.handle("open-filesystem-base-dir", async (_event, requestedPath) => {
    const targetPath = String(requestedPath || "").trim();
    if (!targetPath) {
      return { success: false, message: "Filesystem Base Dir is empty." };
    }

    const resolvedPath = resolveUserPath(app, targetPath);
    fs.mkdirSync(resolvedPath, { recursive: true });
    const error = await shell.openPath(resolvedPath);
    if (error) {
      return { success: false, message: error };
    }
    return { success: true, message: `Opened ${resolvedPath}.`, path: resolvedPath };
  });
  ipcMain.handle("get-full-disk-access-status", async () => getFullDiskAccessStatus());
  ipcMain.handle("open-full-disk-access-settings", async () => openFullDiskAccessSettings());
  ipcMain.handle("get-screen-recording-access-status", async () => getScreenRecordingAccessStatus());
  ipcMain.handle("open-screen-recording-settings", async () => openScreenRecordingSettings());
  ipcMain.handle("relaunch-app", async () => {
    setImmediate(() => {
      app.relaunch();
      app.exit(0);
    });
    return { success: true, message: "Restarting KiraClaw..." };
  });
  ipcMain.handle("open-path", async (_event, requestedPath) => {
    const targetPath = String(requestedPath || "").trim();
    if (!targetPath) {
      return { success: false, message: "Path is empty." };
    }

    const resolvedPath = resolveUserPath(app, targetPath);
    const exists = fs.existsSync(resolvedPath);
    if (exists) {
      const stats = fs.statSync(resolvedPath);
      if (stats.isDirectory()) {
        const error = await shell.openPath(resolvedPath);
        if (error) {
          return { success: false, message: error };
        }
        return { success: true, message: `Opened ${resolvedPath}.`, path: resolvedPath };
      }

      shell.showItemInFolder(resolvedPath);
      return { success: true, message: `Revealed ${resolvedPath}.`, path: resolvedPath };
    }

    const parentDir = path.dirname(resolvedPath);
    fs.mkdirSync(parentDir, { recursive: true });
    const error = await shell.openPath(parentDir);
    if (error) {
      return { success: false, message: error };
    }
    return { success: true, message: `Opened ${parentDir}.`, path: parentDir };
  });
  ipcMain.handle("open-external", async (_event, url) => {
    const targetUrl = String(url || "").trim();
    if (!targetUrl) {
      return { success: false, message: "URL is empty." };
    }
    const error = await shell.openExternal(targetUrl);
    if (error) {
      return { success: false, message: error };
    }
    return { success: true, message: `Opened ${targetUrl}.`, url: targetUrl };
  });
  ipcMain.handle("start-daemon", async () => daemonController.start());
  ipcMain.handle("stop-daemon", async () => daemonController.stop());
  ipcMain.handle("restart-daemon", async () => daemonController.restart());
  ipcMain.handle("get-updater-state", async () => {
    const updaterState = getUpdaterState?.();
    if (!updaterState?.getState) {
      return unsupportedUpdaterState(app);
    }
    return updaterState.getState();
  });
  ipcMain.handle("check-for-updates", async () => {
    const updaterState = getUpdaterState?.();
    if (!updaterState?.checkForUpdates) {
      return unsupportedUpdaterState(app);
    }
    return updaterState.checkForUpdates();
  });
  ipcMain.handle("download-update", async () => {
    const updaterState = getUpdaterState?.();
    if (!updaterState?.downloadUpdate) {
      return unsupportedUpdaterState(app);
    }
    return updaterState.downloadUpdate();
  });
  ipcMain.handle("install-update", async () => {
    const updaterState = getUpdaterState?.();
    if (!updaterState?.installUpdate) {
      return unsupportedUpdaterState(app);
    }
    return updaterState.installUpdate();
  });
}

module.exports = {
  registerIpcHandlers,
};
