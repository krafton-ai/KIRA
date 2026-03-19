const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");

const {
  clearIncompatiblePendingUpdate,
  getAppBundlePath,
  isInApplicationsFolder,
  readUpdaterCacheDirName,
  shouldClearPendingUpdate,
} = require("./updater-helpers");

test("getAppBundlePath extracts mac app bundle path", () => {
  const exePath = "/Applications/KiraClaw.app/Contents/MacOS/KiraClaw";
  assert.equal(getAppBundlePath(exePath, "darwin"), "/Applications/KiraClaw.app");
});

test("getAppBundlePath falls back to executable directory off mac", () => {
  const exePath = "C:\\Program Files\\KiraClaw\\KiraClaw.exe";
  assert.equal(getAppBundlePath(exePath, "win32"), path.dirname(exePath));
});

test("isInApplicationsFolder accepts system and user Applications folders", () => {
  assert.equal(isInApplicationsFolder("/Applications/KiraClaw.app", "/Users/tester", "darwin"), true);
  assert.equal(isInApplicationsFolder("/Users/tester/Applications/KiraClaw.app", "/Users/tester", "darwin"), true);
  assert.equal(isInApplicationsFolder("/Users/tester/Downloads/KiraClaw.app", "/Users/tester", "darwin"), false);
});

test("readUpdaterCacheDirName reads explicit updater cache name", () => {
  const tmpdir = fs.mkdtempSync(path.join(os.tmpdir(), "kiraclaw-updater-config-"));
  const configPath = path.join(tmpdir, "app-update.yml");
  fs.writeFileSync(configPath, "provider: s3\nupdaterCacheDirName: '@kiraclawdesktop-updater'\n");
  assert.equal(readUpdaterCacheDirName(configPath, "KiraClaw"), "@kiraclawdesktop-updater");
});

test("shouldClearPendingUpdate rejects stale KIRA bundle names", () => {
  assert.equal(shouldClearPendingUpdate("KiraClaw", "KIRA-0.1.8-arm64-mac.zip"), true);
  assert.equal(shouldClearPendingUpdate("KiraClaw", "KiraClaw-0.2.0-arm64.zip"), false);
});

test("clearIncompatiblePendingUpdate removes stale pending cache", () => {
  const tmpdir = fs.mkdtempSync(path.join(os.tmpdir(), "kiraclaw-updater-cache-"));
  const cacheDir = path.join(tmpdir, "@kiraclawdesktop-updater");
  const pendingDir = path.join(cacheDir, "pending");
  fs.mkdirSync(pendingDir, { recursive: true });
  fs.writeFileSync(path.join(cacheDir, "update.zip"), "zip");
  fs.writeFileSync(
    path.join(pendingDir, "update-info.json"),
    JSON.stringify({ fileName: "KIRA-0.1.8-arm64-mac.zip" }),
  );
  fs.writeFileSync(path.join(pendingDir, "KIRA-0.1.8-arm64-mac.zip"), "zip");

  const result = clearIncompatiblePendingUpdate(cacheDir, "KiraClaw");

  assert.equal(result.cleared, true);
  assert.equal(fs.existsSync(path.join(cacheDir, "update.zip")), false);
  assert.equal(fs.existsSync(pendingDir), false);
});

test("clearIncompatiblePendingUpdate keeps compatible pending cache", () => {
  const tmpdir = fs.mkdtempSync(path.join(os.tmpdir(), "kiraclaw-updater-cache-"));
  const cacheDir = path.join(tmpdir, "@kiraclawdesktop-updater");
  const pendingDir = path.join(cacheDir, "pending");
  fs.mkdirSync(pendingDir, { recursive: true });
  fs.writeFileSync(
    path.join(pendingDir, "update-info.json"),
    JSON.stringify({ fileName: "KiraClaw-0.2.0-arm64.zip" }),
  );

  const result = clearIncompatiblePendingUpdate(cacheDir, "KiraClaw");

  assert.equal(result.cleared, false);
  assert.equal(result.reason, "compatible");
  assert.equal(fs.existsSync(pendingDir), true);
});
