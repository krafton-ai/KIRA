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
    skill_names: list[str] | None = None,
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
    if skill_names:
        parts.append(
            "Available skills can be loaded on demand with the skill tool: "
            + ", ".join(skill_names)
        )
    return "\n\n".join(parts)
