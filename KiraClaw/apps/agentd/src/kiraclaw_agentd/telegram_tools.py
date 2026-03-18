from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import re
from typing import Any, Callable
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

import aiohttp

from krim_sdk.tools import Tool
from kiraclaw_agentd.settings import KiraClawSettings


TelegramRequester = Callable[[str, dict[str, Any], str | None], dict[str, Any]]


def _build_result(success: bool, **payload: Any) -> str:
    body = {"success": success, **payload}
    return json.dumps(body, ensure_ascii=False, indent=2)


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w.\-]+", "_", name.strip())
    return cleaned or "telegram_file"


def _resolve_output_path(workspace_dir: Path, *, default_name: str, chat_id: str | None, file_path: str | None) -> Path:
    if file_path:
        candidate = Path(file_path).expanduser()
        return candidate if candidate.is_absolute() else workspace_dir / candidate
    chat_segment = chat_id or "downloads"
    return workspace_dir / "files" / "telegram" / chat_segment / _sanitize_filename(default_name)


def _make_requester(bot_token: str) -> TelegramRequester:
    base_url = f"https://api.telegram.org/bot{bot_token}"

    async def _request_async(method: str, payload: dict[str, Any], file_path: str | None = None) -> dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            if file_path:
                form = aiohttp.FormData()
                for key, value in payload.items():
                    if value is not None:
                        form.add_field(key, str(value))
                with open(file_path, "rb") as handle:
                    form.add_field(
                        "document",
                        handle,
                        filename=os.path.basename(file_path),
                        content_type="application/octet-stream",
                    )
                    async with session.post(f"{base_url}/{method}", data=form) as response:
                        return await response.json()

            async with session.post(f"{base_url}/{method}", json=payload) as response:
                return await response.json()

    def _request(method: str, payload: dict[str, Any], file_path: str | None = None) -> dict[str, Any]:
        return asyncio.run(_request_async(method, payload, file_path))

    return _request


class _TelegramToolBase(Tool):
    def __init__(self, requester: TelegramRequester) -> None:
        self._requester = requester

    def _run_with_error_boundary(self, fn: Callable[[], str]) -> str:
        try:
            return fn()
        except Exception as exc:
            return _build_result(False, error=str(exc))


class TelegramSendMessageTool(_TelegramToolBase):
    name = "telegram_send_message"
    description = "Send a message to any Telegram chat when Telegram is enabled as an allowed channel."
    parameters = {
        "chat_id": {
            "type": "string",
            "description": "Telegram chat ID to send to.",
        },
        "text": {
            "type": "string",
            "description": "Message text to send.",
        },
        "reply_to_message_id": {
            "type": "integer",
            "description": "Optional Telegram message ID to reply to.",
            "optional": True,
        },
    }

    def run(self, chat_id: str, text: str, reply_to_message_id: int | None = None) -> str:
        def _send() -> str:
            response = self._requester(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": text,
                    "reply_to_message_id": reply_to_message_id,
                },
                None,
            )
            if not response.get("ok"):
                return _build_result(False, error=str(response.get("description") or response))
            result = response.get("result", {})
            return _build_result(True, chat_id=chat_id, message_id=result.get("message_id"))

        return self._run_with_error_boundary(_send)


class TelegramUploadFileTool(_TelegramToolBase):
    name = "telegram_upload_file"
    description = (
        "Upload a local file to a Telegram chat when the file already exists on disk and the user wants it sent."
    )
    parameters = {
        "chat_id": {
            "type": "string",
            "description": "Telegram chat ID to upload into.",
        },
        "file_path": {
            "type": "string",
            "description": "Absolute local file path to upload.",
        },
        "caption": {
            "type": "string",
            "description": "Optional caption to send with the file.",
            "optional": True,
        },
        "reply_to_message_id": {
            "type": "integer",
            "description": "Optional Telegram message ID to reply to.",
            "optional": True,
        },
    }

    def run(
        self,
        chat_id: str,
        file_path: str,
        caption: str | None = None,
        reply_to_message_id: int | None = None,
    ) -> str:
        def _upload() -> str:
            if not os.path.isfile(file_path):
                return _build_result(False, error=f"file_not_found: {file_path}")

            response = self._requester(
                "sendDocument",
                {
                    "chat_id": chat_id,
                    "caption": caption,
                    "reply_to_message_id": reply_to_message_id,
                },
                file_path,
            )
            if not response.get("ok"):
                return _build_result(False, error=str(response.get("description") or response))
            result = response.get("result", {})
            document = result.get("document", {})
            return _build_result(
                True,
                chat_id=chat_id,
                message_id=result.get("message_id"),
                file_name=document.get("file_name") or os.path.basename(file_path),
                mime_type=document.get("mime_type"),
            )

        return self._run_with_error_boundary(_upload)


class TelegramDownloadFileTool(Tool):
    name = "telegram_download_file"
    description = "Download a Telegram file by file_id into the local workspace so you can inspect or process it."
    parameters = {
        "file_id": {
            "type": "string",
            "description": "Telegram file_id from an incoming attachment.",
        },
        "chat_id": {
            "type": "string",
            "description": "Optional chat ID for organizing the download path.",
            "optional": True,
        },
        "file_path": {
            "type": "string",
            "description": "Optional output path. Relative paths are resolved from FILESYSTEM_BASE_DIR.",
            "optional": True,
        },
    }

    def __init__(self, bot_token: str, workspace_dir: Path) -> None:
        self._bot_token = bot_token
        self._workspace_dir = workspace_dir

    def run(self, file_id: str, chat_id: str | None = None, file_path: str | None = None) -> str:
        try:
            info_request = Request(
                f"https://api.telegram.org/bot{self._bot_token}/getFile?file_id={quote(file_id, safe='')}"
            )
            with urlopen(info_request) as response:
                info = json.loads(response.read().decode("utf-8"))
            if not info.get("ok"):
                return _build_result(False, error=str(info.get("description") or info))
            result = info.get("result", {})
            telegram_path = str(result.get("file_path") or "")
            if not telegram_path:
                return _build_result(False, error="file_path_missing")

            default_name = Path(unquote(urlparse(telegram_path).path)).name or f"{file_id}.bin"
            target = _resolve_output_path(
                self._workspace_dir,
                default_name=default_name,
                chat_id=chat_id,
                file_path=file_path,
            )
            target.parent.mkdir(parents=True, exist_ok=True)

            download_request = Request(f"https://api.telegram.org/file/bot{self._bot_token}/{telegram_path}")
            with urlopen(download_request) as response:
                body = response.read()
            target.write_bytes(body)
            return _build_result(True, path=str(target), size_bytes=len(body), chat_id=chat_id, file_id=file_id)
        except Exception as exc:
            return _build_result(False, error=str(exc))


def build_telegram_tools(
    settings: KiraClawSettings,
    *,
    requester: TelegramRequester | None = None,
) -> list[Tool]:
    if not settings.telegram_enabled or not settings.telegram_bot_token:
        return []

    request_fn = requester or _make_requester(settings.telegram_bot_token)
    return [
        TelegramSendMessageTool(request_fn),
        TelegramUploadFileTool(request_fn),
        TelegramDownloadFileTool(settings.telegram_bot_token, settings.workspace_dir),
    ]
