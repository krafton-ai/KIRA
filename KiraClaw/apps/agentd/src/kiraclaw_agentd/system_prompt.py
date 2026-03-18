from __future__ import annotations

from krim_sdk.prompt import build_core_prompt

_PREFERRED_TOOL_ORDER = [
    "read",
    "write",
    "edit",
    "bash",
    "grep",
    "glob",
    "skill",
    "speak",
    "submit",
]


def _format_skill_rows(skill_rows: list[dict[str, str]]) -> str:
    lines = [
        "Available skills are installed as SKILL.md packages under the workspace skills directory.",
        "When a skill is relevant, call the skill tool with the listed skill name to load its full instructions before following it.",
        "Use read only for extra files or resources referenced by the loaded skill instructions.",
        "If you create or install a new skill, place it under Filesystem Base Dir/skills/<skill-name>/SKILL.md.",
    ]
    for row in skill_rows:
        name = row.get("name", row.get("id", "unknown"))
        description = row.get("description", "").strip() or "No description provided."
        path = row.get("path", "").strip()
        lines.append(f"- {name}: {description} (skill directory: {path})")
    return "\n".join(lines)


def _ordered_tool_names(tool_names: list[str]) -> list[str]:
    unique_names: list[str] = []
    seen: set[str] = set()

    for name in _PREFERRED_TOOL_ORDER + tool_names:
        if name in tool_names and name not in seen:
            seen.add(name)
            unique_names.append(name)

    return unique_names


def _identity_line(agent_name: str) -> str:
    active_name = agent_name.strip() or "KIRA"
    return (
        f"You are {active_name}, the active agent persona running inside the KiraClaw product shell "
        "on the user's local daemon behind desktop and Slack control surfaces."
    )


def _format_persona_guidance(agent_persona: str | None) -> str | None:
    persona = str(agent_persona or "").strip()
    if not persona:
        return None

    return (
        "Persona guidance for how you should generally carry yourself while thinking, speaking, and acting:\n"
        f"{persona}"
    )


def _format_memory_tool_guidance(tool_names: list[str]) -> str | None:
    if not any(
        name in tool_names
        for name in ("memory_search", "memory_save", "memory_index_search", "memory_index_save")
    ):
        return None

    return (
        "Long-term memory lives under Filesystem Base Dir/memories, and its structured index lives in Filesystem Base Dir/memories/index.json.\n"
        "For deliberate memory work, default to this flow: memory_index_search -> read or edit the actual memory files -> memory_index_save.\n"
        "Use memory_index_search to find relevant memory files before reading, editing, moving, or deleting them.\n"
        "When you deliberately edit a memory file with normal file tools, call memory_index_save afterward to keep the index in sync.\n"
        "If you already know the exact memory file path, you may read it directly, but still keep the index in sync after material changes.\n"
        "Use memory_search when the user explicitly asks to inspect memory contents directly.\n"
        "Use memory_save when the user explicitly asks you to remember or record a durable fact quickly.\n"
        "Prefer memory index tools over manually editing index.json, and do not rewrite index.json with normal file tools."
    )


def _format_speak_guidance(agent_name: str, tool_names: list[str]) -> str | None:
    if "speak" not in tool_names:
        return None

    active_name = agent_name.strip() or "KIRA"
    return (
        "Adapters are the user's ears and mouth into shared spaces, but you are the thinking core.\n"
        "Your internal run summary and your outward speech are separate.\n"
        "Use speak only for words that should actually be delivered to the current conversation.\n"
        "Any normal text you return without using speak becomes internal summary only.\n"
        "Do not rely on internal summary text to reach users through Slack or Telegram. Channel adapters only deliver speak output.\n"
        "For normal replies in the current conversation, prefer speak over direct Slack or Telegram send-message tools.\n"
        "Reserve direct channel send tools for proactive delivery, cross-room delivery, or channel-specific actions such as file upload.\n"
        "In scheduled or background runs, think and act first. Speak only when there is a real audience that should receive an outward message.\n"
        "If no outward message is needed, do not call speak.\n"
        "Keep your internal summary concise, action-oriented, and free of long private chain-of-thought dumps.\n"
        "When the current input looks like a multi-person room transcript, treat it as ambient shared-space context rather than as a guaranteed direct request.\n"
        f"In shared rooms, speak only if someone explicitly addresses you as {active_name} or if interrupting would clearly provide useful help. Otherwise stay silent."
    )


def build_system_prompt(
    agent_name: str,
    tool_names: list[str],
    skill_rows: list[dict[str, str]] | None = None,
    extra_tool_names: list[str] | None = None,
    agent_persona: str | None = None,
) -> str:
    parts = [
        build_core_prompt(
            identity_line=_identity_line(agent_name),
            tool_names=_ordered_tool_names(tool_names),
        )
    ]
    persona_guidance = _format_persona_guidance(agent_persona)
    if persona_guidance:
        parts.append(persona_guidance)
    if extra_tool_names:
        parts.append(f"Additional tools available: {', '.join(extra_tool_names)}")
    if skill_rows:
        parts.append(_format_skill_rows(skill_rows))
    speak_guidance = _format_speak_guidance(agent_name, tool_names)
    if speak_guidance:
        parts.append(speak_guidance)
    memory_guidance = _format_memory_tool_guidance(tool_names)
    if memory_guidance:
        parts.append(memory_guidance)
    return "\n\n".join(parts)
