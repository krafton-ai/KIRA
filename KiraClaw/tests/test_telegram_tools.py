from __future__ import annotations

import json
from pathlib import Path

from kiraclaw_agentd.settings import KiraClawSettings
from kiraclaw_agentd.telegram_tools import build_telegram_tools


class FakeTelegramRequester:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, method: str, payload: dict, file_path: str | None) -> dict:
        self.calls.append({"method": method, "payload": payload, "file_path": file_path})
        if method == "sendMessage":
            return {"ok": True, "result": {"message_id": 101}}
        if method == "sendDocument":
            return {
                "ok": True,
                "result": {
                    "message_id": 202,
                    "document": {
                        "file_name": Path(file_path or "").name,
                        "mime_type": "application/pdf",
                    },
                },
            }
        raise AssertionError(f"unexpected method: {method}")


def test_telegram_tools_are_gated_by_channel_enablement(tmp_path) -> None:
    disabled = KiraClawSettings(
        data_dir=tmp_path / "data-disabled",
        workspace_dir=tmp_path / "workspace-disabled",
        home_mode="modern",
        telegram_enabled=False,
        telegram_bot_token="token",
    )
    missing_token = KiraClawSettings(
        data_dir=tmp_path / "data-token",
        workspace_dir=tmp_path / "workspace-token",
        home_mode="modern",
        telegram_enabled=True,
        telegram_bot_token="",
    )
    enabled = KiraClawSettings(
        data_dir=tmp_path / "data-enabled",
        workspace_dir=tmp_path / "workspace-enabled",
        home_mode="modern",
        telegram_enabled=True,
        telegram_bot_token="token",
    )

    assert build_telegram_tools(disabled) == []
    assert build_telegram_tools(missing_token) == []
    assert [tool.name for tool in build_telegram_tools(enabled)] == [
        "telegram_send_message",
        "telegram_upload_file",
    ]


def test_telegram_send_message_and_upload_tools_use_requester(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        telegram_enabled=True,
        telegram_bot_token="token",
    )
    requester = FakeTelegramRequester()
    tools = {tool.name: tool for tool in build_telegram_tools(settings, requester=requester)}

    send_result = json.loads(
        tools["telegram_send_message"].run(chat_id="12345", text="hello", reply_to_message_id=77)
    )
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    upload_result = json.loads(
        tools["telegram_upload_file"].run(
            chat_id="12345",
            file_path=str(pdf_path),
            caption="attached",
            reply_to_message_id=77,
        )
    )

    assert send_result["success"] is True
    assert upload_result["success"] is True
    assert requester.calls == [
        {
            "method": "sendMessage",
            "payload": {
                "chat_id": "12345",
                "text": "hello",
                "reply_to_message_id": 77,
            },
            "file_path": None,
        },
        {
            "method": "sendDocument",
            "payload": {
                "chat_id": "12345",
                "caption": "attached",
                "reply_to_message_id": 77,
            },
            "file_path": str(pdf_path),
        },
    ]


def test_telegram_upload_file_reports_missing_path(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        telegram_enabled=True,
        telegram_bot_token="token",
    )
    requester = FakeTelegramRequester()
    tools = {tool.name: tool for tool in build_telegram_tools(settings, requester=requester)}

    result = json.loads(
        tools["telegram_upload_file"].run(
            chat_id="12345",
            file_path=str(Path(tmp_path) / "missing.pdf"),
        )
    )

    assert result["success"] is False
    assert "file_not_found" in result["error"]
    assert requester.calls == []
