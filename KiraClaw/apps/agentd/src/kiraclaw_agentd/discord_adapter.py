from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
import importlib
import logging
import re
from typing import Any

import aiohttp

from kiraclaw_agentd.channel_debounce import KeyedDebouncer
from kiraclaw_agentd.session_manager import RunRecord, SessionManager
from kiraclaw_agentd.settings import KiraClawSettings
from kiraclaw_agentd.tool_event_summary import append_tool_summary

logger = logging.getLogger(__name__)
_CHANNEL_DEBOUNCE_SECONDS = 5.0
_DISCORD_MESSAGE_URL = "https://discord.com/api/v10/channels/{channel_id}/messages"


@dataclass
class _BufferedDiscordMessage:
    message: Any
    session_id: str
    channel_id: int | str
    reply_to_message_id: int | None
    prompt: str
    user_name: str
    mention: bool


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _parse_allowed_names(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def _is_authorized_user_name(user_name: str, allowed_names: str) -> bool:
    tokens = _parse_allowed_names(allowed_names)
    if not tokens:
        return True

    normalized = user_name.strip().lower()
    compact_name = "".join(normalized.split())
    for token in tokens:
        normalized_token = token.lower()
        compact_token = "".join(normalized_token.split())
        if normalized_token in normalized or compact_token in compact_name:
            return True
    return False


def _display_name(user: Any) -> str:
    for attr in ("display_name", "global_name", "name"):
        value = str(getattr(user, attr, "") or "").strip()
        if value:
            return value
    return str(getattr(user, "id", "Discord"))


def _matchable_name(user: Any) -> str:
    parts: list[str] = []
    name = str(getattr(user, "name", "") or "").strip()
    if name:
        parts.append(f"@{name}")
    for attr in ("display_name", "global_name", "name"):
        value = str(getattr(user, attr, "") or "").strip()
        if value and value not in parts and f"@{value}" not in parts:
            parts.append(value)
    return " ".join(parts).strip() or str(getattr(user, "id", "Discord"))


def _is_private_message(message: Any) -> bool:
    return getattr(message, "guild", None) is None


def _session_id_from_message(message: Any) -> str:
    channel_id = getattr(getattr(message, "channel", None), "id", "unknown")
    if _is_private_message(message):
        return f"discord:dm:{channel_id}"
    return f"discord:{channel_id}:main"


def _reply_to_message_id(message: Any) -> int | None:
    try:
        return int(getattr(message, "id", 0)) or None
    except (TypeError, ValueError):
        return None


def _debounce_key_for_message(session_id: str, message: Any) -> str:
    if _is_private_message(message):
        return f"{session_id}:{getattr(getattr(message, 'author', None), 'id', '')}"
    return session_id


def _clean_prompt_text(
    text: str,
    bot_user_id: int | str | None,
    *,
    mention: bool,
    agent_name: str | None = None,
) -> str:
    if mention and bot_user_id:
        replacement = agent_name.strip() if agent_name and agent_name.strip() else "KiraClaw"
        text = re.sub(fr"<@!?{re.escape(str(bot_user_id))}>", replacement, text)
    return _normalize_text(text)


def _build_delivery_context_prefix(channel_id: int | str, reply_to_message_id: int | None) -> str:
    lines = [
        "Current Discord delivery context for this conversation:",
        f"- channel_id: {channel_id}",
    ]
    if reply_to_message_id is not None:
        lines.append(f"- reply_to_message_id: {reply_to_message_id}")
    lines.extend(
        [
            "For an ordinary reply to this same conversation, prefer speak.",
            "Use Discord tools only when you need a file upload or proactive delivery to another channel.",
            "If you do need to use a Discord tool in this same conversation, use these exact identifiers.",
        ]
    )
    return "\n".join(lines)


def _merge_context_prefix(*parts: str | None) -> str | None:
    merged = [part.strip() for part in parts if part and part.strip()]
    if not merged:
        return None
    return "\n\n".join(merged)


def _extract_attachment_metadata(message: Any) -> list[dict[str, str]]:
    extracted: list[dict[str, str]] = []
    for attachment in list(getattr(message, "attachments", []) or []):
        extracted.append(
            {
                "name": str(getattr(attachment, "filename", "") or getattr(attachment, "id", "attachment")),
                "content_type": str(getattr(attachment, "content_type", "") or "unknown"),
                "size": str(getattr(attachment, "size", "") or ""),
                "url": str(getattr(attachment, "url", "") or ""),
            }
        )
    return extracted


def _format_attachment_prompt(files: list[dict[str, str]]) -> str:
    if not files:
        return ""
    lines = [
        "Attached Discord files:",
        "Use discord_download_attachment with the provided url if you need the actual file contents.",
    ]
    for file_info in files:
        details = [file_info["content_type"]]
        if file_info["size"]:
            details.append(f"size_bytes={file_info['size']}")
        line = f"- {file_info['name']}"
        if details:
            line += f" ({', '.join(part for part in details if part)})"
        if file_info["url"]:
            line += f" [url: {file_info['url']}]"
        lines.append(line)
    return "\n".join(lines)


def _build_message_prompt(
    message: Any,
    bot_user_id: int | str | None,
    *,
    mention: bool,
    agent_name: str | None = None,
) -> str:
    text = _clean_prompt_text(
        str(getattr(message, "content", "") or ""),
        bot_user_id,
        mention=mention,
        agent_name=agent_name,
    )
    attachments = _format_attachment_prompt(_extract_attachment_metadata(message))
    return _merge_context_prefix(text, attachments) or ""


def _merge_prompt_text(items: list[_BufferedDiscordMessage]) -> str:
    if not items:
        return ""
    if _is_private_message(items[-1].message):
        return "\n".join(item.prompt for item in items if item.prompt.strip())

    lines = ["Recent room messages:"]
    for item in items:
        text = item.prompt.strip()
        if not text:
            continue
        text_lines = text.splitlines()
        lines.append(f"- {item.user_name}: {text_lines[0]}")
        for continuation in text_lines[1:]:
            lines.append(f"  {continuation}")
    return "\n".join(lines) if len(lines) > 1 else ""


def _is_human_message(message: Any) -> bool:
    author = getattr(message, "author", None)
    if author is None or bool(getattr(author, "bot", False)):
        return False
    return bool(str(getattr(message, "content", "") or "").strip() or _extract_attachment_metadata(message))


class DiscordGateway:
    def __init__(
        self,
        session_manager: SessionManager,
        settings: KiraClawSettings,
        *,
        debounce_seconds: float = _CHANNEL_DEBOUNCE_SECONDS,
    ) -> None:
        self.session_manager = session_manager
        self.settings = settings
        self.state: str = "not_configured"
        self.last_error: str | None = None
        self.identity: dict[str, str | int] = {}
        self._runner_task: asyncio.Task[None] | None = None
        self._client: Any = None
        self._http_session: aiohttp.ClientSession | None = None
        self._ready_event = asyncio.Event()
        self._debouncer = KeyedDebouncer[_BufferedDiscordMessage](
            delay_seconds=debounce_seconds,
            on_flush=self._flush_debounced_messages,
            label="discord",
        )
        if self.configured:
            self.state = "configured"

    @property
    def configured(self) -> bool:
        return bool(self.settings.discord_enabled and self.settings.discord_bot_token)

    async def start(self) -> None:
        if not self.configured:
            self.state = "not_configured"
            return

        self.state = "starting"
        self.last_error = None
        self._ready_event.clear()

        try:
            if self._client is None:
                self._client = self._create_client()
            if self._runner_task is None or self._runner_task.done():
                self._runner_task = asyncio.create_task(
                    self._client.start(self.settings.discord_bot_token),
                    name="discord-gateway",
                )
                self._runner_task.add_done_callback(self._handle_runner_done)

            for _ in range(200):
                if self._ready_event.is_set():
                    self.state = "running"
                    return
                if self._runner_task.done():
                    error = self._runner_task.exception()
                    raise error or RuntimeError("Discord gateway stopped during startup")
                await asyncio.sleep(0.1)

            raise RuntimeError("Discord gateway did not become ready in time")
        except Exception as exc:
            self.state = "failed"
            self.last_error = str(exc)
            logger.exception("Discord gateway failed to start")

    async def stop(self) -> None:
        await self._debouncer.stop()

        if self._client is not None:
            with contextlib.suppress(Exception):
                await self._client.close()

        if self._runner_task and not self._runner_task.done():
            self._runner_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._runner_task
        self._runner_task = None

        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
        self._http_session = None

        if self.configured:
            self.state = "configured"
        else:
            self.state = "not_configured"

    async def send_message(
        self,
        channel_id: int | str,
        text: str,
        reply_to_message_id: int | None = None,
    ) -> None:
        payload: dict[str, Any] = {"content": text}
        if reply_to_message_id is not None:
            payload["message_reference"] = {"message_id": str(reply_to_message_id)}
            payload["allowed_mentions"] = {"replied_user": False}
        await self._api("POST", _DISCORD_MESSAGE_URL.format(channel_id=channel_id), json_payload=payload)

    def _create_client(self) -> Any:
        discord = importlib.import_module("discord")
        intents = discord.Intents.default()
        intents.message_content = True

        gateway = self

        class _DiscordClient(discord.Client):
            async def on_ready(self) -> None:
                user = self.user
                gateway.identity = {
                    "id": int(getattr(user, "id", 0)),
                    "name": str(getattr(user, "name", "") or ""),
                    "display_name": str(getattr(user, "display_name", "") or getattr(user, "name", "") or ""),
                }
                gateway.last_error = None
                gateway.state = "running"
                gateway._ready_event.set()

            async def on_message(self, message: Any) -> None:
                await gateway._handle_message(message)

        return _DiscordClient(intents=intents)

    def _handle_runner_done(self, task: asyncio.Task[None]) -> None:
        if task.cancelled():
            if self.state != "stopped":
                self.state = "stopped"
            return

        error = task.exception()
        if error is not None:
            self.state = "failed"
            self.last_error = str(error)
            logger.error("Discord gateway stopped with an error: %s", error)
        elif self.state != "stopped":
            self.state = "stopped"

    async def _handle_message(self, message: Any) -> None:
        if not _is_human_message(message):
            return

        bot_user_id = self.identity.get("id")
        raw_mentions = [int(value) for value in list(getattr(message, "raw_mentions", []) or []) if str(value).isdigit()]
        mention = bool(bot_user_id and int(bot_user_id) in raw_mentions)

        user = getattr(message, "author", None)
        user_name = _display_name(user)
        if not _is_authorized_user_name(_matchable_name(user), self.settings.discord_allowed_names):
            logger.info("Ignoring unauthorized Discord user: %s", user_name)
            return

        prompt = _build_message_prompt(message, bot_user_id, mention=mention, agent_name=self.settings.agent_name)
        if not prompt:
            return

        session_id = _session_id_from_message(message)
        channel_id = getattr(getattr(message, "channel", None), "id", "unknown")
        reply_to_message_id = _reply_to_message_id(message)
        await self._debouncer.enqueue(
            _debounce_key_for_message(session_id, message),
            _BufferedDiscordMessage(
                message=message,
                session_id=session_id,
                channel_id=channel_id,
                reply_to_message_id=reply_to_message_id,
                prompt=prompt,
                user_name=user_name,
                mention=mention,
            ),
        )

    async def _flush_debounced_messages(self, items: list[_BufferedDiscordMessage]) -> None:
        last = items[-1]
        merged_prompt = _merge_prompt_text(items)
        await self._run_for_message(
            message=last.message,
            session_id=last.session_id,
            channel_id=last.channel_id,
            reply_to_message_id=last.reply_to_message_id,
            prompt=merged_prompt or last.prompt,
            user_name=last.user_name,
            mention=last.mention,
        )

    async def _run_for_message(
        self,
        *,
        message: Any,
        session_id: str,
        channel_id: int | str,
        reply_to_message_id: int | None,
        prompt: str,
        user_name: str,
        mention: bool,
    ) -> None:
        metadata = {
            "source": "discord-dm" if _is_private_message(message) else "discord-group",
            "channel": str(channel_id),
            "channel_id": str(channel_id),
            "user": str(getattr(getattr(message, "author", None), "id", "")),
            "user_name": user_name,
        }
        context_prefix = _build_delivery_context_prefix(channel_id, reply_to_message_id)
        record = await self.session_manager.run(
            session_id=session_id,
            prompt=prompt,
            context_prefix=context_prefix,
            metadata=metadata,
        )
        await self._publish_result(channel_id, reply_to_message_id, record)

    async def _publish_result(
        self,
        channel_id: int | str,
        reply_to_message_id: int | None,
        record: RunRecord,
    ) -> None:
        if record.state == "failed":
            text = f"Run failed.\n{record.error or 'Unknown error'}"
            await self.send_message(channel_id, text, reply_to_message_id=reply_to_message_id)
            return

        spoken_messages = list(record.result.spoken_messages) if record.result else []
        if spoken_messages:
            rendered_messages = list(spoken_messages)
            rendered_messages[-1] = append_tool_summary(rendered_messages[-1], record.result.tool_events)
            for text in rendered_messages:
                await self.send_message(channel_id, text, reply_to_message_id=reply_to_message_id)

    async def _api(
        self,
        method: str,
        url: str,
        *,
        json_payload: dict[str, Any] | None = None,
        form_data: aiohttp.FormData | None = None,
    ) -> dict[str, Any]:
        if self._http_session is None or self._http_session.closed:
            headers = {"Authorization": f"Bot {self.settings.discord_bot_token}"}
            self._http_session = aiohttp.ClientSession(headers=headers)

        request_kwargs: dict[str, Any] = {}
        if json_payload is not None:
            request_kwargs["json"] = json_payload
        if form_data is not None:
            request_kwargs["data"] = form_data

        async with self._http_session.request(method, url, **request_kwargs) as response:
            data = await response.json()
        if response.status >= 400:
            raise RuntimeError(str(data))
        return data
