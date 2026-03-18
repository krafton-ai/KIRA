from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
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


@dataclass
class _BufferedTelegramMessage:
    message: dict[str, Any]
    session_id: str
    chat_id: int | str
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


def _matchable_name(user: dict[str, Any]) -> str:
    parts: list[str] = []
    username = str(user.get("username") or "").strip()
    if username:
        parts.append(f"@{username}")

    first = str(user.get("first_name") or "").strip()
    last = str(user.get("last_name") or "").strip()
    full = " ".join(part for part in [first, last] if part).strip()
    if full:
        parts.append(full)

    return " ".join(parts).strip() or str(user.get("id") or "Telegram")


def _display_name(user: dict[str, Any]) -> str:
    username = str(user.get("username") or "").strip()
    if username:
        return f"@{username}"

    first = str(user.get("first_name") or "").strip()
    last = str(user.get("last_name") or "").strip()
    full = " ".join(part for part in [first, last] if part).strip()
    return full or str(user.get("id") or "Telegram")


def _is_private_chat(message: dict[str, Any]) -> bool:
    return str(message.get("chat", {}).get("type", "")) == "private"


def _clean_prompt_text(
    text: str,
    bot_username: str | None,
    *,
    mention: bool,
    agent_name: str | None = None,
) -> str:
    if mention and bot_username:
        replacement = agent_name.strip() if agent_name and agent_name.strip() else f"@{bot_username}"
        text = re.sub(fr"@{re.escape(bot_username)}\b", replacement, text, flags=re.IGNORECASE)
    return _normalize_text(text)


def _build_delivery_context_prefix(chat_id: int | str, reply_to_message_id: int | None) -> str:
    lines = [
        "Current Telegram delivery context for this conversation:",
        f"- chat_id: {chat_id}",
    ]
    if reply_to_message_id is not None:
        lines.append(f"- reply_to_message_id: {reply_to_message_id}")
    lines.extend(
        [
            "For an ordinary reply to this same conversation, prefer speak.",
            "Use Telegram tools only when you need a file upload or proactive delivery to a chat.",
            "If you do need to use a Telegram tool in this same conversation, use these exact identifiers.",
        ]
    )
    return "\n".join(lines)


def _merge_context_prefix(*parts: str | None) -> str | None:
    merged = [part.strip() for part in parts if part and part.strip()]
    if not merged:
        return None
    return "\n\n".join(merged)


def _base_message_text(message: dict[str, Any]) -> str:
    return str(message.get("text") or message.get("caption") or "")


def _extract_attachment_metadata(message: dict[str, Any]) -> list[dict[str, str]]:
    extracted: list[dict[str, str]] = []
    document = message.get("document")
    if isinstance(document, dict):
        extracted.append(
            {
                "name": str(document.get("file_name") or "document"),
                "kind": "document",
                "mime_type": str(document.get("mime_type") or "unknown"),
                "file_id": str(document.get("file_id") or ""),
                "size": str(document.get("file_size") or ""),
            }
        )

    video = message.get("video")
    if isinstance(video, dict):
        extracted.append(
            {
                "name": str(video.get("file_name") or "video.mp4"),
                "kind": "video",
                "mime_type": str(video.get("mime_type") or "video/mp4"),
                "file_id": str(video.get("file_id") or ""),
                "size": str(video.get("file_size") or ""),
            }
        )

    audio = message.get("audio")
    if isinstance(audio, dict):
        extracted.append(
            {
                "name": str(audio.get("file_name") or audio.get("title") or "audio"),
                "kind": "audio",
                "mime_type": str(audio.get("mime_type") or "audio/mpeg"),
                "file_id": str(audio.get("file_id") or ""),
                "size": str(audio.get("file_size") or ""),
            }
        )

    voice = message.get("voice")
    if isinstance(voice, dict):
        extracted.append(
            {
                "name": "voice.ogg",
                "kind": "voice",
                "mime_type": str(voice.get("mime_type") or "audio/ogg"),
                "file_id": str(voice.get("file_id") or ""),
                "size": str(voice.get("file_size") or ""),
            }
        )

    photo = message.get("photo")
    if isinstance(photo, list) and photo:
        largest = photo[-1]
        if isinstance(largest, dict):
            extracted.append(
                {
                    "name": str(largest.get("file_unique_id") or largest.get("file_id") or "photo") + ".jpg",
                    "kind": "photo",
                    "mime_type": "image/jpeg",
                    "file_id": str(largest.get("file_id") or ""),
                    "size": str(largest.get("file_size") or ""),
                }
            )
    return extracted


def _format_attachment_prompt(files: list[dict[str, str]]) -> str:
    if not files:
        return ""
    lines = [
        "Attached Telegram files:",
        "Use telegram_download_file with the provided file_id if you need the actual file contents.",
    ]
    for file_info in files:
        details = [file_info["kind"], file_info["mime_type"]]
        if file_info["size"]:
            details.append(f"size_bytes={file_info['size']}")
        line = f"- {file_info['name']} ({', '.join(part for part in details if part)})"
        if file_info["file_id"]:
            line += f" [file_id: {file_info['file_id']}]"
        lines.append(line)
    return "\n".join(lines)


def _build_message_prompt(message: dict[str, Any], bot_username: str | None, *, mention: bool, agent_name: str | None = None) -> str:
    text = _clean_prompt_text(
        _base_message_text(message),
        bot_username,
        mention=mention,
        agent_name=agent_name,
    )
    attachments = _format_attachment_prompt(_extract_attachment_metadata(message))
    return _merge_context_prefix(text, attachments) or ""


def _is_human_message(message: dict[str, Any]) -> bool:
    user = message.get("from", {})
    return bool(_base_message_text(message) or _extract_attachment_metadata(message)) and not bool(user.get("is_bot"))


def _session_id_from_message(message: dict[str, Any]) -> str:
    chat_id = message.get("chat", {}).get("id", "unknown")
    if _is_private_chat(message):
        return f"telegram:dm:{chat_id}"

    thread = (
        message.get("message_thread_id")
        or message.get("reply_to_message", {}).get("message_id")
        or "main"
    )
    return f"telegram:{chat_id}:{thread}"


def _reply_to_message_id(message: dict[str, Any]) -> int | None:
    if _is_private_chat(message):
        return None
    try:
        return int(message.get("message_id"))
    except (TypeError, ValueError):
        return None


def _debounce_key_for_message(session_id: str, message: dict[str, Any]) -> str:
    if _is_private_chat(message):
        return f"{session_id}:{message.get('from', {}).get('id', '')}"
    return session_id


def _merge_prompt_text(items: list[_BufferedTelegramMessage]) -> str:
    if not items:
        return ""
    if _is_private_chat(items[-1].message):
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


class TelegramGateway:
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
        self._session: aiohttp.ClientSession | None = None
        self._update_offset: int | None = None
        self._debouncer = KeyedDebouncer[_BufferedTelegramMessage](
            delay_seconds=debounce_seconds,
            on_flush=self._flush_debounced_messages,
            label="telegram",
        )
        if self.configured:
            self.state = "configured"

    @property
    def configured(self) -> bool:
        return bool(self.settings.telegram_enabled and self.settings.telegram_bot_token)

    @property
    def _base_url(self) -> str:
        return f"https://api.telegram.org/bot{self.settings.telegram_bot_token}"

    async def start(self) -> None:
        if not self.configured:
            self.state = "not_configured"
            return

        self.state = "starting"
        self.last_error = None
        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
            await self._validate_token()
            await self._prime_offset()
            if self._runner_task is None or self._runner_task.done():
                self._runner_task = asyncio.create_task(self._poll_loop(), name="telegram-gateway")
                self._runner_task.add_done_callback(self._handle_runner_done)
            self.state = "running"
        except Exception as exc:
            self.state = "failed"
            self.last_error = str(exc)
            logger.exception("Telegram gateway failed to start")

    async def stop(self) -> None:
        await self._debouncer.stop()
        if self._runner_task and not self._runner_task.done():
            self._runner_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._runner_task
        self._runner_task = None

        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

        self.state = "configured" if self.configured else "not_configured"

    async def send_message(self, chat_id: int | str, text: str, reply_to_message_id: int | None = None) -> None:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        await self._api("sendMessage", payload)

    async def _validate_token(self) -> None:
        response = await self._api("getMe")
        result = response["result"]
        self.identity = {
            "id": result.get("id", 0),
            "username": result.get("username", ""),
            "first_name": result.get("first_name", ""),
        }

    async def _prime_offset(self) -> None:
        response = await self._api("getUpdates", {"timeout": 0, "limit": 100})
        updates = response.get("result", [])
        if updates:
            self._update_offset = int(updates[-1]["update_id"]) + 1

    def _handle_runner_done(self, task: asyncio.Task[None]) -> None:
        if task.cancelled():
            if self.state != "stopped":
                self.state = "stopped"
            return

        error = task.exception()
        if error is not None:
            self.state = "failed"
            self.last_error = str(error)
            logger.error("Telegram gateway stopped with an error: %s", error)
        elif self.state != "stopped":
            self.state = "stopped"

    async def _poll_loop(self) -> None:
        while True:
            try:
                response = await self._api(
                    "getUpdates",
                    {
                        "timeout": 25,
                        "offset": self._update_offset,
                        "allowed_updates": ["message"],
                    },
                )
                self.last_error = None
                self.state = "running"
                for update in response.get("result", []):
                    self._update_offset = int(update["update_id"]) + 1
                    message = update.get("message")
                    if message:
                        await self._handle_message(message)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.last_error = str(exc) or exc.__class__.__name__
                logger.warning("Telegram polling failed and will retry: %s", self.last_error)
                await asyncio.sleep(2)

    async def _handle_message(self, message: dict[str, Any]) -> None:
        if not _is_human_message(message):
            return
        bot_username = str(self.identity.get("username") or "")
        text = _base_message_text(message)
        mention = bool(bot_username and f"@{bot_username.lower()}" in text.lower())

        user = message.get("from", {})
        user_name = _display_name(user)
        matchable_name = _matchable_name(user)
        if not _is_authorized_user_name(matchable_name, self.settings.telegram_allowed_names):
            logger.info("Ignoring unauthorized Telegram user: %s", matchable_name)
            return

        prompt = _build_message_prompt(
            message,
            bot_username,
            mention=mention,
            agent_name=self.settings.agent_name,
        )
        if not prompt:
            return

        session_id = _session_id_from_message(message)
        chat_id = message.get("chat", {}).get("id")
        reply_to_message_id = _reply_to_message_id(message)
        await self._debouncer.enqueue(
            _debounce_key_for_message(session_id, message),
            _BufferedTelegramMessage(
                message=message,
                session_id=session_id,
                chat_id=chat_id,
                reply_to_message_id=reply_to_message_id,
                prompt=prompt,
                user_name=user_name,
                mention=mention,
            ),
        )

    async def _flush_debounced_messages(self, items: list[_BufferedTelegramMessage]) -> None:
        last = items[-1]
        merged_prompt = _merge_prompt_text(items)
        await self._run_for_message(
            message=last.message,
            session_id=last.session_id,
            chat_id=last.chat_id,
            reply_to_message_id=last.reply_to_message_id,
            prompt=merged_prompt or last.prompt,
            user_name=last.user_name,
            mention=last.mention,
        )

    async def _run_for_message(
        self,
        *,
        message: dict[str, Any],
        session_id: str,
        chat_id: int | str,
        reply_to_message_id: int | None,
        prompt: str,
        user_name: str,
        mention: bool,
    ) -> None:
        metadata = {
            "source": "telegram-dm" if _is_private_chat(message) else "telegram-group",
            "chat_id": str(chat_id),
            "user": str(message.get("from", {}).get("id", "")),
            "user_name": user_name,
        }
        context_prefix = _build_delivery_context_prefix(chat_id, reply_to_message_id)
        record = await self.session_manager.run(
            session_id=session_id,
            prompt=prompt,
            context_prefix=context_prefix,
            metadata=metadata,
        )
        await self._publish_result(chat_id, reply_to_message_id, record)

    async def _publish_result(self, chat_id: int | str, reply_to_message_id: int | None, record: RunRecord) -> None:
        if record.state == "failed":
            text = f"Run failed.\n{record.error or 'Unknown error'}"
            await self.send_message(chat_id, text, reply_to_message_id=reply_to_message_id)
            return

        spoken_messages = list(record.result.spoken_messages) if record.result else []
        if spoken_messages:
            rendered_messages = list(spoken_messages)
            rendered_messages[-1] = append_tool_summary(rendered_messages[-1], record.result.tool_events)
            for text in rendered_messages:
                await self.send_message(chat_id, text, reply_to_message_id=reply_to_message_id)
            return

        return

    async def _api(self, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        async with self._session.post(f"{self._base_url}/{method}", json=payload or {}) as response:
            data = await response.json()
        if not data.get("ok"):
            raise RuntimeError(str(data.get("description") or data))
        return data
