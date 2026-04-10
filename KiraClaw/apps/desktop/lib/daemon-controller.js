const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");
const net = require("net");
const { spawn, spawnSync } = require("child_process");

function createDaemonController({
  appRoot,
  configFile,
  daemonBin,
  daemonUrl,
  runtimeEnvDir,
  runtimeStateFile,
  onLog,
  isPackaged = false,
}) {
  let daemonProcess = null;
  let daemonManagedByDesktop = false;
  let browserMcpProcess = null;
  let browserMcpPort = null;
  let logBuffer = [];

  function emit(type, message) {
    const payload = {
      type,
      message: message.trimEnd(),
      timestamp: new Date().toISOString(),
    };

    logBuffer.push(payload);
    if (logBuffer.length > 300) {
      logBuffer = logBuffer.slice(-300);
    }

    onLog(payload);
  }

  async function request(path, { method = "GET", timeoutMs = 800 } = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${daemonUrl}${path}`, {
        method,
        signal: controller.signal,
      });
      return response.ok;
    } catch {
      return false;
    } finally {
      clearTimeout(timer);
    }
  }

  async function requestJson(path, { method = "GET", timeoutMs = 800 } = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${daemonUrl}${path}`, {
        method,
        signal: controller.signal,
      });
      const text = await response.text();
      let body = {};
      try {
        body = text ? JSON.parse(text) : {};
      } catch {
        body = { raw: text };
      }
      return {
        ok: response.ok,
        status: response.status,
        body,
      };
    } catch {
      return {
        ok: false,
        status: 0,
        body: null,
      };
    } finally {
      clearTimeout(timer);
    }
  }

  function isManagedRunning() {
    return Boolean(daemonProcess && daemonProcess.exitCode === null && !daemonProcess.killed);
  }

  function latestLogSummary() {
    const recent = logBuffer.slice(-8).map((entry) => entry.message.trim()).filter(Boolean);
    if (recent.length === 0) {
      return "";
    }
    return recent.join(" | ");
  }

  async function waitUntil(check, { timeoutMs = 12000, intervalMs = 250 } = {}) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      if (await check()) {
        return true;
      }
      if (daemonManagedByDesktop && daemonProcess && daemonProcess.exitCode !== null) {
        return false;
      }
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
    return false;
  }

  async function isReachable() {
    return request("/health", { timeoutMs: 800 });
  }

  async function readiness() {
    return requestJson("/ready", { timeoutMs: 1200 });
  }

  async function requestShutdown() {
    return request("/v1/admin/shutdown", {
      method: "POST",
      timeoutMs: 1200,
    });
  }

  async function getStatus() {
    const running = await isReachable();
    const readinessState = running ? await readiness() : null;
    return {
      running,
      managed: daemonManagedByDesktop && isManagedRunning(),
      mode: running ? (daemonManagedByDesktop && isManagedRunning() ? "managed" : "external") : "stopped",
      pid: daemonProcess && isManagedRunning() ? daemonProcess.pid : null,
      url: daemonUrl,
      configFile,
      ready: Boolean(readinessState?.ok),
      readiness: readinessState?.body || null,
    };
  }

  function parseEnvFile() {
    if (!fs.existsSync(configFile)) {
      return {};
    }

    const values = {};
    const raw = fs.readFileSync(configFile, "utf8");
    for (const line of raw.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) {
        continue;
      }
      const idx = trimmed.indexOf("=");
      const key = trimmed.slice(0, idx).trim();
      let value = trimmed.slice(idx + 1).trim();
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      values[key] = value;
    }
    return values;
  }

  function parseBoolean(value) {
    const normalized = String(value || "").trim().toLowerCase();
    return ["1", "true", "yes", "on"].includes(normalized);
  }

  function resolveChromeProfileDir(config) {
    const configured = String(config.CHROME_PROFILE_DIR || "").trim();
    if (configured) {
      return configured;
    }
    const workspaceDir = String(config.FILESYSTEM_BASE_DIR || "").trim()
      || path.join(os.homedir(), ".kiraclaw", "workspaces", "default");
    return path.join(workspaceDir, "chrome_profile");
  }

  function resolveChromeOutputDir(config) {
    const configured = String(config.CHROME_OUTPUT_DIR || "").trim();
    if (configured) {
      return configured;
    }
    const workspaceDir = String(config.FILESYSTEM_BASE_DIR || "").trim()
      || path.join(os.homedir(), ".kiraclaw", "workspaces", "default");
    return path.join(workspaceDir, "files");
  }

  function resolveChromeBinary() {
    if (process.platform === "darwin") {
      const appPath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
      if (fs.existsSync(appPath)) {
        return appPath;
      }
      throw new Error("Google Chrome.app is not installed in /Applications.");
    }

    if (process.platform === "win32") {
      const candidates = [
        path.join(process.env.PROGRAMFILES || "", "Google", "Chrome", "Application", "chrome.exe"),
        path.join(process.env["PROGRAMFILES(X86)"] || "", "Google", "Chrome", "Application", "chrome.exe"),
        path.join(process.env.LOCALAPPDATA || "", "Google", "Chrome", "Application", "chrome.exe"),
      ];
      const existing = candidates.find((candidate) => candidate && fs.existsSync(candidate));
      if (existing) {
        return existing;
      }
      throw new Error("chrome.exe was not found in the standard Windows install locations.");
    }

    throw new Error(`Chrome profile setup is not supported on this platform yet: ${process.platform}`);
  }

  function resolveNpxBinary() {
    const candidates = process.platform === "win32"
      ? [
          path.join(process.env.PROGRAMFILES || "", "nodejs", "npx.cmd"),
          path.join(process.env["PROGRAMFILES(X86)"] || "", "nodejs", "npx.cmd"),
          path.join(process.env.LOCALAPPDATA || "", "Programs", "nodejs", "npx.cmd"),
          path.join(process.env.APPDATA || "", "npm", "npx.cmd"),
        ]
      : [
          "/opt/homebrew/bin/npx",
          "/usr/local/bin/npx",
          path.join(os.homedir(), ".local", "bin", "npx"),
          path.join(os.homedir(), ".npm-global", "bin", "npx"),
        ];

    for (const candidate of candidates) {
      if (candidate && fs.existsSync(candidate)) {
        return candidate;
      }
    }

    const findResult = spawnSync(process.platform === "win32" ? "where" : "which", ["npx"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      windowsHide: true,
    });
    if (findResult.status === 0) {
      const firstPath = String(findResult.stdout || "").split(/\r?\n/).map((line) => line.trim()).find(Boolean);
      if (firstPath) {
        return firstPath;
      }
    }

    return null;
  }

  function isPortReachable(port, host = "127.0.0.1", timeoutMs = 500) {
    return new Promise((resolve) => {
      const socket = net.createConnection({ port, host });
      const timer = setTimeout(() => {
        socket.destroy();
        resolve(false);
      }, timeoutMs);
      socket.once("connect", () => {
        clearTimeout(timer);
        socket.destroy();
        resolve(true);
      });
      socket.once("error", () => {
        clearTimeout(timer);
        socket.destroy();
        resolve(false);
      });
    });
  }

  function findFreePort() {
    return new Promise((resolve, reject) => {
      const server = net.createServer();
      server.unref();
      server.once("error", reject);
      server.listen(0, "127.0.0.1", () => {
        const address = server.address();
        const port = address && typeof address === "object" ? address.port : null;
        server.close((error) => {
          if (error) {
            reject(error);
            return;
          }
          if (!port) {
            reject(new Error("Failed to allocate a local port."));
            return;
          }
          resolve(port);
        });
      });
    });
  }

  function resolveUvBinary() {
    const candidates = process.platform === "win32"
      ? [
          path.join(process.env.LOCALAPPDATA || "", "Programs", "uv", "uv.exe"),
          path.join(process.env.USERPROFILE || "", ".cargo", "bin", "uv.exe"),
          path.join(process.env.USERPROFILE || "", ".local", "bin", "uv.exe"),
        ]
      : [
          path.join(os.homedir(), ".local", "bin", "uv"),
          path.join(os.homedir(), ".cargo", "bin", "uv"),
          "/opt/homebrew/bin/uv",
          "/usr/local/bin/uv",
          "/usr/bin/uv",
        ];

    for (const candidate of candidates) {
      if (candidate && fs.existsSync(candidate)) {
        return candidate;
      }
    }

    const findResult = spawnSync(process.platform === "win32" ? "where" : "which", ["uv"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      windowsHide: true,
    });
    if (findResult.status === 0) {
      const firstPath = String(findResult.stdout || "").split(/\r?\n/).map((line) => line.trim()).find(Boolean);
      if (firstPath) {
        return firstPath;
      }
    }

    return null;
  }

  function getUvInstallCommand() {
    if (process.platform === "win32") {
      return {
        command: "powershell",
        args: [
          "-NoProfile",
          "-ExecutionPolicy",
          "Bypass",
          "-Command",
          "irm https://astral.sh/uv/install.ps1 | iex",
        ],
      };
    }

    return {
      command: "sh",
      args: ["-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
    };
  }

  function prependToPath(binDir) {
    const pathSep = process.platform === "win32" ? ";" : ":";
    const currentPath = process.env.PATH || "";
    const parts = currentPath.split(pathSep);
    if (!parts.includes(binDir)) {
      process.env.PATH = `${binDir}${pathSep}${currentPath}`;
    }
  }

  function withPythonUtf8(env) {
    return {
      ...env,
      PYTHONUTF8: "1",
      PYTHONIOENCODING: "utf-8",
    };
  }

  function installUv() {
    const installConfig = getUvInstallCommand();
    emit("info", "uv is missing. Installing uv automatically...");

    return new Promise((resolve, reject) => {
      const proc = spawn(installConfig.command, installConfig.args, {
        stdio: ["ignore", "pipe", "pipe"],
        windowsHide: true,
      });

      proc.stdout.on("data", (chunk) => emit("stdout", String(chunk)));
      proc.stderr.on("data", (chunk) => emit("stderr", String(chunk)));
      proc.on("error", (error) => reject(error));
      proc.on("close", (code) => {
        if (code === 0) {
          resolve();
          return;
        }
        reject(new Error(`uv install failed with code ${code}`));
      });
    });
  }

  async function ensureUvAvailable() {
    let uvPath = resolveUvBinary();
    if (uvPath) {
      prependToPath(path.dirname(uvPath));
      return uvPath;
    }

    if (!isPackaged) {
      return null;
    }

    try {
      await installUv();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      emit("error", `Automatic uv install failed: ${message}`);
      return null;
    }

    uvPath = resolveUvBinary();
    if (uvPath) {
      prependToPath(path.dirname(uvPath));
      emit("info", `uv installed successfully: ${uvPath}`);
      return uvPath;
    }

    emit("error", "uv install completed but uv could not be found afterwards.");
    return null;
  }

  async function resolveLaunchSpec(envOverrides = {}) {
    if (!isPackaged) {
      if (!fs.existsSync(daemonBin)) {
        return {
          ok: false,
          message: `KIRA Engine binary is missing: ${daemonBin}`,
        };
      }
      return {
        ok: true,
        command: daemonBin,
        args: [],
        cwd: appRoot,
        env: withPythonUtf8({
          ...process.env,
          ...envOverrides,
        }),
      };
    }

    const uvPath = await ensureUvAvailable();
    if (!uvPath) {
      return {
        ok: false,
        message: "uv is not available and automatic install failed.",
      };
    }

    const pyprojectFile = path.join(appRoot, "pyproject.toml");
    const lockFile = path.join(appRoot, "uv.lock");
    if (!fs.existsSync(pyprojectFile)) {
      return {
        ok: false,
        message: `Packaged KiraClaw project files are missing: ${pyprojectFile}`,
      };
    }
    if (!fs.existsSync(lockFile)) {
      return {
        ok: false,
        message: `Packaged KiraClaw lock file is missing: ${lockFile}`,
      };
    }

    const syncResult = await ensurePackagedRuntime({ uvPath, pyprojectFile, lockFile });
    if (!syncResult.ok) {
      return syncResult;
    }

    return {
      ok: true,
      command: uvPath,
      args: ["run", "kiraclaw-agentd"],
      cwd: appRoot,
      env: withPythonUtf8({
        ...process.env,
        ...envOverrides,
        APP_ENV: "production",
        UV_PROJECT_ENVIRONMENT: runtimeEnvDir,
      }),
    };
  }

  function readJson(filePath) {
    try {
      return JSON.parse(fs.readFileSync(filePath, "utf8"));
    } catch {
      return null;
    }
  }

  function computeRuntimeFingerprint(pyprojectFile, lockFile) {
    const hash = crypto.createHash("sha256");
    hash.update(fs.readFileSync(pyprojectFile));
    hash.update("\n---\n");
    hash.update(fs.readFileSync(lockFile));
    return hash.digest("hex");
  }

  function runtimeNeedsSync(fingerprint) {
    if (!runtimeEnvDir || !runtimeStateFile) {
      return true;
    }

    const state = readJson(runtimeStateFile);
    if (!state || state.fingerprint !== fingerprint) {
      return true;
    }

    const expectedEntrypoint = path.join(
      runtimeEnvDir,
      process.platform === "win32" ? "Scripts" : "bin",
      process.platform === "win32" ? "kiraclaw-agentd.exe" : "kiraclaw-agentd",
    );
    return !fs.existsSync(expectedEntrypoint);
  }

  function runUvSync(uvPath, env) {
    return new Promise((resolve, reject) => {
      const proc = spawn(uvPath, ["sync", "--frozen", "--no-dev"], {
        cwd: appRoot,
        env,
        stdio: ["ignore", "pipe", "pipe"],
        windowsHide: true,
      });

      proc.stdout.on("data", (chunk) => emit("stdout", String(chunk)));
      proc.stderr.on("data", (chunk) => emit("stderr", String(chunk)));
      proc.on("error", (error) => reject(error));
      proc.on("close", (code) => {
        if (code === 0) {
          resolve();
          return;
        }
        reject(new Error(`uv sync failed with code ${code}`));
      });
    });
  }

  async function ensurePackagedRuntime({ uvPath, pyprojectFile, lockFile }) {
    if (!runtimeEnvDir || !runtimeStateFile) {
      return {
        ok: false,
        message: "Runtime environment paths are not configured.",
      };
    }

    fs.mkdirSync(path.dirname(runtimeStateFile), { recursive: true });
    fs.mkdirSync(runtimeEnvDir, { recursive: true });

    const fingerprint = computeRuntimeFingerprint(pyprojectFile, lockFile);
    if (!runtimeNeedsSync(fingerprint)) {
      return { ok: true };
    }

    emit("info", "Refreshing KiraClaw Python runtime dependencies...");

    const syncEnv = withPythonUtf8({
      ...process.env,
      APP_ENV: "production",
      UV_PROJECT_ENVIRONMENT: runtimeEnvDir,
    });

    try {
      await runUvSync(uvPath, syncEnv);
      fs.writeFileSync(
        runtimeStateFile,
        `${JSON.stringify({ fingerprint }, null, 2)}\n`,
        "utf8",
      );
      emit("info", "KiraClaw Python runtime is up to date.");
      return { ok: true };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      emit("error", `Failed to refresh KiraClaw runtime: ${message}`);
      return {
        ok: false,
        message: `Failed to refresh KiraClaw runtime: ${message}`,
      };
    }
  }

  async function stopBrowserMcp() {
    const proc = browserMcpProcess;
    browserMcpProcess = null;
    browserMcpPort = null;

    if (!proc || proc.exitCode !== null) {
      return;
    }

    proc.kill(process.platform === "win32" ? "SIGTERM" : "SIGINT");
    const exited = await new Promise((resolve) => {
      const timer = setTimeout(() => resolve(false), 3000);
      proc.once("exit", () => {
        clearTimeout(timer);
        resolve(true);
      });
    });

    if (!exited && proc.exitCode === null) {
      if (process.platform === "win32") {
        spawnSync("taskkill", ["/pid", String(proc.pid), "/t", "/f"], {
          stdio: "ignore",
          windowsHide: true,
        });
      } else {
        proc.kill("SIGKILL");
      }
    }
  }

  async function ensureVisibleBrowserMcp(config) {
    await stopBrowserMcp();
    return { ok: true, port: null };
  }

  async function openChromeProfileSetup() {
    const config = parseEnvFile();
    if (!parseBoolean(config.CHROME_ENABLED)) {
      return {
        success: false,
        opened: false,
        message: "Enable Browser MCP first.",
      };
    }

    const profileDir = resolveChromeProfileDir(config);

    try {
      fs.mkdirSync(profileDir, { recursive: true });

      const chromePath = resolveChromeBinary();
      emit("info", `Opening Chrome profile setup: ${profileDir}`);
      const chrome = spawn(
        chromePath,
        [
          `--user-data-dir=${profileDir}`,
          "--no-first-run",
          "--disable-default-apps",
        ],
        {
          stdio: "ignore",
          detached: true,
        },
      );
      chrome.unref();
      return {
        success: true,
        opened: true,
        message: `Chrome profile setup opened: ${profileDir}`,
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      emit("error", `Failed to open Chrome profile setup: ${message}`);
      return {
        success: false,
        opened: false,
        message: `Failed to open Chrome profile setup: ${message}`,
      };
    }
  }

  async function start() {
    if (await isReachable()) {
      return {
        success: true,
        running: true,
        managed: daemonManagedByDesktop && isManagedRunning(),
        message: daemonManagedByDesktop ? "KIRA Engine is already running." : "KIRA Engine is already running externally.",
      };
    }

    if (isManagedRunning()) {
      const stopResult = await stopManaged();
      if (!stopResult.success) {
        return {
          success: false,
          running: true,
          managed: true,
          message: stopResult.message || "KIRA Engine is stuck in an unhealthy state.",
        };
      }
    }

    const config = parseEnvFile();
    const browserSpec = await ensureVisibleBrowserMcp(config);

    const launchEnvOverrides = {
      KIRACLAW_BROWSER_VISIBLE: "false",
    };
    if (browserSpec.port) {
      launchEnvOverrides.KIRACLAW_BROWSER_MCP_PORT = String(browserSpec.port);
    }

    const launchSpec = await resolveLaunchSpec(launchEnvOverrides);
    if (!launchSpec.ok) {
      await stopBrowserMcp();
      return {
        success: false,
        running: false,
        managed: false,
        message: launchSpec.message,
      };
    }

    daemonProcess = spawn(launchSpec.command, launchSpec.args, {
      cwd: launchSpec.cwd,
      env: launchSpec.env,
      stdio: ["ignore", "pipe", "pipe"],
      detached: process.platform !== "win32",
    });
    daemonManagedByDesktop = true;
    logBuffer = [];

    daemonProcess.stdout.on("data", (chunk) => emit("stdout", String(chunk)));
    daemonProcess.stderr.on("data", (chunk) => emit("stderr", String(chunk)));
    daemonProcess.on("error", (error) => {
      emit("error", `Failed to start KIRA Engine: ${error.message}`);
    });
    daemonProcess.on("exit", (code, signal) => {
      emit("info", `KIRA Engine exited (${signal || code || 0}).`);
      daemonProcess = null;
      daemonManagedByDesktop = false;
      void stopBrowserMcp();
    });

    const ready = await waitUntil(async () => {
      const reachable = await isReachable();
      if (!reachable) {
        return false;
      }
      const readinessState = await readiness();
      return Boolean(readinessState.ok);
    }, { timeoutMs: 180000 });
    if (!ready) {
      const details = latestLogSummary();
      await stopManaged();
      await stopBrowserMcp();
      return {
        success: false,
        running: false,
        managed: true,
        message: details
          ? `KIRA Engine failed to become ready. ${details}`
          : "KIRA Engine failed to become ready.",
      };
    }

    return {
      success: true,
      running: true,
      managed: true,
      message: "KIRA Engine started.",
    };
  }

  async function stopManaged() {
    const proc = daemonProcess;
    if (!proc || proc.exitCode !== null) {
      daemonProcess = null;
      daemonManagedByDesktop = false;
      await stopBrowserMcp();
      return { success: true, running: false, managed: false, message: "KIRA Engine is not running." };
    }

    proc.kill(process.platform === "win32" ? "SIGTERM" : "SIGINT");
    const exited = await new Promise((resolve) => {
      const timer = setTimeout(() => resolve(false), 5000);
      proc.once("exit", () => {
        clearTimeout(timer);
        resolve(true);
      });
    });

    if (!exited && proc.exitCode === null) {
      if (process.platform === "win32") {
        spawnSync("taskkill", ["/pid", String(proc.pid), "/t", "/f"], {
          stdio: "ignore",
          windowsHide: true,
        });
      } else {
        proc.kill("SIGKILL");
      }
      const forcedExit = await new Promise((resolve) => {
        const timer = setTimeout(() => resolve(false), 2000);
        proc.once("exit", () => {
          clearTimeout(timer);
          resolve(true);
        });
      });

      if (!forcedExit && proc.exitCode === null) {
        return {
          success: false,
          running: true,
          managed: true,
          message: "KIRA Engine did not stop cleanly.",
        };
      }
    }

    await stopBrowserMcp();
    return { success: true, running: false, managed: false, message: "KIRA Engine stopped." };
  }

  async function stopExternal() {
    const accepted = await requestShutdown();
    if (!accepted) {
      return { success: false, running: true, managed: false, message: "Failed to stop the running KIRA Engine." };
    }

    const stopped = await waitUntil(async () => !(await isReachable()));
    return stopped
      ? { success: true, running: false, managed: false, message: "KIRA Engine stopped." }
      : { success: false, running: true, managed: false, message: "Shutdown was requested, but the KIRA Engine is still running." };
  }

  async function stop() {
    if (daemonManagedByDesktop && isManagedRunning()) {
      return stopManaged();
    }

    if (await isReachable()) {
      return stopExternal();
    }

    return { success: true, running: false, managed: false, message: "KIRA Engine is not running." };
  }

  async function restart() {
    const stopResult = await stop();
    if (!stopResult.success) {
      return stopResult;
    }
    return start();
  }

  async function shutdownBeforeQuit() {
    if (daemonManagedByDesktop && isManagedRunning()) {
      await stop();
    }
  }

  return {
    getLogs: () => logBuffer,
    getStatus,
    restart,
    shutdownBeforeQuit,
    openChromeProfileSetup,
    start,
    stop,
  };
}

module.exports = {
  createDaemonController,
};
