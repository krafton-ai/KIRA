from __future__ import annotations

import json
from pathlib import Path
import threading
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
        "trace_events": list(result.trace_events) if result else [],
        "tool_summary": summarize_tool_events(result.tool_events if result else []),
        "silent_reason": _silent_reason(record),
        "error": record.error,
    }


class RunLogStore:
    def __init__(self, settings: KiraClawSettings) -> None:
        self._log_dir = settings.run_log_dir or (settings.workspace_dir / "logs")
        self._log_file = settings.run_log_file or (self._log_dir / "runs.jsonl")
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._live_records: dict[str, RunRecord] = {}
        self._sequence = 0

    @property
    def log_file(self) -> Path:
        return self._log_file

    def observe(self, record: RunRecord) -> None:
        with self._lock:
            self._sequence += 1
            if record.state in {"queued", "running"}:
                self._live_records[record.run_id] = record
                self._condition.notify_all()
                return

            self._live_records.pop(record.run_id, None)
            self._append_final_entry(record)
            self._condition.notify_all()

    def append(self, record: RunRecord) -> None:
        with self._lock:
            self._sequence += 1
            self._append_final_entry(record)
            self._condition.notify_all()

    def _append_final_entry(self, record: RunRecord) -> None:
        self._log_dir.mkdir(parents=True, exist_ok=True)
        entry = build_run_log_entry(record)
        with self._log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def tail(self, *, limit: int = 50, session_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._read_persisted_rows(session_id=session_id)
            rows.extend(self._build_live_rows(session_id=session_id))
            rows.sort(key=_sort_run_log_entry_key, reverse=True)
            return rows[: max(1, limit)]

    def current_sequence(self) -> int:
        with self._lock:
            return int(self._sequence)

    def wait_for_update(self, after_sequence: int, timeout: float = 15.0) -> int | None:
        with self._condition:
            has_new_record = self._condition.wait_for(lambda: self._sequence > int(after_sequence), timeout=timeout)
            if not has_new_record:
                return None
            return int(self._sequence)

    def _build_live_rows(self, *, session_id: str | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for record in self._live_records.values():
            if session_id and record.session_id != session_id:
                continue
            rows.append(build_run_log_entry(record))
        return rows

    def _read_persisted_rows(self, *, session_id: str | None = None) -> list[dict[str, Any]]:
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

        return rows


def _sort_run_log_entry_key(entry: dict[str, Any]) -> tuple[int, str, str]:
    state = str(entry.get("state") or "").strip().lower()
    priority = {"running": 2, "queued": 1}.get(state, 0)
    if priority > 0:
        timestamp = str(entry.get("started_at") or entry.get("created_at") or "")
    else:
        timestamp = str(entry.get("finished_at") or entry.get("created_at") or "")
    return (priority, timestamp, str(entry.get("run_id") or ""))
