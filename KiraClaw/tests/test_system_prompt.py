from __future__ import annotations

from krim_sdk.prompt import CORE as KRIM_CORE_PROMPT

from kiraclaw_agentd.system_prompt import build_system_prompt


def test_system_prompt_keeps_krim_core_rules_but_overrides_identity() -> None:
    prompt = build_system_prompt("지호봇", ["bash", "read", "write", "edit", "grep", "glob", "submit"])

    krim_lines = KRIM_CORE_PROMPT.splitlines()
    prompt_lines = prompt.splitlines()

    assert prompt_lines[0] == (
        "You are 지호봇, the active agent persona running inside the KiraClaw product shell "
        "on the user's local daemon behind desktop and channel control surfaces."
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
    assert "Skills are available as optional SKILL.md packages under the workspace skills directory." in prompt
    assert "If you create or install a new skill, place it under Filesystem Base Dir/skills/<skill-name>/SKILL.md." in prompt
    assert "If a task may need a specialized workflow, inspect and load the appropriate skill with the skill tool before acting." in prompt
    assert "Do not assume a skill's contents until you have loaded it." in prompt
    assert "Use read only for files or resources referenced by the loaded skill instructions." in prompt
    assert "jira-reader" not in prompt
    assert "Read Jira carefully" not in prompt


def test_system_prompt_mentions_mcp_tools_when_available() -> None:
    prompt = build_system_prompt(
        "KIRA",
        ["bash", "read", "write", "edit", "grep", "glob", "submit"],
        None,
        ["mcp__time__get_current_time"],
    )

    assert "Additional tools available: mcp__time__get_current_time" in prompt


def test_system_prompt_mentions_speak_guidance_when_available() -> None:
    prompt = build_system_prompt(
        "세나",
        ["bash", "read", "write", "edit", "grep", "glob", "speak", "submit"],
    )

    assert "Use speak only for words that should actually be delivered to the current conversation." in prompt
    assert "Any normal text you return without using speak becomes internal summary only." in prompt
    assert "Keep your internal summary concise, action-oriented" in prompt
    assert "scheduled or background runs, think and act first" in prompt
    assert "speak only if someone explicitly addresses you as 세나" in prompt


def test_system_prompt_marks_channel_tools_as_delivery_only() -> None:
    prompt = build_system_prompt(
        "세나",
        [
            "bash",
            "read",
            "write",
            "edit",
            "grep",
            "glob",
            "speak",
            "slack_send_message",
            "slack_reply_to_thread",
            "submit",
        ],
    )

    assert "Channel tools are delivery/control tools, not retrieval tools." in prompt
    assert "Do not use channel tools to ask humans for information" in prompt
    assert "wider workspace search or investigation belongs to MCP/retrieval paths" in prompt
    assert "reuse that surfaced reference before asking follow-up questions" in prompt


def test_system_prompt_mentions_memory_index_first_flow_when_available() -> None:
    prompt = build_system_prompt(
        "세나",
        [
            "bash",
            "read",
            "write",
            "edit",
            "grep",
            "glob",
            "memory_search",
            "memory_save",
            "memory_index_search",
            "memory_index_save",
            "submit",
        ],
    )

    assert "default to this flow: memory_index_search -> read or edit the actual memory files -> memory_index_save" in prompt
    assert "For anything beyond brief small talk or a one-off factual answer" in prompt
    assert "If retrieved memory is present, treat it as first-class context" in prompt
    assert "After you speak or complete an important action, deliberately save salient durable memory" in prompt
    assert "do not rewrite index.json with normal file tools" in prompt


def test_system_prompt_includes_persona_guidance_when_present() -> None:
    prompt = build_system_prompt(
        "세나",
        ["bash", "read", "write", "edit", "grep", "glob", "submit"],
        agent_persona="Be calm and concise.\nPrefer action over explanation.",
    )

    assert "Persona guidance for how you should generally carry yourself while thinking, speaking, and acting:" in prompt
    assert "Be calm and concise." in prompt
    assert "Prefer action over explanation." in prompt


def test_system_prompt_falls_back_to_default_name_when_blank() -> None:
    prompt = build_system_prompt("   ", ["bash", "read", "write", "edit", "grep", "glob", "submit"])

    assert prompt.splitlines()[0].startswith("You are KIRA,")
