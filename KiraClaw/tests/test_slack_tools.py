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
