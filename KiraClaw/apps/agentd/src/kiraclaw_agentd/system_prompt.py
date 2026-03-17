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


def build_system_prompt(
    agent_name: str,
    tool_names: list[str],
    skill_rows: list[dict[str, str]] | None = None,
    extra_tool_names: list[str] | None = None,
) -> str:
    parts = [
        build_core_prompt(
            identity_line=_identity_line(agent_name),
            tool_names=_ordered_tool_names(tool_names),
        )
    ]
    if extra_tool_names:
        parts.append(f"Additional tools available: {', '.join(extra_tool_names)}")
    if skill_rows:
        parts.append(_format_skill_rows(skill_rows))
    return "\n\n".join(parts)
