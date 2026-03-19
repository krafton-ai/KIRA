function setupAutoUpdater() {
  let autoUpdater;
  let log;
  let updateLifecycle = null;

  try {
    ({ autoUpdater } = require("electron-updater"));
    log = require("electron-log");
  } catch {
    return;
  }

  const path = require("path");
  const { app, dialog, BrowserWindow } = require("electron");
  const {
    clearIncompatiblePendingUpdate,
    getAppBundlePath,
    isInApplicationsFolder,
    readUpdaterCacheDirName,
  } = require("./updater-helpers");
  if (!app.isPackaged) {
    return;
  }

  const updateConfigPath = path.join(process.resourcesPath, "app-update.yml");
  const fs = require("fs");
  if (!fs.existsSync(updateConfigPath)) {
    return;
  }
  const updaterCacheDir = path.join(
    app.getPath("cache"),
    readUpdaterCacheDirName(updateConfigPath, app.getName()),
  );

  const exePath = app.getPath("exe");
  const bundlePath = getAppBundlePath(exePath);
  log.info("Packaged app startup", {
    version: app.getVersion(),
    exePath,
    bundlePath,
    updateConfigPath,
    updaterCacheDir,
  });

  autoUpdater.logger = log;
  autoUpdater.logger.transports.file.level = "info";
  autoUpdater.logger.info(`Using packaged app-update.yml: ${updateConfigPath}`);
  clearIncompatiblePendingUpdate(updaterCacheDir, app.getName(), autoUpdater.logger);
  autoUpdater.autoDownload = false;
  autoUpdater.autoInstallOnAppQuit = true;
  app.on("before-quit-for-update", () => {
    updateLifecycle = "installing";
    log.info("Auto-update: before-quit-for-update");
  });
  let promptingForDownload = false;
  let promptingForRestart = false;
  if (!isInApplicationsFolder(bundlePath, app.getPath("home"))) {
    log.warn("Auto-update may be unreliable because the app is not running from Applications.", {
      bundlePath,
    });
    const focusedWindow = BrowserWindow.getFocusedWindow() || BrowserWindow.getAllWindows()[0] || null;
    void dialog.showMessageBox(focusedWindow, {
      type: "warning",
      buttons: ["OK"],
      defaultId: 0,
      title: "Install Location",
      message: "KiraClaw is not running from the Applications folder.",
      detail: "Automatic updates are most reliable when KiraClaw.app is installed in /Applications. If a newly downloaded app still shows an older version, make sure you are reopening the app from /Applications and not another copy in Downloads or a mounted DMG.",
    }).catch((error) => {
      log.error("Install location warning dialog failed:", error);
    });
  }

  autoUpdater.on("checking-for-update", () => {
    log.info("Auto-update: checking for update");
  });

  autoUpdater.on("update-available", async (info) => {
    log.info("Auto-update: update available", info);
    if (promptingForDownload) {
      return;
    }
    promptingForDownload = true;
    try {
      const focusedWindow = BrowserWindow.getFocusedWindow() || BrowserWindow.getAllWindows()[0] || null;
      const result = await dialog.showMessageBox(focusedWindow, {
        type: "info",
        buttons: ["Download Now", "Later"],
        defaultId: 0,
        cancelId: 1,
        title: "Update Available",
        message: `Version ${info.version} is available.`,
        detail: "Download the latest KiraClaw update in the background?",
      });
      if (result.response === 0) {
        await autoUpdater.downloadUpdate();
      }
    } catch (error) {
      log.error("Auto-update available dialog failed:", error);
    } finally {
      promptingForDownload = false;
    }
  });

  autoUpdater.on("update-not-available", (info) => {
    log.info("Auto-update: no update available", info);
  });

  autoUpdater.on("download-progress", (progress) => {
    log.info("Auto-update: download progress", progress);
  });

  autoUpdater.on("update-downloaded", async (info) => {
    log.info("Auto-update: update downloaded", info);
    if (promptingForRestart) {
      return;
    }
    promptingForRestart = true;
    try {
      const focusedWindow = BrowserWindow.getFocusedWindow() || BrowserWindow.getAllWindows()[0] || null;
      const result = await dialog.showMessageBox(focusedWindow, {
        type: "info",
        buttons: ["Restart Now", "Later"],
        defaultId: 0,
        cancelId: 1,
        title: "Update Ready",
        message: `Version ${info.version} has been downloaded.`,
        detail: "Restart now to apply the latest KiraClaw update.",
      });
      if (result.response === 0) {
        setImmediate(() => autoUpdater.quitAndInstall(false, true));
      }
    } catch (error) {
      log.error("Auto-update dialog failed:", error);
    } finally {
      promptingForRestart = false;
    }
  });

  autoUpdater.on("error", (error) => {
    log.error("Auto-update error:", error);
  });

  autoUpdater.checkForUpdates().catch((error) => {
    log.error("Auto-update check failed:", error);
  });

  return {
    isInstallingUpdate() {
      return updateLifecycle === "installing";
    },
  };
}

module.exports = {
  setupAutoUpdater,
};
