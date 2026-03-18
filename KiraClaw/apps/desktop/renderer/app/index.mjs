import { applyAgentIdentity } from "./branding.mjs";
import { clearChatThread, bindChatActions } from "./chat.mjs";
import { byId, initializePasswordToggles, setText } from "./dom.mjs";
import { updateHomeStatus, bindHomeActions } from "./home.mjs";
import { bindNavigation } from "./navigation.mjs";
import { bindSettingsActions, applySettingsToForm, collectSettingsUpdates, setSettingsStatus } from "./settings.mjs";
import { bindSkillsActions, renderSkillsState } from "./skills.mjs";
import { bindScheduleActions, renderSchedulesState } from "./schedules.mjs";
import { bindRunLogActions, renderRunLogsState } from "./logs.mjs";
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

async function refreshActiveView() {
  await refreshRuntime();
  if (state.activeView === "skills") {
    await loadSkills();
  }
  if (state.activeView === "schedules") {
    await loadSchedules();
  }
  if (state.activeView === "runs") {
    await loadRunLogs();
  }
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

async function loadSkills() {
  try {
    state.skills = await api.getSkills();
    renderSkillsState(state);
  } catch (error) {
    state.skills = { skills: [] };
    setSettingsStatus(`Skill load failed: ${error.message}`);
    renderSkillsState(state);
  }
}

async function loadSchedules() {
  try {
    const response = await api.getSchedules();
    state.schedules = response.schedules || [];
    state.scheduleFile = response.schedule_file || "";
    state.scheduleError = "";
    renderSchedulesState(state);
  } catch (error) {
    state.schedules = [];
    state.scheduleFile = "";
    state.scheduleError = error.message;
    renderSchedulesState(state);
  }
}

async function loadRunLogs() {
  try {
    const response = await api.getRunLogs(50);
    state.runLogs = response.logs || [];
    state.runLogFile = response.run_log_file || "";
    state.runLogError = "";
    renderRunLogsState(state);
  } catch (error) {
    state.runLogs = [];
    state.runLogFile = "";
    state.runLogError = error.message;
    renderRunLogsState(state);
  }
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
      state.activeView = viewName;
      if (viewName === "skills") {
        loadSkills().catch(() => {});
      }
      if (viewName === "schedules") {
        loadSchedules().catch(() => {});
      }
      if (viewName === "runs") {
        loadRunLogs().catch(() => {});
      }
      refreshRuntime().catch(() => {});
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
  document.getElementById("open-filesystem-base-dir")?.addEventListener("click", async () => {
    const input = document.getElementById("FILESYSTEM_BASE_DIR");
    const targetPath =
      input?.value.trim() ||
      state.config.FILESYSTEM_BASE_DIR ||
      state.runtime?.workspace_dir ||
      "";

    if (!targetPath) {
      setSettingsStatus("Filesystem Base Dir is empty.");
      return;
    }

    setSettingsStatus("Opening Filesystem Base Dir...");
    try {
      const result = await api.openFilesystemBaseDir(targetPath);
      setSettingsStatus(result.message || "Filesystem Base Dir opened.");
    } catch (error) {
      setSettingsStatus(`Open Folder failed: ${error.message}`);
    }
  });
  bindChatActions({
    api,
    state,
    onAfterSend: refreshRuntime,
  });
  bindSkillsActions({
    state,
    onReload: () => loadSkills(),
    onOpenPath: async (targetPath) => {
      if (!targetPath) {
        setSettingsStatus("Skill folder is not configured.");
        return;
      }
      setSettingsStatus("Opening skill folder...");
      try {
        const result = await api.openPath(targetPath);
        setSettingsStatus(result.message || "Skill folder opened.");
      } catch (error) {
        setSettingsStatus(`Open Folder failed: ${error.message}`);
      }
    },
  });
  bindScheduleActions({
    onReload: loadSchedules,
  });
  bindRunLogActions({
    state,
    onReload: loadRunLogs,
    onOpenPath: async (targetPath) => {
      if (!targetPath) {
        setSettingsStatus("Run log file is not configured.");
        return;
      }
      setSettingsStatus("Opening run log file...");
      try {
        const result = await api.openPath(targetPath);
        setSettingsStatus(result.message || "Run log file opened.");
      } catch (error) {
        setSettingsStatus(`Open Folder failed: ${error.message}`);
      }
    },
  });

  window.addEventListener("focus", () => {
    refreshActiveView().catch(() => {});
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      refreshActiveView().catch(() => {});
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  initializePasswordToggles();
  bindActions();
  await loadAppMeta();
  await loadConfig();
  await refreshActiveView();
  await loadRunLogs();
});
