import { byId, escapeHtml, setText } from "./dom.mjs";

function formatTime(value) {
  const text = String(value || "").trim();
  if (!text) {
    return "";
  }

  try {
    return new Date(text).toLocaleString();
  } catch {
    return text;
  }
}

function renderMultiline(value) {
  const text = String(value || "").trim();
  if (!text) {
    return '<span class="log-empty">None</span>';
  }
  return escapeHtml(text).replace(/\n/g, "<br>");
}

function renderSpokenMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0) {
    return '<span class="log-empty">None</span>';
  }
  return messages.map((message) => `<div class="log-spoken-item">${renderMultiline(message)}</div>`).join("");
}

function logCard(row) {
  const stateClass = row.state === "completed" ? "online" : (row.state === "failed" ? "offline" : "");
  const metaParts = [
    row.source || "unknown",
    row.session_id || "",
    formatTime(row.finished_at || row.created_at),
  ].filter(Boolean);

  return `
    <article class="simple-item run-log-card">
      <div class="schedule-card-head">
        <strong>${escapeHtml(row.run_id || "run")}</strong>
        <span class="status-chip ${stateClass}">${escapeHtml(row.state || "unknown")}</span>
      </div>
      <p class="run-log-meta">${escapeHtml(metaParts.join(" · "))}</p>
      <details class="details-card run-log-details">
        <summary>View Details</summary>
        <div class="details-body run-log-body">
          <div class="run-log-section">
            <div class="run-log-label">Prompt</div>
            <div class="run-log-value">${renderMultiline(row.prompt)}</div>
          </div>
          <div class="run-log-section">
            <div class="run-log-label">Internal Summary</div>
            <div class="run-log-value">${renderMultiline(row.internal_summary)}</div>
          </div>
          <div class="run-log-section">
            <div class="run-log-label">Spoken Reply</div>
            <div class="run-log-value">${renderSpokenMessages(row.spoken_messages)}</div>
          </div>
          <div class="run-log-section">
            <div class="run-log-label">Tools</div>
            <div class="run-log-value">${renderMultiline(row.tool_summary)}</div>
          </div>
          <div class="run-log-section">
            <div class="run-log-label">Silent Reason</div>
            <div class="run-log-value">${renderMultiline(row.silent_reason)}</div>
          </div>
          <div class="run-log-section">
            <div class="run-log-label">Error</div>
            <div class="run-log-value">${renderMultiline(row.error)}</div>
          </div>
        </div>
      </details>
    </article>
  `;
}

export function renderRunLogsState(state) {
  const list = byId("run-log-list");
  if (!list) {
    return;
  }

  if (state.runLogError) {
    list.innerHTML = `
      <article class="simple-item">
        <strong>Run log load failed</strong>
        <p>${escapeHtml(state.runLogError)}</p>
      </article>
    `;
    setText(byId("run-log-status"), `Run log load failed: ${state.runLogError}`);
    return;
  }

  if (!Array.isArray(state.runLogs) || state.runLogs.length === 0) {
    list.innerHTML = `
      <article class="simple-item">
        <strong>No run logs yet</strong>
        <p>No recent runs have been recorded yet.</p>
      </article>
    `;
    setText(byId("run-log-status"), state.runLogFile ? `No recent runs yet · ${state.runLogFile}` : "No recent runs yet.");
    return;
  }

  list.innerHTML = state.runLogs.map(logCard).join("");
  const suffix = state.runLogFile ? ` · ${state.runLogFile}` : "";
  setText(byId("run-log-status"), `${state.runLogs.length} recent run log${state.runLogs.length === 1 ? "" : "s"}${suffix}.`);
}

export function bindRunLogActions({ state, onReload, onOpenPath }) {
  byId("reload-run-logs")?.addEventListener("click", onReload);
  byId("open-run-log-file")?.addEventListener("click", () => {
    onOpenPath(state.runLogFile);
  });
}
