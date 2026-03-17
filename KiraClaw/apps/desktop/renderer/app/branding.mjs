export function getAgentName(state) {
  const configured = (state.config.KIRACLAW_AGENT_NAME || "").trim();
  const runtimeName = state.runtime && state.runtime.agent_name ? String(state.runtime.agent_name).trim() : "";
  return configured || runtimeName || "KIRA";
}

export function applyAgentIdentity(state) {
  document.title = `${getAgentName(state)} · KiraClaw`;
}
