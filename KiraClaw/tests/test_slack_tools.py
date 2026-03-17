from __future__ import annotations

import json

from kiraclaw_agentd.settings import KiraClawSettings
from kiraclaw_agentd.slack_tools import build_slack_tools


class FakeSlackClient:
    def __init__(self) -> None:
        self.messages: list[dict] = []
        self.reactions: list[dict] = []

    def chat_postMessage(self, **kwargs):
        self.messages.append(kwargs)
        return {
            "ok": True,
            "channel": kwargs["channel"],
            "ts": "123.456",
            "message": {"thread_ts": kwargs.get("thread_ts")},
        }

    def reactions_add(self, **kwargs):
        self.reactions.append(kwargs)
        return {"ok": True}


def test_slack_tools_are_gated_by_slack_channel_enablement(tmp_path) -> None:
    disabled = KiraClawSettings(
        data_dir=tmp_path / "data-disabled",
        workspace_dir=tmp_path / "workspace-disabled",
        home_mode="modern",
        slack_enabled=False,
        slack_bot_token="xoxb-token",
    )
    missing_token = KiraClawSettings(
        data_dir=tmp_path / "data-token",
        workspace_dir=tmp_path / "workspace-token",
        home_mode="modern",
        slack_enabled=True,
        slack_bot_token="",
    )
    enabled = KiraClawSettings(
        data_dir=tmp_path / "data-enabled",
        workspace_dir=tmp_path / "workspace-enabled",
        home_mode="modern",
        slack_enabled=True,
        slack_bot_token="xoxb-token",
    )

    assert build_slack_tools(disabled) == []
    assert build_slack_tools(missing_token) == []
    assert [tool.name for tool in build_slack_tools(enabled)] == [
        "slack_send_message",
        "slack_reply_to_thread",
        "slack_add_reaction",
    ]


def test_slack_send_message_and_reaction_tools_use_client_factory(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=True,
        slack_bot_token="xoxb-token",
    )
    client = FakeSlackClient()
    tools = {tool.name: tool for tool in build_slack_tools(settings, client_factory=lambda: client)}

    send_result = json.loads(
        tools["slack_send_message"].run(channel_id="C123", text="hello", thread_ts="111.222")
    )
    reaction_result = json.loads(
        tools["slack_add_reaction"].run(channel_id="C123", timestamp="111.222", reaction="eyes")
    )

    assert send_result["success"] is True
    assert client.messages == [{"channel": "C123", "text": "hello", "thread_ts": "111.222"}]
    assert reaction_result["success"] is True
    assert client.reactions == [{"channel": "C123", "timestamp": "111.222", "name": "eyes"}]
