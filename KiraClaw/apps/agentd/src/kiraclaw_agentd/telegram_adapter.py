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


def _clean_prompt_text(text: str, bot_username: str | None, *, mention: bool) -> str:
    if mention and bot_username:
        text = re.sub(fr"@{re.escape(bot_username)}\b", " ", text, flags=re.IGNORECASE)
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
            "If you need to send a Telegram message or file back into this same conversation,",
            "use these exact identifiers with the Telegram tools.",
        ]
    )
    return "\n".join(lines)


def _merge_context_prefix(*parts: str | None) -> str | None:
    merged = [part.strip() for part in parts if part and part.strip()]
    if not merged:
        return None
    return "\n\n".join(merged)


def _should_handle_message(message: dict[str, Any], bot_username: str | None, bot_id: int | None) -> bool:
    if not message.get("text"):
        return False

    user = message.get("from", {})
    if user.get("is_bot"):
        return False

    if _is_private_chat(message):
        return True

    if bot_id and message.get("reply_to_message", {}).get("from", {}).get("id") == bot_id:
        return True

    if bot_username and f"@{bot_username.lower()}" in str(message.get("text", "")).lower():
        return True

    return False


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
        bot_username = str(self.identity.get("username") or "")
        bot_id = int(self.identity.get("id") or 0) or None
        if not _should_handle_message(message, bot_username, bot_id):
            return

        user = message.get("from", {})
        user_name = _display_name(user)
        matchable_name = _matchable_name(user)
        if not _is_authorized_user_name(matchable_name, self.settings.telegram_allowed_names):
            logger.info("Ignoring unauthorized Telegram user: %s", matchable_name)
            return

        mention = not _is_private_chat(message)
        prompt = _clean_prompt_text(str(message.get("text", "")), bot_username, mention=mention)
        if not prompt:
            return

        session_id = _session_id_from_message(message)
        chat_id = message.get("chat", {}).get("id")
        reply_to_message_id = _reply_to_message_id(message)
        await self._debouncer.enqueue(
            f"{session_id}:{user.get('id', '')}",
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
        merged_prompt = "\n".join(item.prompt for item in items if item.prompt.strip())
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
            "source": "telegram-group" if mention else "telegram-dm",
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
        else:
            text = (record.result.final_response if record.result else "") or "Run completed without a final response."
        await self.send_message(chat_id, text, reply_to_message_id=reply_to_message_id)

    async def _api(self, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        async with self._session.post(f"{self._base_url}/{method}", json=payload or {}) as response:
            data = await response.json()
        if not data.get("ok"):
            raise RuntimeError(str(data.get("description") or data))
        return data
