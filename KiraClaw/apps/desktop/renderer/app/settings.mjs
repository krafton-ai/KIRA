import { BOOLEAN_FIELDS, EXTERNAL_MCP_CONFIG_FIELDS, EXTERNAL_MCP_SERVER_NAMES, PROVIDER_DEFAULT_MODELS, SETTINGS_FIELDS, SELECT_DEFAULTS } from "./constants.mjs";
import { byId, escapeHtml, setText } from "./dom.mjs";
import { t } from "./i18n.mjs";

function normalizeBoolean(value) {
  return String(value ?? "").trim().toLowerCase() === "true";
}

function parseRemoteMcpServers(raw) {
  if (!String(raw ?? "").trim()) {
    return [];
  }
  try {
    const payload = JSON.parse(raw);
    if (!Array.isArray(payload)) {
      return [];
    }
    return payload
      .filter((item) => item && typeof item === "object")
      .map((item) => ({
        name: String(item.name || "").trim().toLowerCase(),
        url: String(item.url || "").trim(),
      }))
      .filter((item) => item.name || item.url);
  } catch {
    return [];
  }
}

function renderRemoteMcpServers(servers) {
  const list = byId("remote-mcp-list");
  if (!list) {
    return;
  }

  if (!servers.length) {
    list.innerHTML = `
      <article class="remote-mcp-card remote-mcp-card-empty">
        <p class="section-copy">${escapeHtml(t("mcp.noRemoteServers"))}</p>
      </article>
    `;
    return;
  }

  list.innerHTML = servers.map((server, index) => `
    <article class="remote-mcp-card" data-remote-mcp-index="${index}">
      <div class="form-grid remote-mcp-grid">
        <label class="field">
          <span>${escapeHtml(t("common.name"))}</span>
          <input data-remote-mcp-input="name" value="${escapeHtml(server.name)}" placeholder="myserver" />
        </label>
        <label class="field">
          <span>${escapeHtml(t("common.url"))}</span>
          <input data-remote-mcp-input="url" value="${escapeHtml(server.url)}" placeholder="https://example.com/mcp" />
        </label>
      </div>
      <div class="button-row remote-mcp-actions">
        <button type="button" class="danger-button" data-remote-mcp-delete="${index}">${escapeHtml(t("common.delete"))}</button>
      </div>
    </article>
  `).join("");
}

function collectRemoteMcpServers() {
  const cards = Array.from(document.querySelectorAll("[data-remote-mcp-index]"));
  return cards.map((card) => {
    const get = (name) => card.querySelector(`[data-remote-mcp-input="${name}"]`);
    return {
      name: String(get("name")?.value || "").trim().toLowerCase(),
      url: String(get("url")?.value || "").trim(),
    };
  });
}

function validateRemoteMcpServers(servers) {
  const seen = new Set();
  for (const server of servers) {
    const touched = server.name || server.url;
    if (!touched) {
      continue;
    }
    if (!server.name) {
      throw new Error(t("mcp.customNameRequired"));
    }
    if (!/^[a-z0-9-]+$/.test(server.name)) {
      throw new Error(t("mcp.customNamePattern"));
    }
    if (!server.url) {
      throw new Error(t("mcp.customUrlRequired", { name: server.name }));
    }
    if (seen.has(server.name)) {
      throw new Error(t("mcp.customNameDuplicated", { name: server.name }));
    }
    seen.add(server.name);
  }
}

function serializeRemoteMcpServers(servers) {
  const rows = servers.filter((server) => server.name && server.url).map((server) => ({
    name: server.name,
    url: server.url,
  }));
  return rows.length ? JSON.stringify(rows) : "";
}

function runtimeValueForField(state, field) {
  if (!state.runtime) {
    return "";
  }

  const runtimeMap = {
    KIRACLAW_AGENT_NAME: state.runtime.agent_name,
    KIRACLAW_AGENT_PERSONA: state.runtime.agent_persona,
    KIRACLAW_PROVIDER: state.runtime.provider,
    KIRACLAW_MODEL: state.runtime.model,
    SLACK_ENABLED: String(Boolean(state.runtime.slack_enabled)),
    SLACK_TEAM_ID: state.runtime.slack_identity && state.runtime.slack_identity.team_id,
    SLACK_ALLOWED_NAMES: state.runtime.slack_allowed_names,
    TELEGRAM_ENABLED: String(Boolean(state.runtime.telegram_enabled)),
    TELEGRAM_ALLOWED_NAMES: state.runtime.telegram_allowed_names,
    DISCORD_ENABLED: String(Boolean(state.runtime.discord_enabled)),
    DISCORD_ALLOWED_NAMES: state.runtime.discord_allowed_names,
    SLACK_RETRIEVE_ENABLED: String(Boolean(state.runtime.slack_retrieve_enabled)),
    SLACK_RETRIEVE_REDIRECT_URL: state.runtime.slack_retrieve_redirect_uri,
    CHROME_ENABLED: String(Boolean(state.runtime.browser_enabled)),
    FILESYSTEM_BASE_DIR: state.runtime.workspace_dir,
  };

  return runtimeMap[field] ?? "";
}

function effectiveFieldValue(state, field) {
  const configured = state.config[field];
  if (configured !== undefined && configured !== null && String(configured).trim() !== "") {
    return String(configured);
  }

  const runtimeValue = runtimeValueForField(state, field);
  if (runtimeValue !== undefined && runtimeValue !== null && String(runtimeValue).trim() !== "") {
    return String(runtimeValue);
  }

  return SELECT_DEFAULTS[field] || "";
}

export function syncProviderFields() {
  const providerInput = byId("KIRACLAW_PROVIDER");
  const provider = providerInput ? providerInput.value : SELECT_DEFAULTS.KIRACLAW_PROVIDER;
  const previousProvider = providerInput?.dataset.lastProvider || "";

  for (const element of document.querySelectorAll("[data-provider]")) {
    const matches = element.dataset.provider === provider;
    element.hidden = !matches;
  }

  const modelInput = byId("KIRACLAW_MODEL");
  if (modelInput) {
    const currentValue = modelInput.value.trim();
    const previousDefault = PROVIDER_DEFAULT_MODELS[previousProvider] || "";
    const nextDefault = PROVIDER_DEFAULT_MODELS[provider] || "";

    if (!currentValue || (previousDefault && currentValue === previousDefault)) {
      modelInput.value = nextDefault;
    }
    modelInput.placeholder = nextDefault || "claude-opus-4-6 or gpt-5.2";
  }

  if (providerInput) {
    providerInput.dataset.lastProvider = provider;
  }
}

function syncExternalMcpFields() {
  for (const element of document.querySelectorAll("[data-external-mcp-fields]")) {
    const field = element.dataset.externalMcpFields;
    const input = byId(field);
    const enabled = input ? input.checked : false;
    element.hidden = !enabled;
  }
}

function hasConfiguredValue(state, field) {
  return Boolean(String(state.config[field] ?? "").trim());
}

function syncChannelCards(state) {
  const slackInput = byId("SLACK_ENABLED");
  const telegramInput = byId("TELEGRAM_ENABLED");
  const discordInput = byId("DISCORD_ENABLED");
  const slackActive = slackInput ? slackInput.checked : normalizeBoolean(effectiveFieldValue(state, "SLACK_ENABLED"));
  const telegramActive = telegramInput ? telegramInput.checked : normalizeBoolean(effectiveFieldValue(state, "TELEGRAM_ENABLED"));
  const discordActive = discordInput ? discordInput.checked : normalizeBoolean(effectiveFieldValue(state, "DISCORD_ENABLED"));

  const channelStates = [
    ["slack", slackActive],
    ["telegram", telegramActive],
    ["discord", discordActive],
  ];
  for (const [name, active] of channelStates) {
    const card = byId(`channel-card-${name}`);
    const toggleId = name === "slack" ? "SLACK_ENABLED" : name === "telegram" ? "TELEGRAM_ENABLED" : "DISCORD_ENABLED";
    const toggle = byId(toggleId);
    if (card) {
      card.classList.toggle("active", active);
    }
    if (toggle) {
      toggle.checked = active;
    }
  }

  const count = channelStates.filter(([, active]) => active).length;
  setText(byId("channel-available-count"), t("common.activeCount", { count }));

  const slackFields = byId("slack-channel-fields");
  const telegramFields = byId("telegram-channel-fields");
  const discordFields = byId("discord-channel-fields");
  if (slackFields) {
    slackFields.disabled = !slackActive;
  }
  if (telegramFields) {
    telegramFields.disabled = !telegramActive;
  }
  if (discordFields) {
    discordFields.disabled = !discordActive;
  }
}

export function applySettingsToForm(state) {
  for (const field of SETTINGS_FIELDS) {
    const input = byId(field);
    if (!input) {
      continue;
    }

    const value = effectiveFieldValue(state, field);
    if (input.type === "checkbox") {
      input.checked = normalizeBoolean(value);
      continue;
    }

    if (input.tagName === "SELECT") {
      const hasOption = Array.from(input.options).some((option) => option.value === value);
      input.value = hasOption ? value : (SELECT_DEFAULTS[field] || input.options[0]?.value || "");
      continue;
    }

    input.value = value;
  }

  state.settingsDirty = false;
  syncProviderFields();
  renderRemoteMcpServers(parseRemoteMcpServers(state.config.REMOTE_MCP_SERVERS));
  syncMcpView(state);
  syncExternalMcpFields();
  syncChannelCards(state);
}

export function collectSettingsUpdates(state) {
  const updates = {};

  for (const field of SETTINGS_FIELDS) {
    const input = byId(field);
    if (!input) {
      continue;
    }

    if (input.type === "checkbox") {
      updates[field] = String(input.checked);
      continue;
    }

    const raw = input.value.trim();
    if (!raw && !(field in state.config)) {
      continue;
    }
    updates[field] = raw;
  }

  const remoteServers = collectRemoteMcpServers();
  validateRemoteMcpServers(remoteServers);
  updates.REMOTE_MCP_SERVERS = serializeRemoteMcpServers(remoteServers);

  return updates;
}

export function setSettingsStatus(message) {
  setText(byId("settings-status"), message);
  setText(byId("channel-status"), message);
  setText(byId("mcp-status"), message);
}

function syncMcpView(state) {
  const runtime = state.runtime;
  const customConfiguredNames = parseRemoteMcpServers(state.config.REMOTE_MCP_SERVERS).map((server) => server.name);
  const configuredExternal = EXTERNAL_MCP_SERVER_NAMES.filter((name) => {
    const fieldName = EXTERNAL_MCP_CONFIG_FIELDS[name];
    return normalizeBoolean(state.config[fieldName]);
  });
  const configuredNames = [...configuredExternal, ...customConfiguredNames];

  if (!runtime) {
    if (configuredNames.length > 0) {
      setText(byId("mcp-status"), t("mcp.enabledInConfig", { names: configuredNames.join(", ") }));
      return;
    }
    setText(byId("mcp-status"), t("mcp.settingsReadFrom"));
    return;
  }

  const configuredSet = new Set(configuredNames);
  const externalLoaded = (runtime.mcp_loaded_servers || []).filter((name) => configuredSet.has(name) || EXTERNAL_MCP_SERVER_NAMES.includes(name));
  const externalFailed = (runtime.mcp_failed_servers || []).filter((name) => configuredSet.has(name) || EXTERNAL_MCP_SERVER_NAMES.includes(name));
  if (externalLoaded.length > 0) {
    const parts = [t("mcp.loadedNow", { names: externalLoaded.join(", ") })];
    if (externalFailed.length > 0) {
      parts.push(t("mcp.failed", { names: externalFailed.join(", ") }));
    } else if (configuredNames.length > externalLoaded.length) {
      const pending = configuredNames.filter((name) => !externalLoaded.includes(name));
      if (pending.length > 0) {
        parts.push(t("mcp.enabledInConfig", { names: pending.join(", ") }));
      }
    }
    setText(byId("mcp-status"), parts.join(" · "));
    return;
  }

  if (runtime.mcp_last_error) {
    setText(byId("mcp-status"), runtime.mcp_last_error);
    return;
  }

  if (externalFailed.length > 0) {
    setText(byId("mcp-status"), t("mcp.failed", { names: externalFailed.join(", ") }));
    return;
  }

  if (configuredNames.length > 0) {
    setText(byId("mcp-status"), t("mcp.enabledInConfig", { names: configuredNames.join(", ") }));
    return;
  }

  setText(byId("mcp-status"), t("mcp.noOptionalLoaded"));
}

function markSettingsDirty(state) {
  state.settingsDirty = true;
}

export function bindSettingsActions({ state, onReload, onSave, onSaveAndRestart }) {
  for (const id of ["reload-config", "reload-channel-config", "reload-mcp-config"]) {
    byId(id)?.addEventListener("click", onReload);
  }

  for (const id of ["save-settings", "save-channel-settings", "save-mcp-settings"]) {
    byId(id)?.addEventListener("click", onSave);
  }

  for (const id of ["apply-settings", "apply-channel-settings", "apply-mcp-settings"]) {
    byId(id)?.addEventListener("click", onSaveAndRestart);
  }

  byId("KIRACLAW_PROVIDER")?.addEventListener("change", () => {
    markSettingsDirty(state);
    syncProviderFields();
  });

  const externalToggleFields = ["SLACK_RETRIEVE_ENABLED", "CHROME_ENABLED", "PERPLEXITY_ENABLED", "GITLAB_ENABLED", "MS365_ENABLED", "ATLASSIAN_ENABLED", "TABLEAU_ENABLED"];
  const channelToggleFields = ["SLACK_ENABLED", "TELEGRAM_ENABLED", "DISCORD_ENABLED"];

  for (const field of externalToggleFields) {
    byId(field)?.addEventListener("change", () => {
      markSettingsDirty(state);
      syncExternalMcpFields();
    });
  }

  for (const field of channelToggleFields) {
    byId(field)?.addEventListener("change", () => {
      markSettingsDirty(state);
      syncChannelCards(state);
    });
  }

  for (const field of SETTINGS_FIELDS) {
    const input = byId(field);
    if (!input || field === "KIRACLAW_PROVIDER" || externalToggleFields.includes(field) || channelToggleFields.includes(field)) {
      continue;
    }

    const eventName = BOOLEAN_FIELDS.includes(field) || input.tagName === "SELECT" ? "change" : "input";
    input.addEventListener(eventName, () => markSettingsDirty(state));
  }

  byId("add-remote-mcp")?.addEventListener("click", () => {
    const rows = collectRemoteMcpServers();
    rows.push({ name: "", url: "" });
    renderRemoteMcpServers(rows);
    markSettingsDirty(state);
  });

  byId("remote-mcp-list")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-remote-mcp-delete]");
    if (!button) {
      return;
    }
    const index = Number(button.dataset.remoteMcpDelete);
    if (!Number.isFinite(index)) {
      return;
    }
    const rows = collectRemoteMcpServers();
    rows.splice(index, 1);
    renderRemoteMcpServers(rows);
    markSettingsDirty(state);
  });

  byId("remote-mcp-list")?.addEventListener("input", () => {
    markSettingsDirty(state);
  });
}
