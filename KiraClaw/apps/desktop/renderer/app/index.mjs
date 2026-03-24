import { applyAgentIdentity } from "./branding.mjs";
import { appendDesktopMessages, clearChatThread, bindChatActions } from "./chat.mjs";
import { byId, initializePasswordToggles, setText } from "./dom.mjs";
import { updateHomeStatus, bindHomeActions } from "./home.mjs";
import { bindNavigation } from "./navigation.mjs";
import { bindSettingsActions, applySettingsToForm, collectSettingsUpdates, setSettingsStatus } from "./settings.mjs";
import { bindSkillsActions, renderSkillsState } from "./skills.mjs";
import { bindScheduleActions, renderSchedulesState } from "./schedules.mjs";
import { bindDaemonPlaneActions, bindRunLogActions, renderDaemonPlaneState, renderRunLogsState } from "./logs.mjs";
import { initI18n, setLanguage, t } from "./i18n.mjs";
import { state } from "./state.mjs";
import { initTheme } from "./theme.mjs";

const api = window.kiraclaw;
let engineActionTimer = null;
let slackRetrieveOauthPollTimer = null;
let runLogPollTimer = null;
let updaterPollTimer = null;
let desktopMessagePollTimer = null;

function syncSlackRetrieveConnectState() {
  const connectButton = byId("connect-slack-retrieve");
  const connectHint = byId("slack-retrieve-connect-hint");
  if (!connectButton) {
    return;
  }

  const engineOnline = Boolean(state.runtime) || Boolean(state.daemonStatus?.running);
  connectButton.disabled = !engineOnline;
  connectButton.setAttribute("aria-disabled", String(connectButton.disabled));

  if (connectHint) {
    connectHint.hidden = engineOnline;
  }
}

function renderDesktopState() {
  if (!state.settingsDirty) {
    applySettingsToForm(state);
  }
  applyAgentIdentity(state);
  updateHomeStatus(state, state.daemonStatus, state.runtime);
  syncSlackRetrieveConnectState();
}

function rerenderLanguageSensitiveViews() {
  renderDesktopState();
  renderSkillsState(state);
  renderSchedulesState(state);
  renderRunLogsState(state);
  renderDaemonPlaneState(state);
  const chatThread = byId("chat-thread");
  if (chatThread && chatThread.querySelectorAll(".terminal-entry").length <= 1) {
    clearChatThread(state);
  }
}

async function refreshActiveView() {
  await refreshRuntime();
  if (state.activeView === "overview") {
    await loadUpdaterState();
  }
  if (state.activeView === "chat") {
    await loadDesktopMessages();
  }
  if (state.activeView === "skills") {
    await loadSkills();
  }
  if (state.activeView === "schedules") {
    await loadSchedules();
  }
  if (state.activeView === "runs") {
    await loadRunLogs();
  }
  if (state.activeView === "diagnostics") {
    await loadDaemonPlane();
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

function stopUpdaterPolling() {
  if (updaterPollTimer) {
    window.clearInterval(updaterPollTimer);
    updaterPollTimer = null;
  }
}

function startUpdaterPolling() {
  stopUpdaterPolling();
  if (state.activeView !== "overview") {
    return;
  }

  updaterPollTimer = window.setInterval(() => {
    if (document.visibilityState !== "visible" || state.activeView !== "overview") {
      return;
    }
    loadUpdaterState().catch(() => {});
  }, 1000);
}

function stopRunLogPolling() {
  if (runLogPollTimer) {
    window.clearInterval(runLogPollTimer);
    runLogPollTimer = null;
  }
}

function stopDesktopMessagePolling() {
  if (desktopMessagePollTimer) {
    window.clearInterval(desktopMessagePollTimer);
    desktopMessagePollTimer = null;
  }
}

function startDesktopMessagePolling() {
  stopDesktopMessagePolling();
  if (state.activeView !== "chat") {
    return;
  }

  desktopMessagePollTimer = window.setInterval(() => {
    if (document.visibilityState !== "visible" || state.activeView !== "chat") {
      return;
    }
    loadDesktopMessages().catch(() => {});
  }, 1000);
}

function startRunLogPolling() {
  stopRunLogPolling();
  if (!["runs", "diagnostics"].includes(state.activeView)) {
    return;
  }

  runLogPollTimer = window.setInterval(() => {
    if (document.visibilityState !== "visible" || !["runs", "diagnostics"].includes(state.activeView)) {
      return;
    }
    if (state.activeView === "runs") {
      loadRunLogs().catch(() => {});
      return;
    }
    loadDaemonPlane().catch(() => {});
  }, 1000);
}

function stopSlackRetrieveOauthPolling() {
  if (slackRetrieveOauthPollTimer) {
    window.clearInterval(slackRetrieveOauthPollTimer);
    slackRetrieveOauthPollTimer = null;
    syncSlackRetrieveConnectState();
  }
}

function startSlackRetrieveOauthPolling() {
  stopSlackRetrieveOauthPolling();
  slackRetrieveOauthPollTimer = window.setInterval(async () => {
    try {
      const status = await api.getSlackRetrieveOAuthStatus();
      if (status.status === "pending" || status.status === "idle") {
        return;
      }
      stopSlackRetrieveOauthPolling();
      if (status.status === "success") {
        setSettingsStatus(t("status.slackRetrieveOauthRestarting"));
        setEngineAction({
          action: "restart",
          busy: true,
          message: t("status.slackRetrieveOauthRestarting"),
          tone: "progress",
          visible: true,
        });
        await refreshRuntime();
        const result = await api.restartDaemon();
        setEngineAction({
          action: "restart",
          busy: false,
          message: result.message || t("status.slackRetrieveOauthRestarted"),
          tone: result.success ? "success" : "error",
          visible: true,
        });
        setSettingsStatus(result.message || t("status.slackRetrieveOauthRestarted"));
        await loadConfig();
        await refreshRuntime();
        scheduleEngineActionClear();
        return;
      }

      setSettingsStatus(status.message || "");
      await loadConfig();
      await refreshRuntime();
    } catch (error) {
      stopSlackRetrieveOauthPolling();
      setSettingsStatus(error.message);
    }
  }, 1000);
  syncSlackRetrieveConnectState();
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

async function loadUpdaterState() {
  try {
    state.updater = await api.getUpdaterState();
  } catch {
    state.updater = {
      supported: false,
      status: "unsupported",
      version: state.appMeta?.version || "",
      progress: 0,
      message: "",
    };
  }
  renderDesktopState();
}

async function maybeCheckForUpdatesOnOverview() {
  try {
    if (!state.updater) {
      await loadUpdaterState();
    }

    const status = String(state.updater?.status || "idle");
    if (!state.updater?.supported) {
      return;
    }
    if (["checking", "available", "downloading", "downloaded"].includes(status)) {
      return;
    }

    state.updater = await api.checkForUpdates();
    renderDesktopState();
  } catch {
    await loadUpdaterState();
  }
}

async function loadSkills() {
  try {
    state.skills = await api.getSkills();
    renderSkillsState(state);
  } catch (error) {
    state.skills = { skills: [] };
    setSettingsStatus(t("status.skillLoadFailed", { message: error.message }));
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
  await loadRecentRunLogs();
}

async function loadRecentRunLogs() {
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

async function loadDaemonPlane() {
  try {
    const [resourcesResponse, eventsResponse] = await Promise.all([
      api.getResources(),
      api.getDaemonEvents(50),
    ]);
    state.daemonResources = resourcesResponse.resources || [];
    state.daemonResourceCounts = resourcesResponse.counts || {};
    state.daemonResourceError = "";
    state.daemonEvents = eventsResponse.events || [];
    state.daemonEventFile = eventsResponse.daemon_event_file || "";
    state.daemonEventError = "";
    renderDaemonPlaneState(state);
  } catch (error) {
    state.daemonResources = [];
    state.daemonResourceCounts = {};
    state.daemonResourceError = error.message;
    state.daemonEvents = [];
    state.daemonEventFile = "";
    state.daemonEventError = error.message;
    renderDaemonPlaneState(state);
  }
}

async function loadDesktopMessages() {
  try {
    const response = await api.getDesktopMessages(DEFAULT_CHAT_SESSION_ID);
    appendDesktopMessages(state, response.messages || []);
  } catch {
    // Ignore transient desktop inbox errors so Talk remains usable.
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
  setSettingsStatus(t("status.savingSettings"));

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
        message: t("status.restartingWithNewSettings"),
        tone: "progress",
        visible: true,
      });
      await refreshRuntime();
      const result = await api.restartDaemon();
      setEngineAction({
        action: "restart",
        busy: false,
        message: result.success ? t("status.engineRestartedWithNewSettings") : (result.message || t("status.engineRestartFailed")),
        tone: result.success ? "success" : "error",
        visible: true,
      });
      setSettingsStatus(result.success ? t("status.settingsSavedAndRestarted") : (result.message || t("status.settingsSavedButRestartFailed")));
      scheduleEngineActionClear();
    } else {
      setSettingsStatus(t("status.settingsSavedToConfig"));
    }

    await refreshRuntime();
  } catch (error) {
    setSettingsStatus(t("status.saveFailed", { message: error.message }));
  }
}

async function runDaemonAction(action) {
  setSettingsStatus(t("status.actionProgress", { action: progressLabelForAction(action) }));
  setEngineAction({
    action,
    busy: true,
    message: t("status.actionProgress", { action: progressLabelForAction(action) }),
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
      message: result.message || t("status.actionCompleted", { action }),
      tone: result.success ? "success" : "error",
      visible: true,
    });
    setSettingsStatus(result.message || t("status.actionCompleted", { action }));
    await refreshRuntime();
    scheduleEngineActionClear();
  } catch (error) {
    setEngineAction({
      action,
      busy: false,
      message: t("status.actionFailed", { action, message: error.message }),
      tone: "error",
      visible: true,
    });
    setSettingsStatus(t("status.actionFailed", { action, message: error.message }));
    await refreshRuntime();
    scheduleEngineActionClear();
  }
}

function progressLabelForAction(action) {
  const labels = {
    start: t("status.start"),
    restart: t("status.restart"),
    stop: t("status.stop"),
  };
  return labels[action] || t("status.updating");
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
      if (viewName === "diagnostics") {
        loadDaemonPlane().catch(() => {});
      }
      if (viewName === "chat") {
        loadDesktopMessages().catch(() => {});
      }
      if (viewName === "runs" || viewName === "diagnostics") {
        startRunLogPolling();
      } else {
        stopRunLogPolling();
      }
      if (viewName === "chat") {
        startDesktopMessagePolling();
      } else {
        stopDesktopMessagePolling();
      }
      if (viewName === "overview") {
        startUpdaterPolling();
      } else {
        stopUpdaterPolling();
      }
      refreshRuntime().catch(() => {});
      if (viewName === "overview") {
        maybeCheckForUpdatesOnOverview().catch(() => {});
      }
    },
  });
  bindHomeActions({
    onStart: () => runDaemonAction("start"),
    onRestart: () => runDaemonAction("restart"),
    onStop: () => runDaemonAction("stop"),
    onUpdaterAction: async () => {
      try {
        const updater = state.updater || {};
        const status = String(updater.status || "idle");
        if (status === "available") {
          await api.downloadUpdate();
        } else if (status === "downloaded") {
          await api.installUpdate();
        } else if (status === "checking" || status === "downloading") {
          return;
        } else {
          await api.checkForUpdates();
        }
      } catch (error) {
        setSettingsStatus(error.message);
      } finally {
        await loadUpdaterState();
      }
    },
  });
  bindSettingsActions({
    state,
    onReload: loadConfig,
    onSave: () => saveSettings({ restart: false }),
    onSaveAndRestart: () => saveSettings({ restart: true }),
  });
  document.getElementById("open-browser-profile-setup")?.addEventListener("click", async () => {
    setSettingsStatus(t("status.openingChromeProfileSetup"));
    try {
      const result = await api.openChromeProfileSetup();
      setSettingsStatus(result.message || t("status.chromeProfileSetupOpened"));
    } catch (error) {
      setSettingsStatus(t("status.profileSetupFailed", { message: error.message }));
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
      setSettingsStatus(t("status.filesystemBaseDirEmpty"));
      return;
    }

    setSettingsStatus(t("status.openingFilesystemBaseDir"));
    try {
      const result = await api.openFilesystemBaseDir(targetPath);
      setSettingsStatus(result.message || t("status.filesystemBaseDirOpened"));
    } catch (error) {
      setSettingsStatus(t("status.openFolderFailed", { message: error.message }));
    }
  });
  document.getElementById("connect-slack-retrieve")?.addEventListener("click", async () => {
    try {
      const engineOnline = Boolean(state.runtime) || Boolean(state.daemonStatus?.running);
      if (!engineOnline) {
        setSettingsStatus(t("status.slackRetrieveStartEngineFirst"));
        syncSlackRetrieveConnectState();
        return;
      }
      const updates = collectSettingsUpdates(state);
      const clientId = String(updates.SLACK_RETRIEVE_CLIENT_ID || state.config.SLACK_RETRIEVE_CLIENT_ID || "").trim();
      const clientSecret = String(updates.SLACK_RETRIEVE_CLIENT_SECRET || state.config.SLACK_RETRIEVE_CLIENT_SECRET || "").trim();
      const redirectUri = String(updates.SLACK_RETRIEVE_REDIRECT_URL || state.config.SLACK_RETRIEVE_REDIRECT_URL || "").trim();
      if (!clientId || !clientSecret) {
        setSettingsStatus(t("status.slackRetrieveClientCredentialsRequired"));
        return;
      }
      await api.saveConfig(updates);
      state.config = { ...state.config, ...updates };
      state.settingsDirty = false;
      const result = await api.startSlackRetrieveOAuth({
        client_id: clientId,
        client_secret: clientSecret,
        redirect_uri: redirectUri,
      });
      await api.openExternal(result.authorization_url);
      setSettingsStatus(result.message || t("status.slackRetrieveOauthStarted"));
      startSlackRetrieveOauthPolling();
    } catch (error) {
      setSettingsStatus(error.message);
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
        setSettingsStatus(t("status.skillFolderNotConfigured"));
        return;
      }
      setSettingsStatus(t("status.openingSkillFolder"));
      try {
        const result = await api.openPath(targetPath);
        setSettingsStatus(result.message || t("status.skillFolderOpened"));
      } catch (error) {
        setSettingsStatus(t("status.openFolderFailed", { message: error.message }));
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
        setSettingsStatus(t("status.runLogFileNotConfigured"));
        return;
      }
      setSettingsStatus(t("status.openingRunLogFile"));
      try {
        const result = await api.openPath(targetPath);
        setSettingsStatus(result.message || t("status.runLogFileOpened"));
      } catch (error) {
        setSettingsStatus(t("status.openFolderFailed", { message: error.message }));
      }
    },
  });
  bindDaemonPlaneActions({
    state,
    onReload: loadDaemonPlane,
    onOpenPath: async (targetPath) => {
      if (!targetPath) {
        setSettingsStatus(t("status.daemonEventFileNotConfigured"));
        return;
      }
      setSettingsStatus(t("status.openingDaemonEventFile"));
      try {
        const result = await api.openPath(targetPath);
        setSettingsStatus(result.message || t("status.daemonEventFileOpened"));
      } catch (error) {
        setSettingsStatus(t("status.openFolderFailed", { message: error.message }));
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
  state.language = initI18n({
    onChange: (language) => {
      state.language = language;
      rerenderLanguageSensitiveViews();
    },
  });
  state.theme = initTheme({
    onChange: (theme) => {
      state.theme = theme;
    },
  });
  initializePasswordToggles();
  bindActions();
  await loadAppMeta();
  await loadConfig();
  await loadUpdaterState();
  await maybeCheckForUpdatesOnOverview();
  await refreshActiveView();
  await loadRunLogs();
  await loadDaemonPlane();
  startUpdaterPolling();
  startRunLogPolling();
  startDesktopMessagePolling();
});
