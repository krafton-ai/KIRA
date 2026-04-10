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
let runtimeEventSource = null;
let runtimeEventRefreshTimer = null;
let runLogEventSource = null;
let desktopMessageEventSource = null;
let runtimeEventReconnectTimer = null;
let runLogEventReconnectTimer = null;
let desktopMessageEventReconnectTimer = null;
let updaterStateLoading = false;
let runLogsLoading = false;
let daemonPlaneLoading = false;
let desktopMessagesLoading = false;

function isEngineOnline() {
  return Boolean(state.runtime) || Boolean(state.daemonStatus?.running);
}

function syncSlackRetrieveConnectState() {
  const connectButton = byId("connect-slack-retrieve");
  const connectHint = byId("slack-retrieve-connect-hint");
  if (!connectButton) {
    return;
  }

  const engineOnline = isEngineOnline();
  connectButton.disabled = !engineOnline;
  connectButton.setAttribute("aria-disabled", String(connectButton.disabled));

  if (connectHint) {
    connectHint.hidden = engineOnline;
  }
}

function responseTraceEnabled() {
  const configured = state.config.RESPONSE_TRACE_ENABLED;
  if (configured !== undefined && configured !== null && String(configured).trim() !== "") {
    return String(configured).trim().toLowerCase() === "true";
  }
  return Boolean(state.runtime?.response_trace_enabled);
}

function renderResponseTraceControl() {
  const enabled = responseTraceEnabled();
  const input = byId("RESPONSE_TRACE_ENABLED");
  const chip = byId("response-trace-chip");
  if (input) {
    input.checked = enabled;
  }
  if (chip) {
    chip.className = `status-chip ${enabled ? "online" : "offline"}`;
    setText(chip, enabled ? t("common.on") : t("common.off"));
  }
}

function fullDiskAccessView(status) {
  if (status === "granted") {
    return {
      className: "status-chip online",
      label: t("settings.fullDiskAccessGranted"),
    };
  }
  if (status === "not_granted") {
    return {
      className: "status-chip offline",
      label: t("settings.fullDiskAccessNotGranted"),
    };
  }
  if (status === "unsupported") {
    return {
      className: "status-chip info",
      label: t("settings.fullDiskAccessUnsupported"),
    };
  }
  return {
    className: "status-chip info",
    label: t("settings.fullDiskAccessUnknown"),
  };
}

function screenRecordingAccessView(status) {
  if (status === "granted") {
    return {
      className: "status-chip online",
      label: t("settings.screenRecordingGranted"),
    };
  }
  if (status === "not_granted") {
    return {
      className: "status-chip offline",
      label: t("settings.screenRecordingNotGranted"),
    };
  }
  if (status === "unsupported") {
    return {
      className: "status-chip info",
      label: t("settings.screenRecordingUnsupported"),
    };
  }
  return {
    className: "status-chip info",
    label: t("settings.screenRecordingUnknown"),
  };
}

function renderFullDiskAccessStatus() {
  const section = byId("full-disk-access-section");
  const panel = byId("full-disk-access-panel");
  const chip = byId("full-disk-access-chip");
  const openButton = byId("open-full-disk-access-settings");
  const relaunchButton = byId("relaunch-app");
  if (!section || !panel || !chip) {
    return;
  }

  if (!state.fullDiskAccess) {
    section.hidden = true;
    chip.className = "status-chip info";
    setText(chip, t("common.checking"));
    if (openButton) {
      openButton.disabled = false;
    }
    if (relaunchButton) {
      relaunchButton.disabled = false;
    }
    return;
  }

  section.hidden = !Boolean(state.fullDiskAccess.supported);
  const view = fullDiskAccessView(String(state.fullDiskAccess.status || "unknown"));
  chip.className = view.className;
  setText(chip, view.label);
  const supported = Boolean(state.fullDiskAccess.supported);
  if (openButton) {
    openButton.disabled = !supported;
  }
  if (relaunchButton) {
    relaunchButton.disabled = !supported;
  }
}

function renderScreenRecordingStatus() {
  const section = byId("screen-recording-section");
  const chip = byId("screen-recording-chip");
  const openButton = byId("open-screen-recording-settings");
  const relaunchButton = byId("relaunch-app-screen-recording");
  if (!section || !chip) {
    return;
  }

  if (!state.screenRecordingAccess) {
    section.hidden = true;
    chip.className = "status-chip info";
    setText(chip, t("common.checking"));
    if (openButton) {
      openButton.disabled = false;
    }
    if (relaunchButton) {
      relaunchButton.disabled = false;
    }
    return;
  }

  section.hidden = !Boolean(state.screenRecordingAccess.supported);
  const view = screenRecordingAccessView(String(state.screenRecordingAccess.status || "unknown"));
  chip.className = view.className;
  setText(chip, view.label);
  const supported = Boolean(state.screenRecordingAccess.supported);
  if (openButton) {
    openButton.disabled = !supported;
  }
  if (relaunchButton) {
    relaunchButton.disabled = !supported;
  }
}

function renderDesktopState() {
  if (!state.settingsDirty) {
    applySettingsToForm(state);
  }
  applyAgentIdentity(state);
  updateHomeStatus(state, state.daemonStatus, state.runtime);
  syncSlackRetrieveConnectState();
  renderResponseTraceControl();
  renderFullDiskAccessStatus();
  renderScreenRecordingStatus();
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

function authServiceLabel(service) {
  if (service === "slack-retrieve") {
    return t("mcp.slackRetrieveTitle");
  }
  if (service === "ms365") {
    return "Microsoft 365";
  }
  if (service === "atlassian") {
    return "Atlassian";
  }
  return service;
}

function authResetOptions(service) {
  if (service !== "atlassian") {
    return {};
  }
  return {
    confluenceSiteUrl: state.config.ATLASSIAN_CONFLUENCE_SITE_URL || "",
    jiraSiteUrl: state.config.ATLASSIAN_JIRA_SITE_URL || "",
  };
}

async function resetAuthState(service) {
  const serviceLabel = authServiceLabel(service);
  setSettingsStatus(t("status.resettingLogin", { service: serviceLabel }));

  try {
    const result = await api.resetAuthState(service, authResetOptions(service));
    await loadConfig();

    const note = result.hasSystemCacheNote ? t("status.ms365SystemCacheNote") : "";

    setEngineAction({
      action: "restart",
      busy: true,
      message: t("status.loginResetBannerRestarting"),
      tone: "progress",
      visible: true,
    });
    setSettingsStatus(t("status.loginResetRestarting", { service: serviceLabel }));
    await refreshRuntime();

    const restartResult = await api.restartDaemon();
    const restartMessage = restartResult.success
      ? t("status.loginResetRestarted", { service: serviceLabel })
      : t("status.loginResetRestartFailed", { service: serviceLabel });
    const restartBannerMessage = restartResult.success
      ? t("status.loginResetBannerRestarted")
      : t("status.loginResetBannerRestartFailed");
    const finalStatusMessage = restartResult.message || restartMessage;

    setEngineAction({
      action: "restart",
      busy: false,
      message: restartBannerMessage,
      tone: restartResult.success ? "success" : "error",
      visible: true,
    });
    setSettingsStatus(
      note
        ? `${finalStatusMessage} ${note}`
        : finalStatusMessage,
    );
    await refreshRuntime();
    scheduleEngineActionClear();
  } catch (error) {
    setSettingsStatus(t("status.loginResetFailed", { service: serviceLabel, message: error.message }));
  }
}

function setResponseTraceStatus(message) {
  setText(byId("response-trace-status"), message);
}

async function refreshActiveView() {
  await refreshRuntime();
  if (state.activeView === "settings") {
    await loadFullDiskAccessStatus();
    await loadScreenRecordingAccessStatus();
  }
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

function clearRuntimeEventRefreshTimer() {
  if (runtimeEventRefreshTimer) {
    window.clearTimeout(runtimeEventRefreshTimer);
    runtimeEventRefreshTimer = null;
  }
}

function clearRuntimeEventReconnectTimer() {
  if (runtimeEventReconnectTimer) {
    window.clearTimeout(runtimeEventReconnectTimer);
    runtimeEventReconnectTimer = null;
  }
}

function clearRunLogEventReconnectTimer() {
  if (runLogEventReconnectTimer) {
    window.clearTimeout(runLogEventReconnectTimer);
    runLogEventReconnectTimer = null;
  }
}

function clearDesktopMessageEventReconnectTimer() {
  if (desktopMessageEventReconnectTimer) {
    window.clearTimeout(desktopMessageEventReconnectTimer);
    desktopMessageEventReconnectTimer = null;
  }
}

function stopRuntimeEventStream() {
  clearRuntimeEventRefreshTimer();
  clearRuntimeEventReconnectTimer();
  if (runtimeEventSource) {
    runtimeEventSource.close();
    runtimeEventSource = null;
  }
}

function scheduleRuntimeEventRefresh() {
  clearRuntimeEventRefreshTimer();
  runtimeEventRefreshTimer = window.setTimeout(async () => {
    runtimeEventRefreshTimer = null;
    if (document.visibilityState !== "visible") {
      return;
    }
    await refreshRuntime();
    if (state.activeView === "diagnostics") {
      await loadDaemonPlane();
      return;
    }
    if (state.activeView === "runs") {
      await loadRunLogs();
    }
  }, 150);
}

function startRuntimeEventStream() {
  stopRuntimeEventStream();
  const baseUrl = api.getDaemonBaseUrl?.();
  if (!baseUrl) {
    return;
  }
  runtimeEventSource = new EventSource(`${baseUrl}/v1/runtime/events`);
  runtimeEventSource.addEventListener("runtime", () => {
    scheduleRuntimeEventRefresh();
  });
  runtimeEventSource.onerror = () => {
    if (document.visibilityState !== "visible") {
      stopRuntimeEventStream();
      return;
    }
    if (!runtimeEventReconnectTimer) {
      runtimeEventReconnectTimer = window.setTimeout(() => {
        runtimeEventReconnectTimer = null;
        startRuntimeEventStream();
      }, 2000);
    }
  };
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

function stopRunLogEventStream() {
  clearRunLogEventReconnectTimer();
  if (runLogEventSource) {
    runLogEventSource.close();
    runLogEventSource = null;
  }
}

function startRunLogEventStream() {
  stopRunLogEventStream();
  if (state.activeView !== "runs") {
    return;
  }
  const baseUrl = api.getDaemonBaseUrl?.();
  if (!baseUrl) {
    return;
  }
  runLogEventSource = new EventSource(`${baseUrl}/v1/run-logs/events`);
  runLogEventSource.addEventListener("runs", () => {
    if (document.visibilityState !== "visible" || state.activeView !== "runs") {
      return;
    }
    loadRunLogs().catch(() => {});
  });
  runLogEventSource.onerror = () => {
    if (document.visibilityState !== "visible" || state.activeView !== "runs") {
      stopRunLogEventStream();
      return;
    }
    if (!runLogEventReconnectTimer) {
      runLogEventReconnectTimer = window.setTimeout(() => {
        runLogEventReconnectTimer = null;
        startRunLogEventStream();
      }, 2000);
    }
  };
}

function stopDesktopMessagePolling() {
  if (desktopMessagePollTimer) {
    window.clearInterval(desktopMessagePollTimer);
    desktopMessagePollTimer = null;
  }
}

function stopDesktopMessageEventStream() {
  clearDesktopMessageEventReconnectTimer();
  if (desktopMessageEventSource) {
    desktopMessageEventSource.close();
    desktopMessageEventSource = null;
  }
}

function startDesktopMessageEventStream() {
  stopDesktopMessageEventStream();
  if (state.activeView !== "chat") {
    return;
  }
  const baseUrl = api.getDaemonBaseUrl?.();
  if (!baseUrl) {
    return;
  }
  const query = new URLSearchParams({ session_id: DEFAULT_CHAT_SESSION_ID });
  desktopMessageEventSource = new EventSource(`${baseUrl}/v1/desktop-messages/events?${query.toString()}`);
  desktopMessageEventSource.addEventListener("desktop", () => {
    if (document.visibilityState !== "visible" || state.activeView !== "chat") {
      return;
    }
    loadDesktopMessages().catch(() => {});
  });
  desktopMessageEventSource.onerror = () => {
    if (document.visibilityState !== "visible" || state.activeView !== "chat") {
      stopDesktopMessageEventStream();
      return;
    }
    if (!desktopMessageEventReconnectTimer) {
      desktopMessageEventReconnectTimer = window.setTimeout(() => {
        desktopMessageEventReconnectTimer = null;
        startDesktopMessageEventStream();
      }, 2000);
    }
  };
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
  }, 5000);
}

function startRunLogPolling() {
  stopRunLogPolling();
  if (state.activeView !== "runs") {
    return;
  }

  runLogPollTimer = window.setInterval(() => {
    if (document.visibilityState !== "visible" || state.activeView !== "runs") {
      return;
    }
    loadRunLogs().catch(() => {});
  }, 5000);
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

async function loadFullDiskAccessStatus() {
  try {
    state.fullDiskAccess = await api.getFullDiskAccessStatus();
  } catch {
    state.fullDiskAccess = {
      supported: true,
      status: "unknown",
    };
  }
  renderDesktopState();
}

async function loadScreenRecordingAccessStatus() {
  try {
    state.screenRecordingAccess = await api.getScreenRecordingAccessStatus();
  } catch {
    state.screenRecordingAccess = {
      supported: true,
      status: "unknown",
    };
  }
  renderDesktopState();
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
  if (updaterStateLoading) {
    return;
  }
  updaterStateLoading = true;
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
  } finally {
    updaterStateLoading = false;
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
  if (runLogsLoading) {
    return;
  }
  runLogsLoading = true;
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
  } finally {
    runLogsLoading = false;
    renderRunLogsState(state);
  }
}

async function loadDaemonPlane() {
  if (daemonPlaneLoading) {
    return;
  }
  daemonPlaneLoading = true;
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
  } finally {
    daemonPlaneLoading = false;
    renderDaemonPlaneState(state);
  }
}

async function loadDesktopMessages() {
  if (desktopMessagesLoading) {
    return;
  }
  desktopMessagesLoading = true;
  try {
    const response = await api.getDesktopMessages(DEFAULT_CHAT_SESSION_ID);
    appendDesktopMessages(state, response.messages || []);
  } catch {
    // Ignore transient desktop inbox errors so Talk remains usable.
  } finally {
    desktopMessagesLoading = false;
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

async function saveResponseTraceSetting(enabled) {
  const value = String(Boolean(enabled));
  setResponseTraceStatus(t("diagnostics.responseTraceSaving"));

  try {
    await api.saveConfig({ RESPONSE_TRACE_ENABLED: value });
    state.config = { ...state.config, RESPONSE_TRACE_ENABLED: value };
    state.settingsDirty = false;

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
    await refreshRuntime();
    renderResponseTraceControl();
    setResponseTraceStatus(
      result.success
        ? (enabled ? t("diagnostics.responseTraceEnabledStatus") : t("diagnostics.responseTraceDisabledStatus"))
        : (result.message || t("status.engineRestartFailed")),
    );
    scheduleEngineActionClear();
  } catch (error) {
    await loadConfig();
    await refreshRuntime();
    setResponseTraceStatus(t("status.saveFailed", { message: error.message }));
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
      if (viewName === "settings") {
        loadFullDiskAccessStatus().catch(() => {});
        loadScreenRecordingAccessStatus().catch(() => {});
      }
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
      if (viewName === "runs") {
        startRunLogEventStream();
      } else {
        stopRunLogEventStream();
      }
      if (viewName === "chat") {
        startDesktopMessagePolling();
        startDesktopMessageEventStream();
      } else {
        stopDesktopMessagePolling();
        stopDesktopMessageEventStream();
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
  document.getElementById("open-full-disk-access-settings")?.addEventListener("click", async () => {
    setSettingsStatus(t("status.openingFullDiskAccessSettings"));
    try {
      await api.openFullDiskAccessSettings();
      setSettingsStatus(t("status.fullDiskAccessSettingsOpened"));
    } catch (error) {
      setSettingsStatus(t("status.fullDiskAccessSettingsFailed", { message: error.message }));
    }
  });
  document.getElementById("relaunch-app")?.addEventListener("click", async () => {
    setSettingsStatus(t("status.relaunchingApp"));
    await api.relaunchApp();
  });
  document.getElementById("open-screen-recording-settings")?.addEventListener("click", async () => {
    setSettingsStatus(t("status.openingScreenRecordingSettings"));
    try {
      await api.openScreenRecordingSettings();
      setSettingsStatus(t("status.screenRecordingSettingsOpened"));
    } catch (error) {
      setSettingsStatus(t("status.screenRecordingSettingsFailed", { message: error.message }));
    }
  });
  document.getElementById("relaunch-app-screen-recording")?.addEventListener("click", async () => {
    setSettingsStatus(t("status.relaunchingApp"));
    await api.relaunchApp();
  });
  document.getElementById("connect-slack-retrieve")?.addEventListener("click", async () => {
    try {
      const engineOnline = isEngineOnline();
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
  document.getElementById("reset-slack-retrieve-auth")?.addEventListener("click", () => {
    resetAuthState("slack-retrieve").catch(() => {});
  });
  document.getElementById("reset-ms365-auth")?.addEventListener("click", () => {
    resetAuthState("ms365").catch(() => {});
  });
  document.getElementById("reset-atlassian-auth")?.addEventListener("click", () => {
    resetAuthState("atlassian").catch(() => {});
  });
  document.getElementById("RESPONSE_TRACE_ENABLED")?.addEventListener("change", (event) => {
    const enabled = Boolean(event.target?.checked);
    saveResponseTraceSetting(enabled).catch(() => {});
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
    startRuntimeEventStream();
    startRunLogEventStream();
    startDesktopMessageEventStream();
    refreshActiveView().catch(() => {});
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      startRuntimeEventStream();
      startRunLogEventStream();
      startDesktopMessageEventStream();
      refreshActiveView().catch(() => {});
      return;
    }
    stopRuntimeEventStream();
    stopRunLogEventStream();
    stopDesktopMessageEventStream();
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
  startRuntimeEventStream();
  startRunLogEventStream();
  startDesktopMessageEventStream();
  startUpdaterPolling();
  startRunLogPolling();
  startDesktopMessagePolling();
});
