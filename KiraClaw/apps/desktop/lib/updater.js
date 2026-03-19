function setupAutoUpdater() {
  let autoUpdater;
  let log;

  try {
    ({ autoUpdater } = require("electron-updater"));
    log = require("electron-log");
  } catch {
    return;
  }

  const fs = require("fs");
  const path = require("path");
  const { app, dialog, BrowserWindow } = require("electron");
  if (!app.isPackaged) {
    return;
  }

  const updateConfigPath = path.join(process.resourcesPath, "app-update.yml");
  if (!fs.existsSync(updateConfigPath)) {
    return;
  }

  autoUpdater.logger = log;
  autoUpdater.logger.transports.file.level = "info";
  autoUpdater.logger.info(`Using packaged app-update.yml: ${updateConfigPath}`);
  autoUpdater.autoDownload = true;
  autoUpdater.autoInstallOnAppQuit = true;

  autoUpdater.on("checking-for-update", () => {
    log.info("Auto-update: checking for update");
  });

  autoUpdater.on("update-available", (info) => {
    log.info("Auto-update: update available", info);
  });

  autoUpdater.on("update-not-available", (info) => {
    log.info("Auto-update: no update available", info);
  });

  autoUpdater.on("download-progress", (progress) => {
    log.info("Auto-update: download progress", progress);
  });

  autoUpdater.on("update-downloaded", async (info) => {
    log.info("Auto-update: update downloaded", info);
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
        autoUpdater.quitAndInstall();
      }
    } catch (error) {
      log.error("Auto-update dialog failed:", error);
    }
  });

  autoUpdater.on("error", (error) => {
    log.error("Auto-update error:", error);
  });

  autoUpdater.checkForUpdatesAndNotify().catch((error) => {
    log.error("Auto-update check failed:", error);
  });
}

module.exports = {
  setupAutoUpdater,
};
