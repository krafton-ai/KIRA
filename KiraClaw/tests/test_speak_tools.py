from __future__ import annotations

import json

from kiraclaw_agentd.settings import KiraClawSettings
from kiraclaw_agentd.speak_tools import build_speak_tools


def test_speak_tool_is_always_available(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )

    tools = build_speak_tools(settings)

    assert [tool.name for tool in tools] == ["speak"]


def test_speak_tool_records_spoken_messages_in_tool_context(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )
    spoken_messages: list[str] = []
    tools = {
        tool.name: tool
        for tool in build_speak_tools(
            settings,
            tool_context={"__spoken_messages__": spoken_messages},
        )
    }

    result = json.loads(tools["speak"].run(text="외부에 말할 내용"))

    assert result["success"] is True
    assert spoken_messages == ["외부에 말할 내용"]
