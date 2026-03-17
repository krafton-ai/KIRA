from __future__ import annotations

import pytest

from kiraclaw_agentd.engine import (
    KiraClawEngine,
    _compose_prompt,
    _configure_tools,
    create_model,
    list_available_skills,
)
from kiraclaw_agentd.settings import KiraClawSettings


def test_engine_requires_claude_credentials(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        provider="claude",
    )
    settings.ensure_directories()

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        KiraClawEngine(settings).run("Say hi.")


def test_openai_default_model_is_gpt_5_3_codex(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    model = create_model("openai", None, max_tokens=2048)

    assert model.model == "gpt-5.3-codex"


def test_compose_prompt_includes_recent_history_when_present() -> None:
    prompt = _compose_prompt(
        "what about yesterday?",
        "Recent conversation history:\nUser: hello\nAssistant: hi",
        "Relevant long-term memory:\nUser prefers concise answers.",
    )

    assert "<retrieved_memory>" in prompt
    assert "User prefers concise answers." in prompt
    assert "<recent_conversation>" in prompt
    assert "User: hello" in prompt
    assert "<current_user_request>\nwhat about yesterday?\n</current_user_request>" in prompt


def test_configure_tools_adds_skill_tool_only_when_skills_exist(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        skills_enabled=True,
    )
    settings.ensure_directories()

    tools, skill_rows = _configure_tools(settings)

    assert "skill" not in [tool.name for tool in tools]
    assert skill_rows == []


def test_configure_tools_discovers_workspace_skill_md(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        skills_enabled=True,
    )
    settings.ensure_directories()

    skill_dir = settings.workspace_dir / "skills" / "jira-reader"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: jira-reader\ndescription: Read Jira carefully\n---\nUse Jira tools.\n",
        encoding="utf-8",
    )

    tools, skill_rows = _configure_tools(settings)

    assert "skill" in [tool.name for tool in tools]
    assert skill_rows == [
        {
            "id": "jira-reader",
            "name": "jira-reader",
            "description": "Read Jira carefully",
            "path": str(skill_dir),
            "source": "workspace",
        }
    ]


def test_list_available_skills_reports_workspace_source(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        skills_enabled=True,
    )
    settings.ensure_directories()

    skill_dir = settings.workspace_dir / "skills" / "pptx"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: pptx\ndescription: Work with presentations\n---\nUse office files.\n",
        encoding="utf-8",
    )

    rows = list_available_skills(settings)

    assert rows == [
        {
            "id": "pptx",
            "name": "pptx",
            "description": "Work with presentations",
            "path": str(skill_dir),
            "source": "workspace",
        }
    ]


def test_list_available_skills_ignores_global_kira_skill_dir(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        skills_enabled=True,
    )
    settings.ensure_directories()

    global_skill_dir = settings.data_dir / "skills" / "ignored"
    global_skill_dir.mkdir(parents=True, exist_ok=True)
    (global_skill_dir / "SKILL.md").write_text(
        "---\nname: ignored\ndescription: Should not be loaded\n---\nIgnore me.\n",
        encoding="utf-8",
    )

    rows = list_available_skills(settings)

    assert rows == []
