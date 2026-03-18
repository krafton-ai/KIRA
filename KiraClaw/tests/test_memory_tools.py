from __future__ import annotations

import json

from kiraclaw_agentd.memory_tools import build_memory_tools
from kiraclaw_agentd.settings import KiraClawSettings


def test_memory_tools_are_gated_by_memory_enablement(tmp_path) -> None:
    disabled = KiraClawSettings(
        data_dir=tmp_path / "data-disabled",
        workspace_dir=tmp_path / "workspace-disabled",
        home_mode="modern",
        slack_enabled=False,
        memory_enabled=False,
    )
    enabled = KiraClawSettings(
        data_dir=tmp_path / "data-enabled",
        workspace_dir=tmp_path / "workspace-enabled",
        home_mode="modern",
        slack_enabled=False,
        memory_enabled=True,
    )

    assert build_memory_tools(disabled) == []
    assert [tool.name for tool in build_memory_tools(enabled)] == [
        "memory_index_search",
        "memory_index_save",
        "memory_search",
        "memory_save",
    ]


def test_memory_search_and_save_tools_use_current_session_context(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        memory_enabled=True,
    )
    settings.ensure_directories()

    tools = {
        tool.name: tool
        for tool in build_memory_tools(
            settings,
            tool_context={
                "session_id": "slack:dm:D123",
                "source": "slack-dm",
                "user": "U123",
                "user_name": "Jiho Jeon",
                "channel": "D123",
            },
        )
    }

    save_result = json.loads(
        tools["memory_save"].run(note="Remember that Jiho prefers PDF attachments for reports.")
    )
    search_result = json.loads(
        tools["memory_search"].run(query="Jiho PDF attachments")
    )

    assert save_result["success"] is True
    assert save_result["session_id"] == "slack:dm:D123"
    assert save_result["count"] >= 1
    assert search_result["success"] is True
    assert search_result["session_id"] == "slack:dm:D123"
    assert search_result["count"] >= 1
    assert any("PDF attachments" in entry["content"] for entry in search_result["entries"])


def test_memory_index_tools_can_search_and_sync_index(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        memory_enabled=True,
    )
    settings.ensure_directories()

    memory_file = settings.memory_dir / "projects" / "moltbook.md"
    memory_file.parent.mkdir(parents=True, exist_ok=True)
    memory_file.write_text("# Moltbook\n\nAgent profile setup notes.\n", encoding="utf-8")

    tools = {
        tool.name: tool
        for tool in build_memory_tools(
            settings,
            tool_context={
                "session_id": "desktop:local",
                "source": "api",
            },
        )
    }

    save_result = json.loads(
        tools["memory_index_save"].run(
            path=str(memory_file),
            summary="Agent profile setup notes for Moltbook.",
            title="Moltbook Profile",
            category="projects",
            tags="agent, moltbook",
        )
    )
    search_result = json.loads(
        tools["memory_index_search"].run(
            query="moltbook profile",
        )
    )

    assert save_result["success"] is True
    assert save_result["entry"]["path"] == "projects/moltbook.md"
    assert search_result["success"] is True
    assert search_result["count"] >= 1
    assert search_result["entries"][0]["path"] == "projects/moltbook.md"
