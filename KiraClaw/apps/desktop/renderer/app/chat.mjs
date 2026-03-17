import { DEFAULT_CHAT_SESSION_ID } from "./constants.mjs";
import { getAgentName } from "./branding.mjs";
import { byId, escapeHtml } from "./dom.mjs";

let chatBusy = false;

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
        <div class="terminal-text">Direct chat is ready.</div>
      </div>
    </article>
  `;
}

function appendChatMessage(state, role, text, { meta = "", pending = false } = {}) {
  const thread = byId("chat-thread");
  if (!thread) {
    return null;
  }

  const message = document.createElement("article");
  message.className = `terminal-entry ${role}${pending ? " pending" : ""}`;
  const pendingSuffix = pending ? '<span class="thinking-dots" aria-hidden="true"></span>' : "";
  const metaMarkup = meta ? `<div class="terminal-meta">${escapeHtml(meta)}</div>` : "";
  message.innerHTML = `
    <div class="terminal-line">
      <span class="terminal-prefix">${role === "user" ? "You" : escapeHtml(getAgentName(state))}</span>
      <div class="terminal-text">${escapeHtml(text).replace(/\n/g, "<br>")}${pendingSuffix}</div>
    </div>
    ${metaMarkup}
  `;
  thread.appendChild(message);
  thread.scrollTop = thread.scrollHeight;
  return message;
}

function replaceChatMessage(message, state, role, text, { meta = "", pending = false } = {}) {
  if (!message) {
    return;
  }

  message.className = `terminal-entry ${role}${pending ? " pending" : ""}`;
  const pendingSuffix = pending ? '<span class="thinking-dots" aria-hidden="true"></span>' : "";
  const metaMarkup = meta ? `<div class="terminal-meta">${escapeHtml(meta)}</div>` : "";
  message.innerHTML = `
    <div class="terminal-line">
      <span class="terminal-prefix">${role === "user" ? "You" : escapeHtml(getAgentName(state))}</span>
      <div class="terminal-text">${escapeHtml(text).replace(/\n/g, "<br>")}${pendingSuffix}</div>
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

  return `Used: ${[...counts.entries()].map(([name, count]) => count > 1 ? `${name} x${count}` : name).join(", ")}`;
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
    sendButton.textContent = isBusy ? "Thinking..." : "Send";
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
  const pendingMessage = appendChatMessage(state, "assistant", "Thinking", {
    meta: "Preparing a response...",
    pending: true,
  });
  setChatBusy(true);

  try {
    const daemonStatus = await api.getDaemonStatus();
    if (!daemonStatus.running) {
      throw new Error("Start the KIRA Engine first.");
    }

    const result = await api.runPrompt({
      session_id: sessionId,
      prompt,
    });

    if (result.state !== "completed") {
      throw new Error(result.error || "Run failed.");
    }

    replaceChatMessage(
      pendingMessage,
      state,
      "assistant",
      result.final_response || "(empty response)",
      {
        meta: summarizeToolEvents(result.tool_events),
      },
    );
    await onAfterSend();
  } catch (error) {
    replaceChatMessage(pendingMessage, state, "assistant", `Run failed: ${error.message}`);
  } finally {
    setChatBusy(false);
    input.focus();
  }
}

export function bindChatActions({ api, state, onAfterSend }) {
  const input = byId("chat-input");
  let composing = false;

  byId("clear-chat")?.addEventListener("click", () => clearChatThread(state));
  byId("send-chat")?.addEventListener("click", () => sendChat({ api, state, onAfterSend }));

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
