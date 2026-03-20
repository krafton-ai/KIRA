import { DEFAULT_CHAT_SESSION_ID } from "./constants.mjs";
import { getAgentName } from "./branding.mjs";
import { byId, escapeHtml } from "./dom.mjs";
import { t } from "./i18n.mjs";

let chatBusy = false;
const FILE_PATH_PATTERN = /(~[\\/][^\s<>"']*|[A-Za-z]:[\\/][^\s<>"']*|\/(?:Users|tmp|private|var|Volumes|opt|Applications|Library)[^\s<>"']*)/g;

export function clearChatThread(state) {
  const agentName = getAgentName(state);
  const thread = byId("chat-thread");
  if (!thread) {
    return;
  }

  thread.innerHTML = `
    <article class="terminal-entry assistant">
      <div class="terminal-line">
        <span class="terminal-prefix">${escapeHtml(agentName)}</span>
        <div class="terminal-text">${escapeHtml(t("chat.ready"))}</div>
      </div>
    </article>
  `;
}

function appendChatMessage(state, role, text, { meta = "", pending = false, prefix = "" } = {}) {
  const thread = byId("chat-thread");
  if (!thread) {
    return null;
  }

  const message = document.createElement("article");
  message.className = `terminal-entry ${role}${pending ? " pending" : ""}`;
  const pendingSuffix = pending ? '<span class="thinking-dots" aria-hidden="true"></span>' : "";
  const metaMarkup = meta ? `<div class="terminal-meta">${escapeHtml(meta)}</div>` : "";
  const speaker = prefix || (role === "user" ? t("chat.userLabel") : getAgentName(state));
  message.innerHTML = `
    <div class="terminal-line">
      <span class="terminal-prefix">${escapeHtml(speaker)}</span>
      <div class="terminal-text">${renderTerminalText(text)}${pendingSuffix}</div>
    </div>
    ${metaMarkup}
  `;
  thread.appendChild(message);
  thread.scrollTop = thread.scrollHeight;
  return message;
}

function buildScheduledMessageMeta(message) {
  const parts = [t("chat.scheduledMessage")];
  const scheduleName = String(message?.metadata?.schedule_name || "").trim();
  if (scheduleName) {
    parts.push(scheduleName);
  }
  return parts.join(" • ");
}

function replaceChatMessage(message, state, role, text, { meta = "", pending = false, prefix = "" } = {}) {
  if (!message) {
    return;
  }

  message.className = `terminal-entry ${role}${pending ? " pending" : ""}`;
  const pendingSuffix = pending ? '<span class="thinking-dots" aria-hidden="true"></span>' : "";
  const metaMarkup = meta ? `<div class="terminal-meta">${escapeHtml(meta)}</div>` : "";
  const speaker = prefix || (role === "user" ? t("chat.userLabel") : getAgentName(state));
  message.innerHTML = `
    <div class="terminal-line">
      <span class="terminal-prefix">${escapeHtml(speaker)}</span>
      <div class="terminal-text">${renderTerminalText(text)}${pendingSuffix}</div>
    </div>
    ${metaMarkup}
  `;
  const thread = byId("chat-thread");
  thread?.scrollTo({ top: thread.scrollHeight });
}

function summarizeToolEvents(toolEvents) {
  const counts = new Map();
  for (const event of toolEvents || []) {
    if (event.phase !== "start" || !event.name || event.name === "submit") {
      continue;
    }
    counts.set(event.name, (counts.get(event.name) || 0) + 1);
  }

  if (counts.size === 0) {
    return "";
  }

  return `${t("chat.usedTools")}: ${[...counts.entries()].map(([name, count]) => count > 1 ? `${name} x${count}` : name).join(", ")}`;
}

function buildChatMeta(toolEvents, extraParts = []) {
  const parts = [];
  const toolSummary = summarizeToolEvents(toolEvents);
  if (toolSummary) {
    parts.push(toolSummary);
  }
  for (const part of extraParts) {
    if (part) {
      parts.push(part);
    }
  }
  return parts.join(" • ");
}

function normalizeForComparison(text) {
  return String(text ?? "").trim().replace(/\s+/g, " ");
}

function renderTerminalText(text) {
  const source = String(text ?? "");
  return source
    .split("\n")
    .map((line) => renderTerminalLine(line))
    .join("<br>");
}

function renderTerminalLine(line) {
  let lastIndex = 0;
  let html = "";
  FILE_PATH_PATTERN.lastIndex = 0;

  for (const match of line.matchAll(FILE_PATH_PATTERN)) {
    const [fullMatch] = match;
    const matchIndex = match.index ?? 0;
    html += escapeHtml(line.slice(lastIndex, matchIndex));
    html += `<button type="button" class="terminal-path-link" data-open-path="${escapeHtml(fullMatch)}">${escapeHtml(fullMatch)}</button>`;
    lastIndex = matchIndex + fullMatch.length;
  }

  html += escapeHtml(line.slice(lastIndex));
  return html;
}

function setChatBusy(isBusy) {
  chatBusy = isBusy;
  const input = byId("chat-input");
  const sendButton = byId("send-chat");
  const clearButton = byId("clear-chat");
  const sessionInput = byId("chat-session-id");

  if (input) {
    input.disabled = isBusy;
  }
  if (sessionInput) {
    sessionInput.disabled = isBusy;
  }
  if (sendButton) {
    sendButton.disabled = isBusy;
    sendButton.textContent = isBusy ? t("chat.thinking") : t("chat.send");
  }
  if (clearButton) {
    clearButton.disabled = isBusy;
  }
}

async function sendChat({ api, state, onAfterSend }) {
  const input = byId("chat-input");
  const sessionInput = byId("chat-session-id");
  if (!input || !sessionInput || chatBusy) {
    return;
  }

  const prompt = input.value.trim();
  const sessionId = sessionInput.value.trim() || DEFAULT_CHAT_SESSION_ID;
  if (!prompt) {
    return;
  }

  appendChatMessage(state, "user", prompt);
  input.value = "";
  const thinkingPrefix = `${getAgentName(state)} (${t("chat.thinkingLabel")})`;
  const pendingMessage = appendChatMessage(state, "assistant", t("chat.thinking"), {
    meta: t("chat.preparingResponse"),
    pending: true,
    prefix: thinkingPrefix,
  });
  setChatBusy(true);

  try {
    const daemonStatus = await api.getDaemonStatus();
    if (!daemonStatus.running) {
      throw new Error(t("chat.startEngineFirst"));
    }

    const result = await api.runPrompt({
      session_id: sessionId,
      prompt,
    });

    if (result.state !== "completed") {
      throw new Error(result.error || "Run failed.");
    }

    const internalSummary = result.internal_summary || result.final_response || t("chat.emptyInternalSummary");
    const spokenText = Array.isArray(result.spoken_messages) && result.spoken_messages.length > 0
      ? result.spoken_messages.join("\n\n")
      : "";
    const summaryMatchesSpoken = spokenText
      ? normalizeForComparison(spokenText) === normalizeForComparison(internalSummary)
      : false;

    if (spokenText) {
      replaceChatMessage(
        pendingMessage,
        state,
        "assistant",
        spokenText,
        {
          meta: buildChatMeta(result.tool_events, [t("chat.spokenReply")]),
        },
      );
      if (!summaryMatchesSpoken) {
        appendChatMessage(
          state,
          "assistant",
          internalSummary,
          {
            meta: t("chat.internalSummary"),
            prefix: thinkingPrefix,
          },
        );
      }
    } else {
      replaceChatMessage(
        pendingMessage,
        state,
        "assistant",
        internalSummary,
        {
          meta: buildChatMeta(result.tool_events, [t("chat.internalSummary")]),
          prefix: thinkingPrefix,
        },
      );
    }
    await onAfterSend();
  } catch (error) {
    replaceChatMessage(pendingMessage, state, "assistant", t("chat.runFailed", { message: error.message }));
  } finally {
    setChatBusy(false);
    input.focus();
  }
}

export function appendDesktopMessages(state, messages) {
  if (!Array.isArray(messages) || messages.length === 0) {
    return;
  }

  for (const message of messages) {
    const text = String(message?.text || "").trim();
    if (!text) {
      continue;
    }
    appendChatMessage(state, "assistant", text, {
      meta: buildScheduledMessageMeta(message),
    });
  }
}

export function bindChatActions({ api, state, onAfterSend }) {
  const input = byId("chat-input");
  const thread = byId("chat-thread");
  let composing = false;

  byId("clear-chat")?.addEventListener("click", () => clearChatThread(state));
  byId("send-chat")?.addEventListener("click", () => sendChat({ api, state, onAfterSend }));
  thread?.addEventListener("click", async (event) => {
    const target = event.target.closest("[data-open-path]");
    if (!target) {
      return;
    }

    const targetPath = target.getAttribute("data-open-path");
    if (!targetPath) {
      return;
    }

    event.preventDefault();
    await api.openPath(targetPath);
  });

  input?.addEventListener("compositionstart", () => {
    composing = true;
  });

  input?.addEventListener("compositionend", () => {
    composing = false;
  });

  input?.addEventListener("keydown", (event) => {
    if (composing || event.isComposing || event.keyCode === 229) {
      return;
    }

    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendChat({ api, state, onAfterSend });
    }
  });
}
