from __future__ import annotations

import json
from typing import Any

from krim_sdk.tools import Tool

from kiraclaw_agentd.process_manager import BackgroundProcessManager
from kiraclaw_agentd.settings import KiraClawSettings

_PROCESS_MANAGER_KEY = "__process_manager__"


def _build_result(success: bool, **payload: Any) -> str:
    return json.dumps({"success": success, **payload}, ensure_ascii=False, indent=2)


class ExecTool(Tool):
    name = "exec"
    description = (
        "Run a shell command that may finish quickly or continue as a background session. "
        "Use this for long-running builds, tests, servers, or jobs you may want to poll later."
    )
    parameters = {
        "command": {
            "type": "string",
            "description": "Shell command to execute.",
        },
        "background": {
            "type": "boolean",
            "description": "If true, return a session_id immediately instead of waiting briefly for completion.",
            "optional": True,
        },
        "yield_ms": {
            "type": "integer",
            "description": "How long to wait for quick completion before returning a running session.",
            "optional": True,
        },
        "cwd": {
            "type": "string",
            "description": "Optional working directory. Relative paths are resolved from the workspace root.",
            "optional": True,
        },
    }

    def __init__(self, manager: BackgroundProcessManager, tool_context: dict[str, Any] | None = None) -> None:
        self._manager = manager
        self._tool_context = dict(tool_context or {})

    def run(
        self,
        command: str,
        background: bool | None = None,
        yield_ms: int | None = None,
        cwd: str | None = None,
    ) -> str:
        try:
            session = self._manager.start(
                command=command,
                cwd=cwd,
                owner_session_id=str(self._tool_context.get("session_id") or "").strip(),
            )
        except (KeyError, ValueError) as exc:
            return _build_result(False, error=str(exc))

        if background:
            snapshot = self._manager.poll(session.session_id)
            return _build_result(
                True,
                status=snapshot["status"],
                session_id=session.session_id,
                command=snapshot["command"],
                cwd=snapshot["cwd"],
                pid=snapshot["pid"],
                output=snapshot["output"],
                background=True,
            )

        completed = self._manager.wait_briefly(session.session_id, int(yield_ms or 10_000))
        snapshot = self._manager.poll(session.session_id)

        if completed:
            try:
                self._manager.clear(session.session_id)
            except ValueError:
                pass
            return _build_result(
                True,
                status=snapshot["status"],
                command=snapshot["command"],
                cwd=snapshot["cwd"],
                pid=snapshot["pid"],
                exit_code=snapshot["exit_code"],
                output=snapshot["output"],
                completed=True,
                background=False,
            )

        return _build_result(
            True,
            status=snapshot["status"],
            session_id=session.session_id,
            command=snapshot["command"],
            cwd=snapshot["cwd"],
            pid=snapshot["pid"],
            output=snapshot["output"],
            completed=False,
            background=True,
        )


class ProcessTool(Tool):
    name = "process"
    description = (
        "Inspect or manage background exec sessions. Use this to list, poll, read logs, kill, or clear exec sessions."
    )
    parameters = {
        "action": {
            "type": "string",
            "description": "One of: list, poll, log, kill, clear.",
        },
        "session_id": {
            "type": "string",
            "description": "The exec session_id to inspect or manage.",
            "optional": True,
        },
        "tail_chars": {
            "type": "integer",
            "description": "Optional output tail size for poll/log/list responses.",
            "optional": True,
        },
    }

    def __init__(self, manager: BackgroundProcessManager, tool_context: dict[str, Any] | None = None) -> None:
        self._manager = manager
        self._tool_context = dict(tool_context or {})

    def _owner_session_id(self) -> str:
        return str(self._tool_context.get("session_id") or "").strip()

    def run(
        self,
        action: str,
        session_id: str | None = None,
        tail_chars: int | None = None,
    ) -> str:
        normalized = str(action or "").strip().lower()
        owner_session_id = self._owner_session_id()
        try:
            if normalized == "list":
                return _build_result(
                    True,
                    action=normalized,
                    sessions=self._manager.list_sessions(
                        tail_chars=tail_chars,
                        owner_session_id=owner_session_id,
                    ),
                )
            if normalized == "poll":
                return _build_result(
                    True,
                    action=normalized,
                    session=self._manager.poll(
                        str(session_id or "").strip(),
                        tail_chars=tail_chars,
                        owner_session_id=owner_session_id,
                    ),
                )
            if normalized == "log":
                return _build_result(
                    True,
                    action=normalized,
                    session=self._manager.log(
                        str(session_id or "").strip(),
                        tail_chars=tail_chars,
                        owner_session_id=owner_session_id,
                    ),
                )
            if normalized == "kill":
                return _build_result(
                    True,
                    action=normalized,
                    session=self._manager.kill(
                        str(session_id or "").strip(),
                        owner_session_id=owner_session_id,
                    ),
                )
            if normalized == "clear":
                self._manager.clear(
                    str(session_id or "").strip(),
                    owner_session_id=owner_session_id,
                )
                return _build_result(True, action=normalized, session_id=str(session_id or "").strip())
        except (KeyError, ValueError) as exc:
            return _build_result(False, error=str(exc), action=normalized)

        return _build_result(False, error=f"unsupported_action: {normalized}")


def build_process_tools(
    _settings: KiraClawSettings,
    *,
    tool_context: dict[str, Any] | None = None,
) -> list[Tool]:
    context = dict(tool_context or {})
    manager = context.get(_PROCESS_MANAGER_KEY)
    if not isinstance(manager, BackgroundProcessManager):
        return []
    return [ExecTool(manager, context), ProcessTool(manager, context)]
