const { BrowserWindow } = require("electron");
const path = require("path");

function createMainWindow({ desktopRoot }) {
  const defaultBounds = {
    width: 900,
    height: 620,
  };

  const window = new BrowserWindow({
    width: defaultBounds.width,
    height: defaultBounds.height,
    minWidth: 640,
    minHeight: 460,
    center: true,
    show: false,
    title: "KiraClaw",
    autoHideMenuBar: true,
    backgroundColor: "#0f1217",
    titleBarStyle: process.platform === "darwin" ? "hiddenInset" : undefined,
    trafficLightPosition: process.platform === "darwin" ? { x: 14, y: 12 } : undefined,
    webPreferences: {
      preload: path.join(desktopRoot, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  window.once("ready-to-show", () => {
    window.setSize(defaultBounds.width, defaultBounds.height);
    window.center();
    window.show();
  });

  window.loadFile(path.join(desktopRoot, "renderer", "index.html"));
  return window;
}

module.exports = {
  createMainWindow,
};
