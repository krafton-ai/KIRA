from __future__ import annotations

import json
from pathlib import Path

from kiraclaw_agentd.settings import KiraClawSettings
import kiraclaw_agentd.slack_tools as slack_tools_module
from kiraclaw_agentd.slack_tools import build_slack_tools


class FakeSlackClient:
    def __init__(self) -> None:
        self.messages: list[dict] = []
        self.reactions: list[dict] = []
        self.uploads: list[dict] = []
        self.opened_dms: list[dict] = []

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

    def files_upload_v2(self, **kwargs):
        self.uploads.append(kwargs)
        return {
            "ok": True,
            "file": {
                "id": "F123",
                "title": kwargs.get("title"),
                "name": kwargs.get("filename"),
                "permalink": "https://slack.example/file/F123",
            },
        }

    def conversations_list(self, **kwargs):
        return {
            "channels": [
                {"id": "C123", "name": "general"},
                {"id": "C999", "name": "project-updates"},
            ]
        }

    def users_list(self, **kwargs):
        return {
            "members": [
                {
                    "id": "U123",
                    "name": "jiho",
                    "profile": {
                        "display_name": "jiho",
                        "real_name": "Jiho Jeon",
                        "display_name_normalized": "jiho",
                        "real_name_normalized": "Jiho Jeon",
                    },
                },
                {
                    "id": "U999",
                    "name": "sena",
                    "profile": {
                        "display_name": "sena",
                        "real_name": "Sena Bot",
                        "display_name_normalized": "sena",
                        "real_name_normalized": "Sena Bot",
                    },
                },
            ]
        }

    def conversations_open(self, **kwargs):
        self.opened_dms.append(kwargs)
        user_id = kwargs["users"]
        return {"channel": {"id": f"D-{user_id}"}}


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
        "slack_upload_file",
        "slack_download_file",
    ]


def test_slack_send_message_reaction_and_upload_tools_use_client_factory(tmp_path) -> None:
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
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    upload_result = json.loads(
        tools["slack_upload_file"].run(
            channel_id="C123",
            file_path=str(pdf_path),
            title="report",
            initial_comment="attached",
            thread_ts="111.222",
        )
    )

    assert send_result["success"] is True
    assert client.messages == [{"channel": "C123", "text": "hello", "thread_ts": "111.222"}]
    assert reaction_result["success"] is True
    assert client.reactions == [{"channel": "C123", "timestamp": "111.222", "name": "eyes"}]
    assert upload_result["success"] is True
    assert client.uploads == [
        {
            "channel": "C123",
            "file": str(pdf_path),
            "filename": "report.pdf",
            "title": "report",
            "initial_comment": "attached",
            "thread_ts": "111.222",
        }
    ]


def test_slack_send_message_resolves_channel_name_and_mentions(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=True,
        slack_bot_token="xoxb-token",
    )
    client = FakeSlackClient()
    tools = {tool.name: tool for tool in build_slack_tools(settings, client_factory=lambda: client)}

    result = json.loads(
        tools["slack_send_message"].run(
            channel_id="#general",
            text="Hey @jiho please check #project-updates",
        )
    )

    assert result["success"] is True
    assert client.messages == [
        {
            "channel": "C123",
            "text": "Hey <@U123> please check <#C999|project-updates>",
            "thread_ts": None,
        }
    ]


def test_slack_send_message_can_open_dm_from_user_name(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=True,
        slack_bot_token="xoxb-token",
    )
    client = FakeSlackClient()
    tools = {tool.name: tool for tool in build_slack_tools(settings, client_factory=lambda: client)}

    result = json.loads(
        tools["slack_send_message"].run(
            channel_id="@jiho",
            text="hello",
        )
    )

    assert result["success"] is True
    assert client.opened_dms == [{"users": "U123"}]
    assert client.messages == [{"channel": "D-U123", "text": "hello", "thread_ts": None}]


def test_slack_send_message_can_open_dm_from_korean_honorific_name(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=True,
        slack_bot_token="xoxb-token",
    )
    client = FakeSlackClient()
    client.users_list = lambda **kwargs: {
        "members": [
            {
                "id": "U777",
                "name": "jiho",
                "profile": {
                    "display_name": "전지호",
                    "real_name": "전지호",
                    "display_name_normalized": "전지호",
                    "real_name_normalized": "전지호",
                },
            }
        ]
    }
    tools = {tool.name: tool for tool in build_slack_tools(settings, client_factory=lambda: client)}

    result = json.loads(
        tools["slack_send_message"].run(
            channel_id="전지호님",
            text="hello",
        )
    )

    assert result["success"] is True
    assert client.opened_dms == [{"users": "U777"}]
    assert client.messages == [{"channel": "D-U777", "text": "hello", "thread_ts": None}]


def test_slack_upload_file_reports_missing_path(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=True,
        slack_bot_token="xoxb-token",
    )
    client = FakeSlackClient()
    tools = {tool.name: tool for tool in build_slack_tools(settings, client_factory=lambda: client)}

    result = json.loads(
        tools["slack_upload_file"].run(
            channel_id="C123",
            file_path=str(Path(tmp_path) / "missing.pdf"),
        )
    )

    assert result["success"] is False
    assert "file_not_found" in result["error"]
    assert client.uploads == []


def test_slack_download_file_saves_into_workspace(tmp_path, monkeypatch) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=True,
        slack_bot_token="xoxb-token",
    )
    client = FakeSlackClient()
    tools = {tool.name: tool for tool in build_slack_tools(settings, client_factory=lambda: client)}

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return b"hello from slack"

    def fake_urlopen(request):
        assert request.full_url == "https://files.slack.com/files-pri/T1-F1/report.pdf"
        assert request.headers["Authorization"] == "Bearer xoxb-token"
        return _FakeResponse()

    monkeypatch.setattr(slack_tools_module, "urlopen", fake_urlopen)
    result = json.loads(
        tools["slack_download_file"].run(
            url_private="https://files.slack.com/files-pri/T1-F1/report.pdf",
            channel_id="C123",
        )
    )

    assert result["success"] is True
    saved = Path(result["path"])
    assert saved == settings.workspace_dir / "files" / "slack" / "C123" / "report.pdf"
    assert saved.read_bytes() == b"hello from slack"
