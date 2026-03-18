import json
from pathlib import Path

import kiraclaw_agentd.discord_tools as discord_tools_module
from kiraclaw_agentd.discord_tools import build_discord_tools
from kiraclaw_agentd.settings import KiraClawSettings


def _payload(raw: str) -> dict:
    return json.loads(raw)


def test_discord_tools_are_gated_by_channel_enablement(tmp_path) -> None:
    disabled = KiraClawSettings(
        data_dir=tmp_path / "data-disabled",
        workspace_dir=tmp_path / "workspace-disabled",
        home_mode="modern",
        discord_enabled=False,
        discord_bot_token="token",
        slack_enabled=False,
    )
    missing_token = KiraClawSettings(
        data_dir=tmp_path / "data-missing",
        workspace_dir=tmp_path / "workspace-missing",
        home_mode="modern",
        discord_enabled=True,
        discord_bot_token="",
        slack_enabled=False,
    )
    enabled = KiraClawSettings(
        data_dir=tmp_path / "data-enabled",
        workspace_dir=tmp_path / "workspace-enabled",
        home_mode="modern",
        discord_enabled=True,
        discord_bot_token="token",
        slack_enabled=False,
    )

    assert build_discord_tools(disabled) == []
    assert build_discord_tools(missing_token) == []
    assert [tool.name for tool in build_discord_tools(enabled)] == [
        "discord_send_message",
        "discord_upload_file",
        "discord_download_attachment",
    ]


def test_discord_send_message_and_upload_tools_use_requester(tmp_path) -> None:
    requests: list[dict] = []

    def requester(method, channel_id, payload, file_path=None):
        requests.append(
            {
                "method": method,
                "channel_id": channel_id,
                "payload": payload,
                "file_path": file_path,
            }
        )
        return {
            "status": 200,
            "body": {
                "id": "msg-1",
                "attachments": [{"filename": "report.pdf", "url": "https://discord.example/report.pdf"}],
            },
        }

    file_path = tmp_path / "report.pdf"
    file_path.write_text("pdf", encoding="utf-8")

    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        discord_enabled=True,
        discord_bot_token="token",
        slack_enabled=False,
    )
    tools = {tool.name: tool for tool in build_discord_tools(settings, requester=requester)}

    send_result = _payload(tools["discord_send_message"].run(channel_id="12345", text="hello", reply_to_message_id=77))
    upload_result = _payload(
        tools["discord_upload_file"].run(
            channel_id="12345",
            file_path=str(file_path),
            caption="here",
            reply_to_message_id=88,
        )
    )

    assert send_result["success"] is True
    assert send_result["channel_id"] == "12345"
    assert upload_result["success"] is True
    assert upload_result["file_name"] == "report.pdf"
    assert requests[0]["payload"]["message_reference"] == {"message_id": "77"}
    assert requests[1]["file_path"] == str(file_path)


def test_discord_upload_file_reports_missing_path(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        discord_enabled=True,
        discord_bot_token="token",
        slack_enabled=False,
    )
    tools = {tool.name: tool for tool in build_discord_tools(settings, requester=lambda *_args, **_kwargs: {})}

    result = _payload(
        tools["discord_upload_file"].run(
            channel_id="12345",
            file_path=str(tmp_path / "missing.pdf"),
        )
    )

    assert result["success"] is False
    assert "file_not_found" in result["error"]


def test_discord_download_attachment_saves_into_workspace(tmp_path, monkeypatch) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        discord_enabled=True,
        discord_bot_token="token",
        slack_enabled=False,
    )
    tools = {tool.name: tool for tool in build_discord_tools(settings, requester=lambda *_args, **_kwargs: {})}

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return b"hello from discord"

    def fake_urlopen(request):
        assert request.full_url == "https://cdn.discordapp.com/attachments/C1/F1/report.pdf"
        assert request.headers["Authorization"] == "Bot token"
        return _FakeResponse()

    monkeypatch.setattr(discord_tools_module, "urlopen", fake_urlopen)
    result = _payload(
        tools["discord_download_attachment"].run(
            url="https://cdn.discordapp.com/attachments/C1/F1/report.pdf",
            channel_id="12345",
        )
    )

    assert result["success"] is True
    saved = Path(result["path"])
    assert saved == settings.workspace_dir / "files" / "discord" / "12345" / "report.pdf"
    assert saved.read_bytes() == b"hello from discord"
