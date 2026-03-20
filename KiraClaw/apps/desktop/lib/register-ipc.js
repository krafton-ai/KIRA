const fs = require("fs");
const path = require("path");
const { shell } = require("electron");

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

function registerIpcHandlers({ app, ipcMain, configStore, daemonController }) {
  ipcMain.handle("get-app-meta", async () => ({
    version: app.getVersion(),
    name: app.getName(),
  }));

  ipcMain.handle("get-config", async () => configStore.read());

  ipcMain.handle("save-config", async (_event, config) => {
    configStore.write(config);
    return { success: true, configFile: configStore.configFile };
  });

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
}

module.exports = {
  registerIpcHandlers,
};
