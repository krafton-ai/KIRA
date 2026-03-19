from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any, Callable
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from krim_sdk.tools import Tool
from kiraclaw_agentd.settings import KiraClawSettings


SlackClientFactory = Callable[[], Any]


def _make_client_factory(bot_token: str) -> SlackClientFactory:
    return lambda: WebClient(token=bot_token)


def _build_result(success: bool, **payload: Any) -> str:
    body = {"success": success, **payload}
    return json.dumps(body, ensure_ascii=False, indent=2)


_SLACK_CHANNEL_ID_PATTERN = re.compile(r"^[CDG][A-Z0-9]+$")
_SLACK_USER_ID_PATTERN = re.compile(r"^U[A-Z0-9]+$")
_SLACK_CHANNEL_TOKEN_PATTERN = re.compile(r"(?<![\w/])#([a-zA-Z0-9._-]+)")
_SLACK_USER_TOKEN_PATTERN = re.compile(r"(?<![\w/])@([a-zA-Z0-9._-]+)")
_SPECIAL_MENTIONS = {"here", "channel", "everyone"}


class _SlackToolBase(Tool):
    def __init__(self, client_factory: SlackClientFactory) -> None:
        self._client_factory = client_factory

    def _client(self) -> Any:
        return self._client_factory()

    def _run_with_slack_error_boundary(self, fn: Callable[[], str]) -> str:
        try:
            return fn()
        except SlackApiError as exc:
            error_message = exc.response.get("error", str(exc))
            return _build_result(False, error=error_message)
        except Exception as exc:
            return _build_result(False, error=str(exc))

    def _resolve_channel_target(self, channel_ref: str) -> str:
        client = self._client()
        return _resolve_channel_target(client, channel_ref)

    def _format_text(self, text: str) -> str:
        client = self._client()
        return _format_slack_text(client, text)


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w.\-]+", "_", name.strip())
    return cleaned or "slack_file"


def _resolve_output_path(workspace_dir: Path, *, url_private: str, file_path: str | None, channel_id: str | None) -> Path:
    if file_path:
        candidate = Path(file_path).expanduser()
        return candidate if candidate.is_absolute() else workspace_dir / candidate

    parsed = urlparse(url_private)
    filename = _sanitize_filename(Path(unquote(parsed.path)).name)
    channel_segment = channel_id or "downloads"
    return workspace_dir / "files" / "slack" / channel_segment / filename


def _normalize_lookup_key(value: str) -> str:
    return re.sub(r"[\s._-]+", "", value.strip().lower())


def _lookup_variants(value: str) -> list[str]:
    base = value.strip()
    if not base:
        return []

    variants = {
        base,
        base.lstrip("@#"),
    }

    trimmed = base.lstrip("@#").strip()
    for suffix in ("님", "씨", "선생님"):
        if trimmed.endswith(suffix):
            variants.add(trimmed[: -len(suffix)].strip())

    return [variant for variant in variants if variant.strip()]


def _extract_channel_or_user_id(value: str) -> str | None:
    stripped = value.strip()
    channel_match = re.match(r"^<#([CDG][A-Z0-9]+)(?:\|[^>]+)?>$", stripped)
    if channel_match:
        return channel_match.group(1)
    user_match = re.match(r"^<@([U][A-Z0-9]+)>$", stripped)
    if user_match:
        return user_match.group(1)
    if _SLACK_CHANNEL_ID_PATTERN.fullmatch(stripped) or _SLACK_USER_ID_PATTERN.fullmatch(stripped):
        return stripped
    return None


def _iter_conversations(client: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        response = client.conversations_list(
            types="public_channel,private_channel,mpim,im",
            limit=1000,
            cursor=cursor,
        )
        results.extend(response.get("channels", []))
        cursor = (
            response.get("response_metadata", {}) or {}
        ).get("next_cursor") or None
        if not cursor:
            return results


def _iter_users(client: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        response = client.users_list(limit=1000, cursor=cursor)
        results.extend(response.get("members", []))
        cursor = (
            response.get("response_metadata", {}) or {}
        ).get("next_cursor") or None
        if not cursor:
            return results


def _find_channel_id_by_name(client: Any, channel_name: str) -> str | None:
    lookups = [_normalize_lookup_key(variant) for variant in _lookup_variants(channel_name)]
    lookups = [lookup for lookup in lookups if lookup]
    if not lookups:
        return None
    for channel in _iter_conversations(client):
        name = str(channel.get("name", "")).strip()
        if name and _normalize_lookup_key(name) in lookups:
            return str(channel.get("id", "")) or None
    return None


def _find_user_id_by_name(client: Any, user_name: str) -> str | None:
    lookups = [_normalize_lookup_key(variant) for variant in _lookup_variants(user_name)]
    lookups = [lookup for lookup in lookups if lookup]
    if not lookups:
        return None
    for member in _iter_users(client):
        if member.get("deleted"):
            continue
        profile = member.get("profile") or {}
        candidates = [
            str(member.get("name", "")),
            str(profile.get("display_name", "")),
            str(profile.get("real_name", "")),
            str(profile.get("display_name_normalized", "")),
            str(profile.get("real_name_normalized", "")),
        ]
        if any(candidate and _normalize_lookup_key(candidate) in lookups for candidate in candidates):
            return str(member.get("id", "")) or None
    return None


def _resolve_dm_channel_for_user(client: Any, user_id: str) -> str:
    response = client.conversations_open(users=user_id)
    channel = response.get("channel") or {}
    return str(channel.get("id", ""))


def _resolve_channel_target(client: Any, channel_ref: str) -> str:
    extracted = _extract_channel_or_user_id(channel_ref)
    if extracted:
        if _SLACK_USER_ID_PATTERN.fullmatch(extracted):
            resolved_dm = _resolve_dm_channel_for_user(client, extracted)
            return resolved_dm or extracted
        return extracted

    channel_id = _find_channel_id_by_name(client, channel_ref)
    if channel_id:
        return channel_id

    user_id = _find_user_id_by_name(client, channel_ref)
    if user_id:
        resolved_dm = _resolve_dm_channel_for_user(client, user_id)
        return resolved_dm or user_id

    return channel_ref


def _format_special_mention(name: str) -> str:
    lowered = name.lower()
    if lowered in _SPECIAL_MENTIONS:
        return f"<!{lowered}>"
    return f"@{name}"


def _format_slack_text(client: Any, text: str) -> str:
    def replace_channel(match: re.Match[str]) -> str:
        name = match.group(1)
        channel_id = _find_channel_id_by_name(client, name)
        if not channel_id:
            return match.group(0)
        return f"<#{channel_id}|{name}>"

    def replace_user(match: re.Match[str]) -> str:
        name = match.group(1)
        if name.lower() in _SPECIAL_MENTIONS:
            return _format_special_mention(name)
        user_id = _find_user_id_by_name(client, name)
        if not user_id:
            return match.group(0)
        return f"<@{user_id}>"

    formatted = _SLACK_CHANNEL_TOKEN_PATTERN.sub(replace_channel, text)
    formatted = _SLACK_USER_TOKEN_PATTERN.sub(replace_user, formatted)
    return formatted


class SlackSendMessageTool(_SlackToolBase):
    name = "slack_send_message"
    description = (
        "Send a message to any Slack channel or DM when Slack is enabled as an allowed channel."
    )
    parameters = {
        "channel_id": {
            "type": "string",
            "description": "Slack channel ID or DM ID to send to.",
        },
        "text": {
            "type": "string",
            "description": "Message text to send.",
        },
        "thread_ts": {
            "type": "string",
            "description": "Optional thread timestamp to reply in-thread.",
            "optional": True,
        },
    }

    def run(self, channel_id: str, text: str, thread_ts: str | None = None) -> str:
        def _send() -> str:
            resolved_channel = self._resolve_channel_target(channel_id)
            formatted_text = self._format_text(text)
            response = self._client().chat_postMessage(
                channel=resolved_channel,
                text=formatted_text,
                thread_ts=thread_ts,
            )
            return _build_result(
                True,
                channel=response.get("channel", resolved_channel),
                ts=response.get("ts"),
                thread_ts=response.get("message", {}).get("thread_ts", thread_ts),
            )

        return self._run_with_slack_error_boundary(_send)


class SlackReplyToThreadTool(_SlackToolBase):
    name = "slack_reply_to_thread"
    description = "Reply to an existing Slack thread."
    parameters = {
        "channel_id": {
            "type": "string",
            "description": "Slack channel ID containing the thread.",
        },
        "thread_ts": {
            "type": "string",
            "description": "Slack thread timestamp.",
        },
        "text": {
            "type": "string",
            "description": "Reply text to send.",
        },
    }

    def run(self, channel_id: str, thread_ts: str, text: str) -> str:
        def _send() -> str:
            resolved_channel = self._resolve_channel_target(channel_id)
            formatted_text = self._format_text(text)
            response = self._client().chat_postMessage(
                channel=resolved_channel,
                text=formatted_text,
                thread_ts=thread_ts,
            )
            return _build_result(
                True,
                channel=response.get("channel", resolved_channel),
                ts=response.get("ts"),
                thread_ts=response.get("message", {}).get("thread_ts", thread_ts),
            )

        return self._run_with_slack_error_boundary(_send)


class SlackAddReactionTool(_SlackToolBase):
    name = "slack_add_reaction"
    description = "Add an emoji reaction to a Slack message."
    parameters = {
        "channel_id": {
            "type": "string",
            "description": "Slack channel ID containing the message.",
        },
        "timestamp": {
            "type": "string",
            "description": "Slack message timestamp to react to.",
        },
        "reaction": {
            "type": "string",
            "description": "Emoji name without colons, for example white_check_mark or eyes.",
        },
    }

    def run(self, channel_id: str, timestamp: str, reaction: str) -> str:
        def _send() -> str:
            resolved_channel = self._resolve_channel_target(channel_id)
            self._client().reactions_add(
                channel=resolved_channel,
                timestamp=timestamp,
                name=reaction,
            )
            return _build_result(True, channel=resolved_channel, timestamp=timestamp, reaction=reaction)

        return self._run_with_slack_error_boundary(_send)


class SlackUploadFileTool(_SlackToolBase):
    name = "slack_upload_file"
    description = (
        "Upload a local file to Slack when a file already exists on disk and the user wants it sent "
        "to a Slack channel, DM, or thread."
    )
    parameters = {
        "channel_id": {
            "type": "string",
            "description": "Slack channel ID or DM ID to upload into.",
        },
        "file_path": {
            "type": "string",
            "description": "Absolute local file path to upload.",
        },
        "title": {
            "type": "string",
            "description": "Optional title shown in Slack for the uploaded file.",
            "optional": True,
        },
        "initial_comment": {
            "type": "string",
            "description": "Optional message to post with the upload.",
            "optional": True,
        },
        "thread_ts": {
            "type": "string",
            "description": "Optional thread timestamp to upload in-thread.",
            "optional": True,
        },
    }

    def run(
        self,
        channel_id: str,
        file_path: str,
        title: str | None = None,
        initial_comment: str | None = None,
        thread_ts: str | None = None,
    ) -> str:
        def _upload() -> str:
            if not os.path.isfile(file_path):
                return _build_result(False, error=f"file_not_found: {file_path}")

            filename = os.path.basename(file_path)
            resolved_channel = self._resolve_channel_target(channel_id)
            formatted_comment = self._format_text(initial_comment) if initial_comment else None
            response = self._client().files_upload_v2(
                channel=resolved_channel,
                file=file_path,
                filename=filename,
                title=title or filename,
                initial_comment=formatted_comment,
                thread_ts=thread_ts,
            )
            file_info = {}
            if isinstance(response, dict):
                file_info = response.get("file") or {}
            else:
                file_info = response.get("file", {})
            return _build_result(
                True,
                channel=resolved_channel,
                file_id=file_info.get("id"),
                title=file_info.get("title") or title or filename,
                name=file_info.get("name") or filename,
                permalink=file_info.get("permalink"),
                thread_ts=thread_ts,
            )

        return self._run_with_slack_error_boundary(_upload)


class SlackDownloadFileTool(Tool):
    name = "slack_download_file"
    description = (
        "Download a Slack file from url_private into the local workspace so you can inspect or process it."
    )
    parameters = {
        "url_private": {
            "type": "string",
            "description": "Slack file url_private or url_private_download value.",
        },
        "channel_id": {
            "type": "string",
            "description": "Optional Slack channel ID for organizing the download path.",
            "optional": True,
        },
        "file_path": {
            "type": "string",
            "description": (
                "Optional output path. Relative paths are resolved from FILESYSTEM_BASE_DIR. "
                "If omitted, the file is saved under files/slack/<channel_id or downloads>/."
            ),
            "optional": True,
        },
    }

    def __init__(self, bot_token: str, workspace_dir: Path) -> None:
        self._bot_token = bot_token
        self._workspace_dir = workspace_dir

    def run(self, url_private: str, channel_id: str | None = None, file_path: str | None = None) -> str:
        try:
            target = _resolve_output_path(
                self._workspace_dir,
                url_private=url_private,
                file_path=file_path,
                channel_id=channel_id,
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            request = Request(url_private, headers={"Authorization": f"Bearer {self._bot_token}"})
            with urlopen(request) as response:
                body = response.read()
            target.write_bytes(body)
            return _build_result(
                True,
                path=str(target),
                size_bytes=len(body),
                channel_id=channel_id,
            )
        except SlackApiError as exc:
            error_message = exc.response.get("error", str(exc))
            return _build_result(False, error=error_message)
        except Exception as exc:
            return _build_result(False, error=str(exc))


def build_slack_tools(
    settings: KiraClawSettings,
    *,
    client_factory: SlackClientFactory | None = None,
) -> list[Tool]:
    if not settings.slack_enabled or not settings.slack_bot_token:
        return []

    factory = client_factory or _make_client_factory(settings.slack_bot_token)
    tools: list[Tool] = [
        SlackSendMessageTool(factory),
        SlackReplyToThreadTool(factory),
        SlackAddReactionTool(factory),
        SlackUploadFileTool(factory),
        SlackDownloadFileTool(settings.slack_bot_token, settings.workspace_dir),
    ]
    return tools
