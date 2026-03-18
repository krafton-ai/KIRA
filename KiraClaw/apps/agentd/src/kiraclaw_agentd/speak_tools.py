from __future__ import annotations

import json
from typing import Any

from krim_sdk.tools import Tool

from kiraclaw_agentd.settings import KiraClawSettings


def _build_result(success: bool, **payload: Any) -> str:
    return json.dumps({"success": success, **payload}, ensure_ascii=False, indent=2)


class SpeakTool(Tool):
    name = "speak"
    description = (
        "Deliver a user-facing message to the current conversation. "
        "Use this when your words should actually be spoken externally."
    )
    parameters = {
        "text": {
            "type": "string",
            "description": "The user-facing message to say out loud in the current conversation.",
        }
    }

    def __init__(self, tool_context: dict[str, Any] | None = None) -> None:
        self._tool_context = dict(tool_context or {})
        messages = self._tool_context.get("__spoken_messages__")
        if isinstance(messages, list):
            self._spoken_messages = messages
        else:
            self._spoken_messages = []
            self._tool_context["__spoken_messages__"] = self._spoken_messages

    def run(self, text: str) -> str:
        cleaned = str(text or "").strip()
        if not cleaned:
            return _build_result(False, error="empty_text")

        self._spoken_messages.append(cleaned)

        return _build_result(
            True,
            text=cleaned,
            count=len(self._spoken_messages),
        )


def build_speak_tools(
    _settings: KiraClawSettings,
    *,
    tool_context: dict[str, Any] | None = None,
) -> list[Tool]:
    return [SpeakTool(tool_context)]
