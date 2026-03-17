from __future__ import annotations

from krim_sdk.prompt import CORE as KRIM_CORE_PROMPT

from kiraclaw_agentd.system_prompt import build_system_prompt


def test_system_prompt_keeps_krim_core_rules_but_overrides_identity() -> None:
    prompt = build_system_prompt("지호봇", ["bash", "read", "write", "edit", "grep", "glob", "submit"])

    krim_lines = KRIM_CORE_PROMPT.splitlines()
    prompt_lines = prompt.splitlines()

    assert prompt_lines[0] == (
        "You are 지호봇, the active agent persona running inside the KiraClaw product shell "
        "on the user's local daemon behind desktop and Slack control surfaces."
    )
    assert prompt_lines[1] == "You have tools: read, write, edit, bash, grep, glob, submit."
    assert prompt_lines[2:] == krim_lines[2:]


def test_system_prompt_mentions_skill_only_when_available() -> None:
    prompt = build_system_prompt(
        "KIRA",
        ["bash", "read", "write", "edit", "grep", "glob", "submit", "skill"],
        [
            {
                "id": "jira-reader",
                "name": "jira-reader",
                "description": "Read Jira carefully",
                "path": "/workspace/skills/jira-reader",
                "source": "workspace",
            }
        ],
    )

    assert "You have tools: read, write, edit, bash, grep, glob, skill, submit." in prompt
    assert "Available skills are installed as SKILL.md packages under the workspace skills directory." in prompt
    assert "If you create or install a new skill, place it under Filesystem Base Dir/skills/<skill-name>/SKILL.md." in prompt
    assert "When a skill is relevant, call the skill tool with the listed skill name to load its full instructions before following it." in prompt
    assert "Use read only for extra files or resources referenced by the loaded skill instructions." in prompt
    assert "- jira-reader: Read Jira carefully (skill directory: /workspace/skills/jira-reader)" in prompt


def test_system_prompt_mentions_mcp_tools_when_available() -> None:
    prompt = build_system_prompt(
        "KIRA",
        ["bash", "read", "write", "edit", "grep", "glob", "submit"],
        None,
        ["mcp__time__get_current_time"],
    )

    assert "Additional tools available: mcp__time__get_current_time" in prompt


def test_system_prompt_falls_back_to_default_name_when_blank() -> None:
    prompt = build_system_prompt("   ", ["bash", "read", "write", "edit", "grep", "glob", "submit"])

    assert prompt.splitlines()[0].startswith("You are KIRA,")
