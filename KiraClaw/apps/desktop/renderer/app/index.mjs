import { applyAgentIdentity } from "./branding.mjs";
import { clearChatThread, bindChatActions } from "./chat.mjs";
import { initializePasswordToggles } from "./dom.mjs";
import { updateHomeStatus, bindHomeActions } from "./home.mjs";
import { bindNavigation } from "./navigation.mjs";
import { bindSettingsActions, applySettingsToForm, collectSettingsUpdates, setSettingsStatus } from "./settings.mjs";
import { state } from "./state.mjs";

const api = window.kiraclaw;
let engineActionTimer = null;

function renderDesktopState() {
  if (!state.settingsDirty) {
    applySettingsToForm(state);
  }
  applyAgentIdentity(state);
  updateHomeStatus(state, state.daemonStatus, state.runtime);
}

function setEngineAction(nextState) {
  state.engineAction = {
    ...state.engineAction,
    ...nextState,
  };
}

function clearEngineActionTimer() {
  if (engineActionTimer) {
    window.clearTimeout(engineActionTimer);
    engineActionTimer = null;
  }
}

function scheduleEngineActionClear() {
  clearEngineActionTimer();
  engineActionTimer = window.setTimeout(async () => {
    setEngineAction({
      action: null,
      busy: false,
      message: "",
      tone: "neutral",
      visible: false,
    });
    await refreshRuntime();
  }, 2400);
}

async function loadConfig() {
  state.config = await api.getConfig();
  renderDesktopState();
  clearChatThread(state);
}

async function loadAppMeta() {
  try {
    state.appMeta = await api.getAppMeta();
  } catch {
    state.appMeta = null;
  }
  renderDesktopState();
}

async function refreshRuntime() {
  try {
    state.daemonStatus = await api.getDaemonStatus();
  } catch {
    state.daemonStatus = state.daemonStatus || null;
  }

  if (!state.daemonStatus?.running) {
    try {
      state.runtime = await api.getRuntime();
      state.daemonStatus = {
        ...(state.daemonStatus || {}),
        running: true,
      };
      renderDesktopState();
      return;
    } catch {
      state.runtime = null;
      renderDesktopState();
      return;
    }
  }

  try {
    state.runtime = await api.getRuntime();
  } catch {
    state.runtime = null;
  }

  renderDesktopState();
}

async function saveSettings({ restart = false } = {}) {
  setSettingsStatus("Saving settings...");

  try {
    const updates = collectSettingsUpdates(state);
    await api.saveConfig(updates);
    state.config = { ...state.config, ...updates };
    state.settingsDirty = false;
    applyAgentIdentity(state);

    if (restart) {
      setEngineAction({
        action: "restart",
        busy: true,
        message: "Restarting KIRA Engine with the new settings...",
        tone: "progress",
        visible: true,
      });
      await refreshRuntime();
      const result = await api.restartDaemon();
      setEngineAction({
        action: "restart",
        busy: false,
        message: result.success ? "KIRA Engine restarted with the new settings." : (result.message || "KIRA Engine restart failed."),
        tone: result.success ? "success" : "error",
        visible: true,
      });
      setSettingsStatus(result.success ? "Settings saved and engine restarted." : (result.message || "Settings saved, but engine restart failed."));
      scheduleEngineActionClear();
    } else {
      setSettingsStatus("Settings saved to ~/.kira/config.env.");
    }

    await refreshRuntime();
  } catch (error) {
    setSettingsStatus(`Save failed: ${error.message}`);
  }
}

async function runDaemonAction(action) {
  setSettingsStatus(`${action} KIRA Engine...`);
  setEngineAction({
    action,
    busy: true,
    message: `${progressLabelForAction(action)} KIRA Engine...`,
    tone: "progress",
    visible: true,
  });
  await refreshRuntime();

  try {
    const actionMap = {
      start: () => api.startDaemon(),
      restart: () => api.restartDaemon(),
      stop: () => api.stopDaemon(),
    };
    const result = await actionMap[action]();
    setEngineAction({
      action,
      busy: false,
      message: result.message || `KIRA Engine ${action} completed.`,
      tone: result.success ? "success" : "error",
      visible: true,
    });
    setSettingsStatus(result.message || `KIRA Engine ${action} completed.`);
    await refreshRuntime();
    scheduleEngineActionClear();
  } catch (error) {
    setEngineAction({
      action,
      busy: false,
      message: `KIRA Engine ${action} failed: ${error.message}`,
      tone: "error",
      visible: true,
    });
    setSettingsStatus(`KIRA Engine ${action} failed: ${error.message}`);
    await refreshRuntime();
    scheduleEngineActionClear();
  }
}

function progressLabelForAction(action) {
  const labels = {
    start: "Starting",
    restart: "Restarting",
    stop: "Stopping",
  };
  return labels[action] || "Updating";
}

function bindActions() {
  bindNavigation({
    onViewChange: (viewName) => {
      if (viewName === "overview") {
        renderDesktopState();
        refreshRuntime().catch(() => {});
      }
    },
  });
  bindHomeActions({
    onStart: () => runDaemonAction("start"),
    onRestart: () => runDaemonAction("restart"),
    onStop: () => runDaemonAction("stop"),
  });
  bindSettingsActions({
    state,
    onReload: loadConfig,
    onSave: () => saveSettings({ restart: false }),
    onSaveAndRestart: () => saveSettings({ restart: true }),
  });
  document.getElementById("open-browser-profile-setup")?.addEventListener("click", async () => {
    setSettingsStatus("Opening Chrome profile setup...");
    try {
      const result = await api.openChromeProfileSetup();
      setSettingsStatus(result.message || "Chrome profile setup opened.");
    } catch (error) {
      setSettingsStatus(`Profile setup failed: ${error.message}`);
    }
  });
  bindChatActions({
    api,
    state,
    onAfterSend: refreshRuntime,
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  initializePasswordToggles();
  bindActions();
  await loadAppMeta();
  await loadConfig();
  await refreshRuntime();
  window.setInterval(() => {
    refreshRuntime().catch(() => {});
  }, 5000);
});
