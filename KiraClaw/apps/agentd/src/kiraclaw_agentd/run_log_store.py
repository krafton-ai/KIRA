from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from kiraclaw_agentd.tool_event_summary import summarize_tool_events

if TYPE_CHECKING:
    from kiraclaw_agentd.session_manager import RunRecord
    from kiraclaw_agentd.settings import KiraClawSettings


def _external_text(record: RunRecord) -> str:
    result = record.result
    if result is None or not result.spoken_messages:
        return ""
    return result.public_response_text


def _silent_reason(record: RunRecord) -> str | None:
    if record.state != "completed":
        return None
    result = record.result
    if result is None or result.spoken_messages:
        return None
    return "no_speak"


def build_run_log_entry(record: RunRecord) -> dict[str, Any]:
    result = record.result
    return {
        "run_id": record.run_id,
        "session_id": record.session_id,
        "state": record.state,
        "source": str(record.metadata.get("source", "")),
        "created_at": record.created_at,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "prompt": record.prompt,
        "metadata": record.metadata,
        "internal_summary": result.internal_summary if result else "",
        "spoken_messages": list(result.spoken_messages) if result else [],
        "external_text": _external_text(record),
        "streamed_text": result.streamed_text if result else "",
        "tool_events": list(result.tool_events) if result else [],
        "tool_summary": summarize_tool_events(result.tool_events if result else []),
        "silent_reason": _silent_reason(record),
        "error": record.error,
    }


class RunLogStore:
    def __init__(self, settings: KiraClawSettings) -> None:
        self._log_dir = settings.run_log_dir or (settings.workspace_dir / "logs")
        self._log_file = settings.run_log_file or (self._log_dir / "runs.jsonl")

    @property
    def log_file(self) -> Path:
        return self._log_file

    def append(self, record: RunRecord) -> None:
        self._log_dir.mkdir(parents=True, exist_ok=True)
        entry = build_run_log_entry(record)
        with self._log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def tail(self, *, limit: int = 50, session_id: str | None = None) -> list[dict[str, Any]]:
        if not self._log_file.exists():
            return []

        rows: list[dict[str, Any]] = []
        for raw_line in self._log_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if session_id and row.get("session_id") != session_id:
                continue
            rows.append(row)

        rows.reverse()
        return rows[: max(1, limit)]
