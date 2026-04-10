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
from kiraclaw_agentd.observer_runtime import (
    cancel_heartbeat_task,
    maybe_route_inflight_message,
    run_heartbeat_loop,
)
from kiraclaw_agentd.observer_service import InflightMessageContext, ObserverService
from kiraclaw_agentd.session_manager import RunRecord, SessionManager
from kiraclaw_agentd.settings import KiraClawSettings
from kiraclaw_agentd.tool_event_summary import append_response_trace, build_terminal_fallback_response

logger = logging.getLogger(__name__)
_APP_MENTION_RE = re.compile(r"<@[^>]+>")
_USER_MENTION_RE = re.compile(r"<@([A-Z0-9]+)>")
_CHANNEL_MENTION_RE = re.compile(r"<#([CDG][A-Z0-9]+)(?:\|([^>]+))?>")
_PRIVATE_CHANNEL_DEBOUNCE_SECONDS = 5.0
_GROUP_CHANNEL_DEBOUNCE_SECONDS = 8.0
_SLACK_HISTORY_LIMIT = 20


@dataclass
class _BufferedSlackEvent:
    event: dict[str, Any]
    session_id: str
    channel: str
    reply_thread_ts: str | None
    user: str
    user_name: str
    prompt: str
    reference_context: str | None
    inbound: InflightMessageContext
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


def _clean_prompt_text(
    text: str,
    bot_user_id: str | None,
    *,
    mention: bool,
    agent_name: str | None = None,
) -> str:
    if mention and bot_user_id:
        replacement = f" {agent_name.strip()} " if agent_name and agent_name.strip() else " KiraClaw "
        text = re.sub(fr"<@{re.escape(bot_user_id)}>", replacement, text)
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
            "For an ordinary reply to this same conversation, prefer speak.",
            "Use Slack tools only when you need a file upload, reaction, thread-specific control, or proactive delivery.",
            "If you do need to use a Slack tool in this same conversation, use these exact identifiers.",
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


def _build_inflight_context(event: dict[str, Any], *, user_name: str, mention: bool) -> InflightMessageContext:
    is_private = _is_dm(event)
    return InflightMessageContext(
        source="slack-dm" if is_private else "slack-group",
        mention=mention,
        is_private=is_private,
        user_name=user_name,
    )


def _session_id_from_event(event: dict[str, Any]) -> str:
    channel = event.get("channel", "unknown")
    if _is_dm(event):
        return f"slack:dm:{channel}"
    thread = event.get("thread_ts") or "main"
    return f"slack:{channel}:{thread}"


def _reply_thread_ts_from_event(event: dict[str, Any]) -> str | None:
    if _is_dm(event):
        return None
    return event.get("thread_ts") or event.get("ts")


def _debounce_key_for_event(session_id: str, event: dict[str, Any], user: str) -> str:
    if _is_dm(event):
        return f"{session_id}:{user}"
    return session_id


def _merge_prompt_text(items: list[_BufferedSlackEvent]) -> str:
    if not items:
        return ""
    if _is_dm(items[-1].event):
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


def _is_human_message_event(event: dict[str, Any]) -> bool:
    subtype = str(event.get("subtype") or "")
    if event.get("bot_id"):
        return False
    if subtype and subtype != "file_share":
        return False
    return bool(event.get("user"))


def _extract_file_metadata(event: dict[str, Any]) -> list[dict[str, str]]:
    extracted: list[dict[str, str]] = []
    for raw_file in event.get("files") or []:
        if not isinstance(raw_file, dict):
            continue
        name = str(raw_file.get("name") or raw_file.get("title") or raw_file.get("id") or "unnamed")
        mimetype = str(raw_file.get("mimetype") or raw_file.get("filetype") or "unknown")
        url_private = str(raw_file.get("url_private") or raw_file.get("url_private_download") or "").strip()
        size = raw_file.get("size")
        size_text = str(size) if size is not None else ""
        extracted.append(
            {
                "name": name,
                "mimetype": mimetype,
                "url_private": url_private,
                "size": size_text,
            }
        )
    return extracted


def _format_file_prompt(files: list[dict[str, str]]) -> str:
    if not files:
        return ""

    lines = [
        "Attached Slack files:",
        "Use slack_download_file with the provided url_private if you need the actual file contents.",
    ]
    for file_info in files:
        detail_parts = [file_info["mimetype"]]
        if file_info["size"]:
            detail_parts.append(f"size_bytes={file_info['size']}")
        detail = ", ".join(part for part in detail_parts if part)
        line = f"- {file_info['name']}"
        if detail:
            line += f" ({detail})"
        if file_info["url_private"]:
            line += f" [url_private: {file_info['url_private']}]"
        lines.append(line)
    return "\n".join(lines)


def _build_event_prompt(
    event: dict[str, Any],
    *,
    mention: bool,
    agent_name: str | None = None,
    bot_user_id: str | None = None,
) -> str:
    text = _clean_prompt_text(
        str(event.get("text") or ""),
        bot_user_id,
        mention=mention,
        agent_name=agent_name,
    )
    files_block = _format_file_prompt(_extract_file_metadata(event))
    return _merge_context_prefix(text, files_block) or ""


class SlackGateway:
    def __init__(
        self,
        session_manager: SessionManager,
        settings: KiraClawSettings,
        *,
        observer_service: ObserverService | None = None,
        debounce_seconds: float | None = None,
        group_debounce_seconds: float | None = None,
    ) -> None:
        self.session_manager = session_manager
        self.settings = settings
        self.observer_service = observer_service
        self._private_debounce_seconds = (
            _PRIVATE_CHANNEL_DEBOUNCE_SECONDS if debounce_seconds is None else float(debounce_seconds)
        )
        self._group_debounce_seconds = (
            _GROUP_CHANNEL_DEBOUNCE_SECONDS
            if group_debounce_seconds is None and debounce_seconds is None
            else self._private_debounce_seconds if group_debounce_seconds is None else float(group_debounce_seconds)
        )
        self.app: AsyncApp | None = None
        self.handler: AsyncSocketModeHandler | None = None
        self._runner_task: asyncio.Task[None] | None = None
        self._recovery_task: asyncio.Task[None] | None = None
        self._stopping: bool = False
        self._reconnect_delay_seconds: float = 2.0
        self.state: str = "not_configured"
        self.last_error: str | None = None
        self.identity: dict[str, str] = {}
        self._user_name_cache: dict[str, str] = {}
        self._channel_name_cache: dict[str, str] = {}
        self._retrieve_client: AsyncWebClient | None = None
        self.socket_mode_validated: bool = False
        self._debouncer = KeyedDebouncer[_BufferedSlackEvent](
            delay_seconds=self._private_debounce_seconds,
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
            if not _is_human_message_event(event):
                return
            logger.info("Slack app mention received: channel=%s user=%s", event.get("channel"), event.get("user"))
            await self._schedule_event(event, client, logger, mention=True)

        @self.app.event("message")
        async def on_message(event, client, logger):
            if not _is_human_message_event(event):
                return
            logger.info("Slack message received: channel=%s user=%s", event.get("channel"), event.get("user"))
            await self._schedule_event(
                event,
                client,
                logger,
                mention=bool(_APP_MENTION_RE.search(str(event.get("text", "")))),
            )

    def _ensure_app(self) -> None:
        if self.app is not None:
            return
        self.app = AsyncApp(
            token=self.settings.slack_bot_token,
            signing_secret=self.settings.slack_signing_secret,
        )
        self._register_handlers()

    async def _reset_socket_runtime(self) -> None:
        runner = self._runner_task
        self._runner_task = None
        if runner is not None and not runner.done():
            runner.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await runner

        if self.handler is not None:
            with contextlib.suppress(Exception):
                await self.handler.close_async()
            self.handler = None

        self.app = None
        self.socket_mode_validated = False

    async def _recover_after_failure(self) -> None:
        await asyncio.sleep(max(0.1, float(self._reconnect_delay_seconds)))
        if self._stopping or not self.configured:
            return
        logger.info("Attempting to recover Slack gateway socket mode connection")
        await self.start()

    def _schedule_recovery(self) -> None:
        if self._stopping or not self.configured:
            return
        if self._recovery_task is not None and not self._recovery_task.done():
            return
        self.state = "reconnecting"
        self._recovery_task = asyncio.create_task(
            self._recover_after_failure(),
            name="slack-socket-mode-recovery",
        )

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
        if task is not self._runner_task:
            return
        self._runner_task = None
        if task.cancelled():
            if self._stopping:
                self.state = "stopped"
            elif self.configured:
                self.state = "configured"
            else:
                self.state = "stopped"
            return

        error = task.exception()
        if error is not None:
            self.state = "failed"
            self.last_error = str(error)
            logger.error("Slack gateway stopped with an error: %s", error)
            self._schedule_recovery()
        elif not self._stopping:
            self.state = "stopped"
            self._schedule_recovery()

    async def start(self) -> None:
        if not self.configured:
            self.state = "not_configured"
            logger.info("Slack gateway is not configured; skipping startup")
            return
        self._stopping = False
        if self._recovery_task is not None and not self._recovery_task.done():
            self._recovery_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._recovery_task
        self._recovery_task = None
        await self._reset_socket_runtime()
        self._ensure_app()
        if self.app is None:
            logger.warning("Slack gateway requested to start without an app")
            self.state = "failed"
            self.last_error = "Slack app is not available"
            return
        self.state = "starting"
        self.last_error = None
        try:
            await self._validate_tokens()
            self.handler = AsyncSocketModeHandler(self.app, self.settings.slack_app_token)
            self._runner_task = asyncio.create_task(self.handler.start_async(), name="slack-socket-mode")
            self._runner_task.add_done_callback(self._handle_runner_done)
            self.state = "running"
            logger.info("Slack gateway started")
        except Exception as error:
            self.state = "failed"
            self.last_error = str(error)
            logger.exception("Slack gateway failed to start")

    async def stop(self) -> None:
        self._stopping = True
        await self._debouncer.stop()
        if self._recovery_task is not None and not self._recovery_task.done():
            self._recovery_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._recovery_task
        self._recovery_task = None
        await self._reset_socket_runtime()
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

    async def _get_channel_name(self, client, channel_id: str) -> str:
        cached = self._channel_name_cache.get(channel_id)
        if cached:
            return cached

        try:
            response = await client.conversations_info(channel=channel_id)
            if response.get("ok"):
                channel = response.get("channel") or {}
                name = str(channel.get("name") or channel_id).strip() or channel_id
                self._channel_name_cache[channel_id] = name
                return name
        except Exception as exc:
            logger.warning("Failed to fetch Slack channel info for %s: %s", channel_id, exc)

        return channel_id

    async def _schedule_event(self, event: dict[str, Any], client, logger, mention: bool) -> None:
        if not _is_human_message_event(event):
            return

        session_id = _session_id_from_event(event)
        channel = event["channel"]
        reply_thread_ts = _reply_thread_ts_from_event(event)
        user = event.get("user", "unknown")
        user_name = await self._get_user_name(client, user)
        if not _is_authorized_user_name(user_name, self.settings.slack_allowed_names):
            logger.info("Ignoring unauthorized Slack user: user=%s name=%s", user, user_name)
            return
        raw_text = str(event.get("text") or "")
        prompt_text = await self._resolve_user_mentions_in_text(client, raw_text)
        reference_context = await self._build_delivery_reference_context(client, raw_text)
        prompt = _build_event_prompt(
            {**event, "text": prompt_text},
            mention=mention,
            agent_name=self.settings.agent_name,
            bot_user_id=self.identity.get("user_id"),
        )
        if not prompt:
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

        if await self._maybe_handle_inflight_event(
            session_id=session_id,
            prompt=prompt,
            channel=channel,
            reply_thread_ts=reply_thread_ts,
            client=client,
            inbound=_build_inflight_context(event, user_name=user_name, mention=mention),
        ):
            return

        await self._debouncer.enqueue_with_delay(
            _debounce_key_for_event(session_id, event, user),
            _BufferedSlackEvent(
                event=event,
                session_id=session_id,
                channel=channel,
                reply_thread_ts=reply_thread_ts,
                user=user,
                user_name=user_name,
                prompt=prompt,
                reference_context=reference_context,
                inbound=_build_inflight_context(event, user_name=user_name, mention=mention),
                client=client,
            ),
            delay_seconds=self._debounce_seconds_for_event(event),
        )

    def _debounce_seconds_for_event(self, event: dict[str, Any]) -> float:
        return self._private_debounce_seconds if _is_dm(event) else self._group_debounce_seconds

    async def _flush_debounced_events(self, items: list[_BufferedSlackEvent]) -> None:
        last = items[-1]
        merged_prompt = _merge_prompt_text(items)
        merged_reference_context = _merge_context_prefix(
            *dict.fromkeys(item.reference_context for item in items if item.reference_context)
        )
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
            reference_context=merged_reference_context,
            inbound=last.inbound,
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
        reference_context: str | None = None,
        inbound: InflightMessageContext,
        client,
        excluded_timestamps: set[str] | None = None,
    ) -> None:
        metadata = {
            "channel": channel,
            "thread_ts": reply_thread_ts,
            "user": user,
            "user_name": user_name,
            "source": inbound.source,
            "mention": inbound.mention,
            "is_private": inbound.is_private,
        }
        delivery_context = _build_delivery_context_prefix(channel, reply_thread_ts)
        context_prefix = delivery_context
        is_thread_event = bool(event.get("thread_ts"))
        should_refresh_bootstrap = not _is_dm(event) or not self.session_manager.get_session_records(session_id)
        if should_refresh_bootstrap:
            bootstrap_context = await self._build_slack_bootstrap_context(
                client=client,
                event=event,
                excluded_timestamps=excluded_timestamps,
            )
            history_warning = None
            if not _is_dm(event) and not bootstrap_context:
                history_warning = (
                    "Slack channel/thread history from earlier messages could not be loaded for this turn.\n"
                    "Do not claim you saw earlier channel or thread messages unless you actually retrieved them."
                )
            context_prefix = _merge_context_prefix(
                delivery_context,
                reference_context,
                bootstrap_context,
                history_warning,
            )
        else:
            context_prefix = _merge_context_prefix(delivery_context, reference_context)
        has_active_run = getattr(self.session_manager, "has_active_run", None)
        start_heartbeat = not has_active_run(session_id) if callable(has_active_run) else True
        run_task = asyncio.create_task(
            self.session_manager.run(
                session_id=session_id,
                prompt=prompt,
                context_prefix=context_prefix,
                metadata=metadata,
            )
        )
        heartbeat_task: asyncio.Task[None] | None = None
        if start_heartbeat and self.settings.observer_enabled and self.observer_service is not None:
            heartbeat_task = asyncio.create_task(
                run_heartbeat_loop(
                    self.session_manager,
                    self.observer_service,
                    session_id=session_id,
                    run_task=run_task,
                    send_update=lambda text: client.chat_postMessage(channel=channel, thread_ts=reply_thread_ts, text=text),
                    initial_delay_seconds=self.settings.observer_heartbeat_initial_seconds,
                    interval_seconds=self.settings.observer_heartbeat_interval_seconds,
                )
            )
        try:
            record = await run_task
        finally:
            await cancel_heartbeat_task(heartbeat_task)
        await self._publish_result(client, channel, reply_thread_ts, record)

    async def _maybe_handle_inflight_event(
        self,
        *,
        session_id: str,
        prompt: str,
        channel: str,
        reply_thread_ts: str | None,
        client,
        inbound: InflightMessageContext,
    ) -> bool:
        decision = await maybe_route_inflight_message(
            self.session_manager,
            self.observer_service if self.settings.observer_enabled else None,
            session_id=session_id,
            prompt=prompt,
            inbound=inbound,
        )
        if decision is None:
            return False

        if decision.reply_text:
            await client.chat_postMessage(channel=channel, thread_ts=reply_thread_ts, text=decision.reply_text)

        return decision.intent in {"status_query", "unsupported_control"}

    async def _publish_result(self, client, channel: str, thread_ts: str | None, record: RunRecord) -> None:
        if record.state == "failed":
            text = f"Run failed.\n{record.error or 'Unknown error'}"
            await client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=text)
            return

        process_manager = getattr(getattr(self.session_manager, "engine", None), "process_manager", None)
        spoken_messages = list(record.result.spoken_messages) if record.result else []
        if spoken_messages:
            rendered_messages = list(spoken_messages)
            rendered_messages[-1] = append_response_trace(
                rendered_messages[-1],
                record,
                process_manager=process_manager,
                enabled=self.settings.response_trace_enabled,
            )
            for text in rendered_messages:
                await client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=text)
            return

        fallback_text = build_terminal_fallback_response(
            record,
            process_manager=process_manager,
            enabled=self.settings.response_trace_enabled,
        )
        if fallback_text:
            await client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=fallback_text)
        return

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
            resolved_text = await self._resolve_user_mentions_in_text(
                client,
                _strip_bot_mention(message.get("text", ""), self.identity.get("user_id")),
            )
            cleaned = _build_event_prompt(
                {
                    **message,
                    "text": resolved_text,
                },
                mention=False,
                agent_name=self.settings.agent_name,
                bot_user_id=self.identity.get("user_id"),
            )
            if not cleaned:
                continue
            cleaned_lines = cleaned.splitlines()
            lines.append(f"{speaker}: {cleaned_lines[0]}")
            for continuation in cleaned_lines[1:]:
                lines.append(f"  {continuation}")

        return "\n".join(lines) if len(lines) > 1 else None

    async def _fetch_bootstrap_messages(
        self,
        client,
        event: dict[str, Any],
        *,
        excluded_timestamps: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            messages = await self._fetch_bootstrap_messages_with_client(
                client,
                event,
                excluded_timestamps=excluded_timestamps,
            )
            if messages:
                logger.info(
                    "Loaded Slack bootstrap history with channel token: channel=%s thread_ts=%s count=%s",
                    event.get("channel"),
                    event.get("thread_ts"),
                    len(messages),
                )
                return messages
        except Exception as exc:
            logger.warning("Failed to fetch Slack history bootstrap with channel token: %s", exc)

        retrieve_client = self._get_retrieve_client()
        if retrieve_client is not None:
            try:
                messages = await self._fetch_bootstrap_messages_with_client(
                    retrieve_client,
                    event,
                    excluded_timestamps=excluded_timestamps,
                )
                if messages:
                    logger.info(
                        "Loaded Slack bootstrap history with retrieve token: channel=%s thread_ts=%s count=%s",
                        event.get("channel"),
                        event.get("thread_ts"),
                        len(messages),
                    )
                    return messages
            except Exception as exc:
                logger.warning("Failed to fetch Slack history bootstrap with retrieve token: %s", exc)

        return []

    async def _fetch_bootstrap_messages_with_client(
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
                limit=_SLACK_HISTORY_LIMIT,
                latest=current_ts,
                inclusive=False,
            )
            messages = response.get("messages", [])
            messages.reverse()
            return [
                message
                for message in messages
                if (message.get("text") or message.get("files")) and str(message.get("ts")) not in excluded
            ]

        thread_ts = event.get("thread_ts")
        if thread_ts:
            response = await client.conversations_replies(
                channel=event["channel"],
                ts=thread_ts,
                latest=current_ts,
                inclusive=False,
                limit=_SLACK_HISTORY_LIMIT,
            )
            current_value = _ts_value(current_ts)
            return [
                message
                for message in response.get("messages", [])
                if (
                    (message.get("text") or message.get("files"))
                    and _ts_value(message.get("ts")) < current_value
                    and str(message.get("ts")) not in excluded
                )
            ]

        response = await client.conversations_history(
            channel=event["channel"],
            limit=_SLACK_HISTORY_LIMIT,
            latest=current_ts,
            inclusive=False,
        )
        messages = response.get("messages", [])
        messages.reverse()
        return [
            message
            for message in messages
            if (message.get("text") or message.get("files")) and str(message.get("ts")) not in excluded
        ]

    def _get_retrieve_client(self) -> AsyncWebClient | None:
        if not (self.settings.slack_retrieve_enabled and self.settings.slack_retrieve_token):
            return None
        if self._retrieve_client is None:
            self._retrieve_client = AsyncWebClient(token=self.settings.slack_retrieve_token)
        return self._retrieve_client

    async def _speaker_for_message(self, client, message: dict[str, Any]) -> str:
        user_id = message.get("user")
        if user_id:
            if user_id == self.identity.get("user_id"):
                return self.settings.agent_name
            return await self._get_user_name(client, user_id)

        if message.get("bot_id") or message.get("subtype") == "bot_message":
            return self.settings.agent_name

        return "Slack"

    async def _resolve_user_mentions_in_text(self, client, text: str) -> str:
        if "<@" not in text and "<#" not in text:
            return text

        bot_user_id = self.identity.get("user_id")
        mentioned_user_ids = {
            match.group(1)
            for match in _USER_MENTION_RE.finditer(text)
            if match.group(1) != bot_user_id
        }
        resolved_names = {
            user_id: await self._get_user_name(client, user_id)
            for user_id in mentioned_user_ids
        }
        mentioned_channels = list(_CHANNEL_MENTION_RE.finditer(text))
        resolved_channel_names = {
            match.group(1): (match.group(2) or await self._get_channel_name(client, match.group(1)))
            for match in mentioned_channels
        }

        def replace(match: re.Match[str]) -> str:
            user_id = match.group(1)
            if user_id == bot_user_id:
                return match.group(0)
            name = resolved_names.get(user_id)
            if not name:
                return match.group(0)
            return f"@{name}"

        resolved = _USER_MENTION_RE.sub(replace, text)

        def replace_channel(match: re.Match[str]) -> str:
            channel_id = match.group(1)
            channel_name = (resolved_channel_names.get(channel_id) or channel_id).strip()
            if not channel_name:
                return match.group(0)
            return f"#{channel_name}"

        return _CHANNEL_MENTION_RE.sub(replace_channel, resolved)

    async def _build_delivery_reference_context(self, client, text: str) -> str | None:
        if "<@" not in text and "<#" not in text:
            return None

        bot_user_id = self.identity.get("user_id")
        lines: list[str] = []

        seen_users: set[str] = set()
        for match in _USER_MENTION_RE.finditer(text):
            user_id = match.group(1)
            if user_id == bot_user_id or user_id in seen_users:
                continue
            seen_users.add(user_id)
            user_name = await self._get_user_name(client, user_id)
            lines.append(f"- user @{user_name}: user_id={user_id}, mention_token=<@{user_id}>")

        seen_channels: set[str] = set()
        for match in _CHANNEL_MENTION_RE.finditer(text):
            channel_id = match.group(1)
            if channel_id in seen_channels:
                continue
            seen_channels.add(channel_id)
            channel_name = (match.group(2) or await self._get_channel_name(client, channel_id)).strip() or channel_id
            lines.append(
                f"- channel #{channel_name}: channel_id={channel_id}, mention_token=<#{channel_id}|{channel_name}>"
            )

        if not lines:
            return None

        return "\n".join(
            [
                "Slack references explicitly mentioned in the current conversation:",
                *lines,
                "Use these exact IDs or mention tokens for Slack delivery in this conversation.",
            ]
        )
