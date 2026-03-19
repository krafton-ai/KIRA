const fs = require("fs");
const path = require("path");

function getAppBundlePath(exePath, platform = process.platform) {
  if (platform !== "darwin") {
    return path.dirname(exePath);
  }
  const marker = ".app/";
  const index = exePath.indexOf(marker);
  if (index === -1) {
    return path.dirname(exePath);
  }
  return exePath.slice(0, index + 4);
}

function isInApplicationsFolder(bundlePath, homePath, platform = process.platform) {
  if (platform !== "darwin") {
    return true;
  }
  const normalized = path.resolve(bundlePath);
  const systemApplications = "/Applications";
  const userApplications = path.join(homePath, "Applications");
  return (
    normalized === systemApplications
    || normalized.startsWith(`${systemApplications}${path.sep}`)
    || normalized === userApplications
    || normalized.startsWith(`${userApplications}${path.sep}`)
  );
}

function readUpdaterCacheDirName(configPath, fallbackName) {
  try {
    const configText = fs.readFileSync(configPath, "utf8");
    const match = configText.match(/^\s*updaterCacheDirName:\s*(.+)\s*$/m);
    if (!match) {
      return fallbackName;
    }
    return String(match[1] || "").trim().replace(/^['"]|['"]$/g, "") || fallbackName;
  } catch {
    return fallbackName;
  }
}

function shouldClearPendingUpdate(appName, fileName) {
  const trimmed = String(fileName || "").trim();
  if (!trimmed) {
    return false;
  }
  const expectedPrefix = `${appName}-`;
  return !trimmed.startsWith(expectedPrefix);
}

function clearIncompatiblePendingUpdate(cacheDir, appName, logger = console) {
  try {
    const pendingDir = path.join(cacheDir, "pending");
    const updateInfoPath = path.join(pendingDir, "update-info.json");
    if (!fs.existsSync(updateInfoPath)) {
      return { cleared: false, reason: "missing_update_info" };
    }

    const updateInfo = JSON.parse(fs.readFileSync(updateInfoPath, "utf8"));
    const fileName = String(updateInfo.fileName || "").trim();
    if (!shouldClearPendingUpdate(appName, fileName)) {
      return { cleared: false, reason: "compatible", fileName };
    }

    logger.warn?.("Clearing incompatible pending update cache", {
      cacheDir,
      fileName,
      expectedPrefix: `${appName}-`,
    });
    fs.rmSync(pendingDir, { recursive: true, force: true });
    fs.rmSync(path.join(cacheDir, "update.zip"), { force: true });
    return { cleared: true, reason: "incompatible", fileName };
  } catch (error) {
    logger.error?.("Failed to clear incompatible pending update cache:", error);
    return { cleared: false, reason: "error", error: String(error) };
  }
}

module.exports = {
  clearIncompatiblePendingUpdate,
  getAppBundlePath,
  isInApplicationsFolder,
  readUpdaterCacheDirName,
  shouldClearPendingUpdate,
};
