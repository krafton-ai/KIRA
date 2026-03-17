import { BOOLEAN_FIELDS, EXTERNAL_MCP_CONFIG_FIELDS, EXTERNAL_MCP_SERVER_NAMES, PROVIDER_DEFAULT_MODELS, SETTINGS_FIELDS, SELECT_DEFAULTS } from "./constants.mjs";
import { byId, setText } from "./dom.mjs";

function normalizeBoolean(value) {
  return String(value ?? "").trim().toLowerCase() === "true";
}

function runtimeValueForField(state, field) {
  if (!state.runtime) {
    return "";
  }

  const runtimeMap = {
    KIRACLAW_AGENT_NAME: state.runtime.agent_name,
    KIRACLAW_PROVIDER: state.runtime.provider,
    KIRACLAW_MODEL: state.runtime.model,
    SLACK_TEAM_ID: state.runtime.slack_identity && state.runtime.slack_identity.team_id,
    SLACK_ALLOWED_NAMES: state.runtime.slack_allowed_names,
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
    modelInput.placeholder = nextDefault || "claude-opus-4-6 or gpt-5.3-codex";
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
  syncMcpView(state);
  syncExternalMcpFields();
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

  return updates;
}

export function setSettingsStatus(message) {
  setText(byId("settings-status"), message);
  setText(byId("channel-status"), message);
  setText(byId("mcp-status"), message);
}

function syncMcpView(state) {
  const runtime = state.runtime;
  const configuredExternal = EXTERNAL_MCP_SERVER_NAMES.filter((name) => {
    const fieldName = EXTERNAL_MCP_CONFIG_FIELDS[name];
    return normalizeBoolean(state.config[fieldName]);
  });

  if (!runtime) {
    if (configuredExternal.length > 0) {
      setText(byId("mcp-status"), `Enabled in config: ${configuredExternal.join(", ")}`);
      return;
    }
    setText(byId("mcp-status"), "External MCP settings are read from ~/.kira/config.env.");
    return;
  }

  const externalLoaded = (runtime.mcp_loaded_servers || []).filter((name) => EXTERNAL_MCP_SERVER_NAMES.includes(name));
  const externalFailed = (runtime.mcp_failed_servers || []).filter((name) => EXTERNAL_MCP_SERVER_NAMES.includes(name));
  if (externalLoaded.length > 0) {
    const parts = [`Loaded now: ${externalLoaded.join(", ")}`];
    if (externalFailed.length > 0) {
      parts.push(`Failed: ${externalFailed.join(", ")}`);
    } else if (configuredExternal.length > externalLoaded.length) {
      const pending = configuredExternal.filter((name) => !externalLoaded.includes(name));
      if (pending.length > 0) {
        parts.push(`Enabled in config: ${pending.join(", ")}`);
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
    setText(byId("mcp-status"), `Failed: ${externalFailed.join(", ")}`);
    return;
  }

  if (configuredExternal.length > 0) {
    setText(byId("mcp-status"), `Enabled in config: ${configuredExternal.join(", ")}`);
    return;
  }

  setText(byId("mcp-status"), "No external npm MCP integrations are loaded right now.");
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

  const externalToggleFields = ["CHROME_ENABLED", "PERPLEXITY_ENABLED", "GITLAB_ENABLED", "MS365_ENABLED", "ATLASSIAN_ENABLED", "TABLEAU_ENABLED"];

  for (const field of externalToggleFields) {
    byId(field)?.addEventListener("change", () => {
      markSettingsDirty(state);
      syncExternalMcpFields();
    });
  }

  for (const field of SETTINGS_FIELDS) {
    const input = byId(field);
    if (!input || field === "KIRACLAW_PROVIDER" || externalToggleFields.includes(field)) {
      continue;
    }

    const eventName = BOOLEAN_FIELDS.includes(field) || input.tagName === "SELECT" ? "change" : "input";
    input.addEventListener(eventName, () => markSettingsDirty(state));
  }
}
