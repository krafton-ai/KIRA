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
  const { app } = require("electron");
  if (!app.isPackaged) {
    return;
  }

  const updateConfigPath = path.join(process.resourcesPath, "app-update.yml");
  if (!fs.existsSync(updateConfigPath)) {
    return;
  }

  autoUpdater.logger = log;
  autoUpdater.logger.transports.file.level = "info";
  autoUpdater.setFeedURL({
    provider: "s3",
    bucket: "kira-releases",
    region: "ap-northeast-2",
    path: "/download",
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
