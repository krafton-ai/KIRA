import { byId, escapeHtml, setText } from "./dom.mjs";

function summarizeSchedule(schedule) {
  const type = String(schedule.schedule_type || "").trim();
  const value = String(schedule.schedule_value || "").trim();
  if (!type && !value) {
    return "Unknown schedule";
  }
  if (type === "cron") {
    return `Cron · ${value}`;
  }
  if (type === "date") {
    return `One time · ${value}`;
  }
  return `${type || "schedule"} · ${value}`;
}

function summarizePrompt(text) {
  const normalized = String(text || "").replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "No prompt text.";
  }
  if (normalized.length <= 140) {
    return normalized;
  }
  return `${normalized.slice(0, 137).trimEnd()}...`;
}

function scheduleMeta(schedule) {
  const parts = [];
  if (schedule.channel_target) {
    const channelLabel = schedule.channel_type === "telegram" ? "Telegram" : "Slack";
    parts.push(`${channelLabel} ${schedule.channel_target}`);
  }
  if (schedule.user) {
    parts.push(`User ${schedule.user}`);
  }
  return parts.join(" · ");
}

export function renderSchedulesState(state) {
  const list = byId("schedule-list");
  if (!list) {
    return;
  }

  if (state.scheduleError) {
    list.innerHTML = `
      <article class="simple-item">
        <strong>Schedule load failed</strong>
        <p>${escapeHtml(state.scheduleError)}</p>
      </article>
    `;
    setText(byId("schedule-status"), `Schedule load failed: ${state.scheduleError}`);
    return;
  }

  if (!state.schedules.length) {
    list.innerHTML = `
      <article class="simple-item">
        <strong>No schedules yet</strong>
        <p>No registered schedules were found in the current workspace.</p>
      </article>
    `;
    setText(byId("schedule-status"), "No schedules are configured yet.");
    return;
  }

  list.innerHTML = state.schedules.map((schedule) => `
    <article class="simple-item">
      <div class="watch-card-head">
        <strong>${escapeHtml(String(schedule.name || schedule.id || "Schedule"))}</strong>
        <span class="status-chip ${schedule.is_enabled !== false ? "online" : "offline"}">${schedule.is_enabled !== false ? "Enabled" : "Disabled"}</span>
      </div>
      <p>${escapeHtml(summarizePrompt(schedule.text || ""))}</p>
      <p class="watch-card-meta">${escapeHtml(summarizeSchedule(schedule))}${scheduleMeta(schedule) ? ` · ${escapeHtml(scheduleMeta(schedule))}` : ""}</p>
    </article>
  `).join("");

  const fileSuffix = state.scheduleFile ? ` · ${state.scheduleFile}` : "";
  setText(
    byId("schedule-status"),
    `${state.schedules.length} schedule${state.schedules.length === 1 ? "" : "s"} loaded${fileSuffix}.`,
  );
}

export function bindScheduleActions({ onReload }) {
  byId("reload-schedules")?.addEventListener("click", onReload);
}
