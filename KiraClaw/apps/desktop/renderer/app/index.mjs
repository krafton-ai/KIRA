import { applyAgentIdentity } from "./branding.mjs";
import { clearChatThread, bindChatActions } from "./chat.mjs";
import { byId, initializePasswordToggles } from "./dom.mjs";
import { updateHomeStatus, bindHomeActions } from "./home.mjs";
import { bindNavigation } from "./navigation.mjs";
import { bindSettingsActions, applySettingsToForm, collectSettingsUpdates, setSettingsStatus } from "./settings.mjs";
import { state } from "./state.mjs";
import { bindWatchActions, collectWatchPayload, getNewWatchId, renderWatchState, setWatchStatus, validateWatchPayload } from "./watch.mjs";

const api = window.kiraclaw;
let engineActionTimer = null;

function renderDesktopState() {
  if (!state.settingsDirty) {
    applySettingsToForm(state);
  }
  applyAgentIdentity(state);
  updateHomeStatus(state, state.daemonStatus, state.runtime);
  if (!(state.activeView === "watch" && state.watchDirty)) {
    renderWatchState(state);
  }
}

async function refreshActiveView() {
  await refreshRuntime();
  if (state.activeView === "watch") {
    await loadWatchData();
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

async function loadWatchData() {
  try {
    const [watchesResponse, runsResponse] = await Promise.all([
      api.getWatches(),
      api.getWatchRuns(50),
    ]);
    state.watches = watchesResponse.watches || [];
    state.watchRuns = runsResponse.runs || [];
    if (!state.watchDraft && state.selectedWatchId && !state.watches.some((row) => row.watch_id === state.selectedWatchId)) {
      state.selectedWatchId = null;
    }
    if (!state.watchDraft && !state.selectedWatchId && state.watches.length > 0) {
      state.selectedWatchId = state.watches[0].watch_id;
    }
    if (!(state.activeView === "watch" && state.watchDirty)) {
      renderWatchState(state);
    }
  } catch (error) {
    setWatchStatus(`Watch load failed: ${error.message}`);
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

async function saveWatch(watchId) {
  setWatchStatus("Saving watch...");
  try {
    const payload = collectWatchPayload(watchId);
    if (!payload) {
      setWatchStatus("Watch form is missing.");
      return;
    }
    const validationError = validateWatchPayload(payload);
    if (validationError) {
      setWatchStatus(validationError);
      return;
    }
    const response = await api.saveWatch(payload);
    state.selectedWatchId = response.watch?.watch_id || payload.watch_id || null;
    state.watchDraft = false;
    state.watchDirty = false;
    await loadWatchData();
    setWatchStatus("Watch saved.");
  } catch (error) {
    setWatchStatus(`Watch save failed: ${error.message}`);
  }
}

async function runWatchNow(watchId) {
  if (!watchId) {
    setWatchStatus("Select a watch first.");
    return;
  }
  setWatchStatus("Running watch now...");
  try {
    const response = await api.runWatchNow(watchId);
    await loadWatchData();
    setWatchStatus(response.run?.state === "completed" ? "Watch run completed." : "Watch run finished.");
  } catch (error) {
    setWatchStatus(`Run failed: ${error.message}`);
  }
}

async function deleteWatch(watchId) {
  if (!watchId) {
    setWatchStatus("Select a watch first.");
    return;
  }
  setWatchStatus("Deleting watch...");
  try {
    await api.deleteWatch(watchId);
    state.selectedWatchId = state.selectedWatchId === watchId ? null : state.selectedWatchId;
    state.watchDraft = false;
    state.watchDirty = false;
    await loadWatchData();
    setWatchStatus("Watch deleted.");
  } catch (error) {
    setWatchStatus(`Delete failed: ${error.message}`);
  }
}

function resetWatchForm() {
  if (state.watchDraft) {
    state.selectedWatchId = getNewWatchId();
    renderWatchState(state);
    const draftConditionInput = document.querySelector(`[data-watch-item="${getNewWatchId()}"] [data-watch-input="condition"]`);
    draftConditionInput?.focus();
    draftConditionInput?.scrollIntoView({ block: "nearest" });
    setWatchStatus("Finish the current draft first.");
    return;
  }

  state.selectedWatchId = getNewWatchId();
  state.watchDraft = true;
  state.watchDirty = false;
  renderWatchState(state);
  const draftConditionInput = document.querySelector(`[data-watch-item="${getNewWatchId()}"] [data-watch-input="condition"]`);
  draftConditionInput?.focus();
  draftConditionInput?.scrollIntoView({ block: "nearest" });
  setWatchStatus("New watch form is ready.");
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
      if (viewName === "watch") {
        loadWatchData().catch(() => {});
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
  bindWatchActions({
    state,
    onSelect: (watchId) => {
      state.selectedWatchId = watchId;
      renderWatchState(state);
    },
    onReload: loadWatchData,
    onNew: resetWatchForm,
    onSave: saveWatch,
    onRunNow: runWatchNow,
    onDelete: deleteWatch,
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
});
