import { byId, escapeHtml, setText } from "./dom.mjs";

const NEW_WATCH_ID = "__new_watch__";

function formatSchedule(spec) {
  return `Every ${spec.interval_minutes} minute${spec.interval_minutes === 1 ? "" : "s"}`;
}

function normalizeWatchText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function deriveWatchTitle(watch) {
  for (const value of [watch.condition, watch.action]) {
    const text = normalizeWatchText(value);
    if (text) {
      return text.length > 72 ? `${text.slice(0, 69).trimEnd()}...` : text;
    }
  }
  return "New Watch";
}

function formatRunTimestamp(value) {
  if (!value) {
    return "Pending";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function summarizeRunsForWatch(state, watchId) {
  return state.watchRuns.filter((run) => run.watch_id === watchId).slice(0, 5);
}

function draftWatch() {
  return {
    watch_id: NEW_WATCH_ID,
    interval_minutes: 30,
    condition: "",
    action: "",
    channel_id: "",
    is_enabled: true,
  };
}

function watchItemMarkup(state, watch) {
  const isDraft = watch.watch_id === NEW_WATCH_ID;
  const open = state.selectedWatchId === watch.watch_id || (isDraft && state.watchDraft);
  const runs = isDraft ? [] : summarizeRunsForWatch(state, watch.watch_id);
  const title = deriveWatchTitle(watch);
  const subtitle = isDraft ? "Unsaved draft" : formatSchedule(watch);

  return `
    <details class="watch-item ${open ? "open" : ""}" data-watch-item="${escapeHtml(watch.watch_id)}"${open ? " open" : ""}>
      <summary class="watch-summary">
        <div class="watch-summary-copy">
          <strong>${escapeHtml(title)}</strong>
          <p class="watch-card-meta">${escapeHtml(subtitle)}</p>
        </div>
        <div class="watch-summary-side">
          <span class="status-chip ${watch.is_enabled ? "online" : "offline"}">${watch.is_enabled ? "Enabled" : "Disabled"}</span>
        </div>
      </summary>
      <div class="watch-item-body">
        <div class="form-grid watch-item-grid">
          <label class="field">
            <span>Every N Minutes</span>
            <input data-watch-input="interval_minutes" type="number" min="1" step="1" value="${escapeHtml(String(watch.interval_minutes || 30))}" placeholder="30" />
          </label>
          <label class="field full">
            <span>Condition</span>
            <textarea data-watch-input="condition" rows="3" placeholder="If a blocked issue appears, or a review state changes, and it matters to me.">${escapeHtml(watch.condition || "")}</textarea>
          </label>
          <label class="field full">
            <span>Action</span>
            <textarea data-watch-input="action" rows="3" placeholder="Send a concise Slack update, save the fact to memory, and summarize what changed.">${escapeHtml(watch.action || "")}</textarea>
          </label>
          <label class="field">
            <span>Default Slack Channel</span>
            <input data-watch-input="channel_id" value="${escapeHtml(watch.channel_id || "")}" placeholder="D123456 or C123456" />
          </label>
          <div class="field">
            <span>Enabled</span>
            <div class="toggle-field">
              <div class="toggle-copy">
                <span class="toggle-title">Active</span>
                <span class="toggle-help">Disabled watches stay saved but do not run.</span>
              </div>
              <label class="toggle-switch">
                <input data-watch-input="is_enabled" type="checkbox"${watch.is_enabled !== false ? " checked" : ""} />
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>

        <div class="button-row watch-item-actions">
          <button class="primary" data-watch-action="save" data-watch-id="${escapeHtml(watch.watch_id)}">Save</button>
          <button class="ghost" data-watch-action="run" data-watch-id="${escapeHtml(watch.watch_id)}"${isDraft ? " disabled" : ""}>Run Now</button>
          <button class="danger-button" data-watch-action="delete" data-watch-id="${escapeHtml(watch.watch_id)}"${isDraft ? " disabled" : ""}>Delete</button>
        </div>

        <div class="watch-inline-runs">
          <div class="card-head">
            <h3>Recent Runs</h3>
          </div>
          ${
            runs.length === 0
              ? `<article class="watch-run-item empty"><p class="section-copy">${isDraft ? "Save this watch first." : "No runs yet."}</p></article>`
              : runs.map((run) => `
                  <article class="watch-run-item">
                    <div class="watch-run-head">
                      <strong>${escapeHtml(run.watch_name)}</strong>
                      <span class="status-chip ${run.state === "completed" ? "online" : "offline"}">${escapeHtml(run.state)}</span>
                    </div>
                    <p class="section-copy">${escapeHtml(run.summary || run.error || "No summary")}</p>
                    <p class="watch-card-meta">${escapeHtml(formatRunTimestamp(run.finished_at || run.created_at))}${run.tool_names?.length ? ` · ${escapeHtml(run.tool_names.join(", "))}` : ""}</p>
                  </article>
                `).join("")
          }
        </div>
      </div>
    </details>
  `;
}

export function renderWatchState(state) {
  const list = byId("watch-list");
  if (!list) {
    return;
  }

  const rows = state.watchDraft
    ? [draftWatch(), ...state.watches]
    : state.watches;

  if (!rows.length) {
    list.innerHTML = `
      <article class="watch-card watch-card-empty">
        <strong>No watches yet</strong>
        <p class="section-copy">Use + Add Watch to create your first repeating watch.</p>
      </article>
    `;
    setText(byId("watch-status"), "No watches are configured yet.");
    return;
  }

  list.innerHTML = rows.map((watch) => watchItemMarkup(state, watch)).join("");
  setText(byId("watch-status"), `${state.watches.length} watch${state.watches.length === 1 ? "" : "es"} loaded.`);
}

export function collectWatchPayload(watchId) {
  const item = document.querySelector(`[data-watch-item="${watchId}"]`);
  if (!item) {
    return null;
  }

  const get = (name) => item.querySelector(`[data-watch-input="${name}"]`);
  return {
    watch_id: watchId === NEW_WATCH_ID ? undefined : watchId,
    interval_minutes: Number(get("interval_minutes")?.value || "0"),
    condition: get("condition")?.value.trim() || "",
    action: get("action")?.value.trim() || "",
    channel_id: get("channel_id")?.value.trim() || undefined,
    is_enabled: Boolean(get("is_enabled")?.checked),
  };
}

export function validateWatchPayload(payload) {
  if (!payload) {
    return "Watch form is missing.";
  }
  if (!Number.isFinite(payload.interval_minutes) || payload.interval_minutes < 1) {
    return "Every N Minutes must be at least 1.";
  }
  if (!payload.condition.trim()) {
    return "Watch condition is required.";
  }
  if (!payload.action.trim()) {
    return "Watch action is required.";
  }
  return null;
}

export function setWatchStatus(message) {
  setText(byId("watch-status"), message);
}

export function bindWatchActions({ state, onSelect, onReload, onNew, onSave, onRunNow, onDelete }) {
  byId("reload-watches")?.addEventListener("click", onReload);
  byId("add-watch-inline")?.addEventListener("click", onNew);

  const list = byId("watch-list");
  list?.addEventListener("click", (event) => {
    const actionButton = event.target.closest("[data-watch-action]");
    if (actionButton) {
      const watchId = actionButton.dataset.watchId;
      const action = actionButton.dataset.watchAction;
      if (!watchId || !action) {
        return;
      }
      if (action === "save") {
        onSave(watchId);
      } else if (action === "run") {
        onRunNow(watchId);
      } else if (action === "delete") {
        onDelete(watchId);
      }
      return;
    }
  });

  const markDirty = (event) => {
    const input = event.target.closest("[data-watch-input]");
    const item = event.target.closest("[data-watch-item]");
    if (!input || !item) {
      return;
    }
    state.selectedWatchId = item.dataset.watchItem || state.selectedWatchId;
    state.watchDirty = true;
  };

  list?.addEventListener("input", markDirty);
  list?.addEventListener("change", markDirty);

  list?.addEventListener("toggle", (event) => {
    const details = event.target;
    if (!(details instanceof HTMLDetailsElement) || !details.dataset.watchItem) {
      return;
    }
    if (details.open) {
      onSelect(details.dataset.watchItem);
    } else if (state.selectedWatchId === details.dataset.watchItem) {
      onSelect(null);
    }
  });
}

export function getNewWatchId() {
  return NEW_WATCH_ID;
}
