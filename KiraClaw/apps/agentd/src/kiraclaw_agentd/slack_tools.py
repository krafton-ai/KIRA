from __future__ import annotations

import json
from typing import Any, Callable

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
            response = self._client().chat_postMessage(
                channel=channel_id,
                text=text,
                thread_ts=thread_ts,
            )
            return _build_result(
                True,
                channel=response.get("channel", channel_id),
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
            response = self._client().chat_postMessage(
                channel=channel_id,
                text=text,
                thread_ts=thread_ts,
            )
            return _build_result(
                True,
                channel=response.get("channel", channel_id),
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
            self._client().reactions_add(
                channel=channel_id,
                timestamp=timestamp,
                name=reaction,
            )
            return _build_result(True, channel=channel_id, timestamp=timestamp, reaction=reaction)

        return self._run_with_slack_error_boundary(_send)


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
    ]
    return tools
