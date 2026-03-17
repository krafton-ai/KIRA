from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
import logging
import re
from typing import Any

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from kiraclaw_agentd.channel_debounce import KeyedDebouncer
from kiraclaw_agentd.session_manager import RunRecord, SessionManager
from kiraclaw_agentd.settings import KiraClawSettings

logger = logging.getLogger(__name__)
_APP_MENTION_RE = re.compile(r"<@[^>]+>")
_CHANNEL_DEBOUNCE_SECONDS = 5.0


@dataclass
class _BufferedSlackEvent:
    event: dict[str, Any]
    session_id: str
    channel: str
    reply_thread_ts: str | None
    user: str
    user_name: str
    prompt: str
    mention: bool
    client: Any


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _parse_allowed_names(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def _is_authorized_user_name(user_name: str, allowed_names: str) -> bool:
    tokens = _parse_allowed_names(allowed_names)
    if not tokens:
        return True

    normalized_user_name = user_name.strip().lower()
    compact_user_name = "".join(normalized_user_name.split())
    for token in tokens:
        normalized_token = token.lower()
        compact_token = "".join(normalized_token.split())
        if normalized_token in normalized_user_name or compact_token in compact_user_name:
            return True
    return False


def _clean_prompt_text(text: str, *, mention: bool) -> str:
    if mention:
        text = _APP_MENTION_RE.sub(" ", text)
    return _normalize_text(text)


def _build_delivery_context_prefix(channel: str, thread_ts: str | None) -> str:
    lines = [
        "Current Slack delivery context for this conversation:",
        f"- channel_id: {channel}",
    ]
    if thread_ts:
        lines.append(f"- thread_ts: {thread_ts}")
    lines.extend(
        [
            "If you need to send a Slack message, reply, reaction, or file back into this same conversation,",
            "use these exact identifiers with the Slack tools.",
        ]
    )
    return "\n".join(lines)


def _merge_context_prefix(*parts: str | None) -> str | None:
    merged = [part.strip() for part in parts if part and part.strip()]
    if not merged:
        return None
    return "\n\n".join(merged)


def _strip_bot_mention(text: str, bot_user_id: str | None) -> str:
    if not bot_user_id:
        return _normalize_text(text)
    return _normalize_text(text.replace(f"<@{bot_user_id}>", " "))


def _ts_value(value: str | None) -> float:
    try:
        return float(value or "0")
    except (TypeError, ValueError):
        return 0.0


def _is_dm(event: dict[str, Any]) -> bool:
    return event.get("channel_type") == "im"


def _session_id_from_event(event: dict[str, Any]) -> str:
    channel = event.get("channel", "unknown")
    if _is_dm(event):
        return f"slack:dm:{channel}"
    thread = event.get("thread_ts") or event.get("ts") or "root"
    return f"slack:{channel}:{thread}"


def _reply_thread_ts_from_event(event: dict[str, Any]) -> str | None:
    if _is_dm(event):
        return None
    return event.get("thread_ts") or event.get("ts")


def _should_handle_message(event: dict[str, Any]) -> bool:
    if event.get("subtype"):
        return False
    if event.get("bot_id"):
        return False
    return _is_dm(event)


class SlackGateway:
    def __init__(
        self,
        session_manager: SessionManager,
        settings: KiraClawSettings,
        *,
        debounce_seconds: float = _CHANNEL_DEBOUNCE_SECONDS,
    ) -> None:
        self.session_manager = session_manager
        self.settings = settings
        self.app: AsyncApp | None = None
        self.handler: AsyncSocketModeHandler | None = None
        self._runner_task: asyncio.Task[None] | None = None
        self.state: str = "not_configured"
        self.last_error: str | None = None
        self.identity: dict[str, str] = {}
        self._user_name_cache: dict[str, str] = {}
        self.socket_mode_validated: bool = False
        self._debouncer = KeyedDebouncer[_BufferedSlackEvent](
            delay_seconds=debounce_seconds,
            on_flush=self._flush_debounced_events,
            label="slack",
        )
        if self.configured:
            self.state = "configured"
            self._ensure_app()

    @property
    def configured(self) -> bool:
        return bool(
            self.settings.slack_enabled
            and self.settings.slack_bot_token
            and self.settings.slack_app_token
            and self.settings.slack_signing_secret
        )

    def _register_handlers(self) -> None:
        if self.app is None:
            return

        @self.app.event("app_mention")
        async def on_app_mention(event, client, logger):
            logger.info("Slack app mention received: channel=%s user=%s", event.get("channel"), event.get("user"))
            await self._schedule_event(event, client, logger, mention=True)

        @self.app.event("message")
        async def on_message(event, client, logger):
            if not _should_handle_message(event):
                return
            logger.info("Slack DM received: channel=%s user=%s", event.get("channel"), event.get("user"))
            await self._schedule_event(event, client, logger, mention=False)

    def _ensure_app(self) -> None:
        if self.app is not None:
            return
        self.app = AsyncApp(
            token=self.settings.slack_bot_token,
            signing_secret=self.settings.slack_signing_secret,
        )
        self._register_handlers()

    async def _validate_tokens(self) -> None:
        if self.app is None:
            raise RuntimeError("Slack app is not available")

        auth = await self.app.client.auth_test()
        self.identity = {
            "team": auth.get("team", ""),
            "team_id": auth.get("team_id", ""),
            "user": auth.get("user", ""),
            "user_id": auth.get("user_id", ""),
        }

        app_client = AsyncWebClient(token=self.settings.slack_app_token)
        socket_mode_resp = await app_client.api_call(api_method="apps.connections.open")
        self.socket_mode_validated = bool(socket_mode_resp.get("ok"))
        if not self.socket_mode_validated:
            raise RuntimeError(socket_mode_resp.get("error", "Socket Mode validation failed"))

    def _handle_runner_done(self, task: asyncio.Task[None]) -> None:
        if task.cancelled():
            if self.state != "stopped":
                self.state = "stopped"
            return

        error = task.exception()
        if error is not None:
            self.state = "failed"
            self.last_error = str(error)
            logger.error("Slack gateway stopped with an error: %s", error)
        elif self.state != "stopped":
            self.state = "stopped"

    async def start(self) -> None:
        if not self.configured:
            self.state = "not_configured"
            logger.info("Slack gateway is not configured; skipping startup")
            return
        self._ensure_app()
        if self.app is None:
            logger.warning("Slack gateway requested to start without an app")
            self.state = "failed"
            self.last_error = "Slack app is not available"
            return
        self.state = "starting"
        self.last_error = None
        self.socket_mode_validated = False
        try:
            await self._validate_tokens()
            if self.handler is None:
                self.handler = AsyncSocketModeHandler(self.app, self.settings.slack_app_token)
            if self._runner_task is None or self._runner_task.done():
                self._runner_task = asyncio.create_task(self.handler.start_async(), name="slack-socket-mode")
                self._runner_task.add_done_callback(self._handle_runner_done)
            self.state = "running"
            logger.info("Slack gateway started")
        except Exception as error:
            self.state = "failed"
            self.last_error = str(error)
            logger.exception("Slack gateway failed to start")

    async def stop(self) -> None:
        await self._debouncer.stop()
        if self._runner_task and not self._runner_task.done():
            self._runner_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._runner_task
        if self.handler is not None:
            with contextlib.suppress(Exception):
                await self.handler.close_async()
            self.handler = None
        if self.configured:
            self.state = "configured"
        else:
            self.state = "not_configured"

    async def send_message(self, channel: str, text: str, thread_ts: str | None = None) -> None:
        if not self.configured:
            raise RuntimeError("Slack gateway is not configured")
        self._ensure_app()
        if self.app is None:
            raise RuntimeError("Slack app is not available")
        await self.app.client.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts,
        )

    async def _get_user_name(self, client, user_id: str) -> str:
        cached = self._user_name_cache.get(user_id)
        if cached:
            return cached

        try:
            response = await client.users_info(user=user_id)
            if response.get("ok"):
                user = response.get("user", {})
                profile = user.get("profile", {})
                user_name = (
                    profile.get("display_name")
                    or user.get("real_name")
                    or profile.get("real_name")
                    or user.get("name")
                    or user_id
                )
                self._user_name_cache[user_id] = user_name
                return user_name
        except Exception as exc:
            logger.warning("Failed to fetch Slack user info for %s: %s", user_id, exc)

        return user_id

    async def _schedule_event(self, event: dict[str, Any], client, logger, mention: bool) -> None:
        text = event.get("text", "").strip()
        if not text:
            return

        session_id = _session_id_from_event(event)
        channel = event["channel"]
        reply_thread_ts = _reply_thread_ts_from_event(event)
        user = event.get("user", "unknown")
        user_name = await self._get_user_name(client, user)
        if not _is_authorized_user_name(user_name, self.settings.slack_allowed_names):
            logger.info("Ignoring unauthorized Slack user: user=%s name=%s", user, user_name)
            return
        cleaned_text = _clean_prompt_text(text, mention=mention)
        if not cleaned_text:
            return
        logger.info(
            "Queueing Slack run with debounce: session_id=%s channel=%s user=%s name=%s mention=%s dm=%s",
            session_id,
            channel,
            user,
            user_name,
            mention,
            _is_dm(event),
        )

        await self._debouncer.enqueue(
            f"{session_id}:{user}",
            _BufferedSlackEvent(
                event=event,
                session_id=session_id,
                channel=channel,
                reply_thread_ts=reply_thread_ts,
                user=user,
                user_name=user_name,
                prompt=cleaned_text,
                mention=mention,
                client=client,
            ),
        )

    async def _flush_debounced_events(self, items: list[_BufferedSlackEvent]) -> None:
        last = items[-1]
        merged_prompt = "\n".join(item.prompt for item in items if item.prompt.strip())
        excluded_timestamps = {
            str(item.event.get("ts"))
            for item in items
            if item.event.get("ts")
        }
        await self._run_for_event(
            event=last.event,
            session_id=last.session_id,
            channel=last.channel,
            reply_thread_ts=last.reply_thread_ts,
            user=last.user,
            user_name=last.user_name,
            prompt=merged_prompt or last.prompt,
            mention=last.mention,
            client=last.client,
            excluded_timestamps=excluded_timestamps,
        )

    async def _run_for_event(
        self,
        *,
        event: dict[str, Any],
        session_id: str,
        channel: str,
        reply_thread_ts: str | None,
        user: str,
        user_name: str,
        prompt: str,
        mention: bool,
        client,
        excluded_timestamps: set[str] | None = None,
    ) -> None:
        metadata = {
            "channel": channel,
            "thread_ts": reply_thread_ts,
            "user": user,
            "user_name": user_name,
            "source": "slack-app-mention" if mention else "slack-dm",
        }
        delivery_context = _build_delivery_context_prefix(channel, reply_thread_ts)
        context_prefix = delivery_context
        if not self.session_manager.get_session_records(session_id):
            bootstrap_context = await self._build_slack_bootstrap_context(
                client=client,
                event=event,
                excluded_timestamps=excluded_timestamps,
            )
            context_prefix = _merge_context_prefix(delivery_context, bootstrap_context)
        record = await self.session_manager.run(
            session_id=session_id,
            prompt=prompt,
            context_prefix=context_prefix,
            metadata=metadata,
        )
        await self._publish_result(client, channel, reply_thread_ts, record)

    async def _publish_result(self, client, channel: str, thread_ts: str | None, record: RunRecord) -> None:
        if record.state == "failed":
            text = f"Run failed.\n{record.error or 'Unknown error'}"
        else:
            text = (record.result.final_response if record.result else "") or "Run completed without a final response."
        await client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=text)

    async def _build_slack_bootstrap_context(
        self,
        client,
        event: dict[str, Any],
        excluded_timestamps: set[str] | None = None,
    ) -> str | None:
        try:
            messages = await self._fetch_bootstrap_messages(client, event, excluded_timestamps=excluded_timestamps)
        except Exception as exc:
            logger.warning("Failed to fetch Slack history bootstrap: %s", exc)
            return None

        if not messages:
            return None

        lines = [
            "Slack conversation history from this thread/channel before the current request:",
        ]
        for message in messages:
            speaker = await self._speaker_for_message(client, message)
            cleaned = _strip_bot_mention(message.get("text", ""), self.identity.get("user_id"))
            if not cleaned:
                continue
            lines.append(f"{speaker}: {cleaned}")

        return "\n".join(lines) if len(lines) > 1 else None

    async def _fetch_bootstrap_messages(
        self,
        client,
        event: dict[str, Any],
        *,
        excluded_timestamps: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        excluded = excluded_timestamps or set()
        current_ts = event.get("ts")
        if _is_dm(event):
            response = await client.conversations_history(
                channel=event["channel"],
                limit=8,
                latest=current_ts,
                inclusive=False,
            )
            messages = response.get("messages", [])
            messages.reverse()
            return [
                message
                for message in messages
                if message.get("text") and str(message.get("ts")) not in excluded
            ]

        thread_ts = event.get("thread_ts")
        if not thread_ts:
            return []

        response = await client.conversations_replies(
            channel=event["channel"],
            ts=thread_ts,
        )
        current_value = _ts_value(current_ts)
        return [
            message
            for message in response.get("messages", [])
            if (
                message.get("text")
                and _ts_value(message.get("ts")) < current_value
                and str(message.get("ts")) not in excluded
            )
        ]

    async def _speaker_for_message(self, client, message: dict[str, Any]) -> str:
        user_id = message.get("user")
        if user_id:
            if user_id == self.identity.get("user_id"):
                return self.settings.agent_name
            return await self._get_user_name(client, user_id)

        if message.get("bot_id") or message.get("subtype") == "bot_message":
            return self.settings.agent_name

        return "Slack"
