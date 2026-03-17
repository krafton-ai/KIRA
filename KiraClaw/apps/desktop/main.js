const { app, BrowserWindow, ipcMain } = require("electron");

const { APP_ROOT, CONFIG_DIR, CONFIG_FILE, DAEMON_BIN, DAEMON_URL, DESKTOP_ROOT } = require("./lib/constants");
const { createConfigStore } = require("./lib/config-store");
const { createDaemonController } = require("./lib/daemon-controller");
const { createMainWindow } = require("./lib/create-window");
const { registerIpcHandlers } = require("./lib/register-ipc");

const configStore = createConfigStore({
  configDir: CONFIG_DIR,
  configFile: CONFIG_FILE,
});

let mainWindow = null;

const daemonController = createDaemonController({
  appRoot: APP_ROOT,
  configFile: CONFIG_FILE,
  daemonBin: DAEMON_BIN,
  daemonUrl: DAEMON_URL,
  onLog(payload) {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send("daemon-log", payload);
    }
  },
});

function openMainWindow() {
  mainWindow = createMainWindow({
    desktopRoot: DESKTOP_ROOT,
  });
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  registerIpcHandlers({
    app,
    ipcMain,
    configStore,
    daemonController,
  });
  openMainWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      openMainWindow();
    }
  });
});

app.on("before-quit", async () => {
  await daemonController.shutdownBeforeQuit();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
