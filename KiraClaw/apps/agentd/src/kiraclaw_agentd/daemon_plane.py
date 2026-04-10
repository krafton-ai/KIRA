from __future__ import annotations

import json
from pathlib import Path
import threading
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from kiraclaw_agentd.settings import KiraClawSettings


def _timestamp() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


class DaemonEventStore:
    def __init__(self, settings: KiraClawSettings) -> None:
        self._log_dir = settings.run_log_dir or (settings.workspace_dir / "logs")
        self._log_file = self._log_dir / "daemon-events.jsonl"
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._sequence = 0
        self._latest_entry: dict[str, Any] | None = None

    @property
    def log_file(self) -> Path:
        return self._log_file

    def emit(
        self,
        event_type: str,
        *,
        message: str,
        level: str = "info",
        resource_kind: str | None = None,
        resource_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self._sequence += 1
            entry = {
            "event_id": f"evt_{uuid4().hex[:12]}",
            "type": str(event_type or "").strip() or "daemon.event",
            "level": str(level or "info").strip() or "info",
            "message": str(message or "").strip(),
            "resource_kind": str(resource_kind or "").strip() or None,
            "resource_id": str(resource_id or "").strip() or None,
            "payload": payload or {},
            "created_at": _timestamp(),
            "sequence": self._sequence,
            }
            self._log_dir.mkdir(parents=True, exist_ok=True)
            with self._log_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self._latest_entry = dict(entry)
            self._condition.notify_all()
        return entry

    def current_sequence(self) -> int:
        with self._lock:
            return int(self._sequence)

    def wait_for_event(self, after_sequence: int, timeout: float = 15.0) -> dict[str, Any] | None:
        with self._condition:
            has_new_event = self._condition.wait_for(lambda: self._sequence > int(after_sequence), timeout=timeout)
            if not has_new_event or self._latest_entry is None:
                return None
            return dict(self._latest_entry)

    def tail(
        self,
        *,
        limit: int = 100,
        resource_kind: str | None = None,
        resource_id: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
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
                if resource_kind and row.get("resource_kind") != resource_kind:
                    continue
                if resource_id and row.get("resource_id") != resource_id:
                    continue
                rows.append(row)
            rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
            return rows[: max(1, int(limit))]


class DaemonResourceRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._resources: dict[tuple[str, str], dict[str, Any]] = {}

    def upsert(
        self,
        kind: str,
        resource_id: str,
        state: str,
        *,
        data: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        key = (str(kind).strip(), str(resource_id).strip())
        if not key[0] or not key[1]:
            raise ValueError("resource_kind_and_id_required")

        entry = {
            "kind": key[0],
            "id": key[1],
            "state": str(state or "").strip() or "unknown",
            "data": data or {},
            "updated_at": _timestamp(),
        }
        with self._lock:
            previous = self._resources.get(key)
            changed = previous is None or previous.get("state") != entry["state"] or previous.get("data") != entry["data"]
            self._resources[key] = entry
        return entry, changed

    def remove(self, kind: str, resource_id: str) -> dict[str, Any] | None:
        key = (str(kind).strip(), str(resource_id).strip())
        with self._lock:
            return self._resources.pop(key, None)

    def list(self, *, kind: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._resources.values())
        if kind:
            rows = [row for row in rows if row.get("kind") == kind]
        rows.sort(key=lambda row: (str(row.get("kind") or ""), str(row.get("id") or "")))
        return rows

    def summary(self) -> dict[str, int]:
        with self._lock:
            rows = list(self._resources.values())
        counts: dict[str, int] = {}
        for row in rows:
            key = str(row.get("kind") or "")
            counts[key] = counts.get(key, 0) + 1
        return counts


class DaemonPlane:
    def __init__(self, settings: KiraClawSettings) -> None:
        self.events = DaemonEventStore(settings)
        self.resources = DaemonResourceRegistry()

    @property
    def event_log_file(self) -> Path:
        return self.events.log_file

    def upsert_resource(
        self,
        kind: str,
        resource_id: str,
        state: str,
        *,
        data: dict[str, Any] | None = None,
        event_type: str | None = None,
        message: str | None = None,
        level: str = "info",
    ) -> dict[str, Any]:
        entry, changed = self.resources.upsert(kind, resource_id, state, data=data)
        if changed:
            self.events.emit(
                event_type or f"{kind}.updated",
                message=message or f"{kind}:{resource_id} -> {entry['state']}",
                level=level,
                resource_kind=entry["kind"],
                resource_id=entry["id"],
                payload=entry["data"],
            )
        return entry

    def remove_resource(
        self,
        kind: str,
        resource_id: str,
        *,
        message: str | None = None,
        event_type: str | None = None,
        level: str = "info",
        payload: dict[str, Any] | None = None,
    ) -> None:
        removed = self.resources.remove(kind, resource_id)
        if removed is None:
            return
        self.events.emit(
            event_type or f"{kind}.removed",
            message=message or f"{kind}:{resource_id} removed",
            level=level,
            resource_kind=kind,
            resource_id=resource_id,
            payload=payload or removed.get("data") or {},
        )

    def emit(
        self,
        event_type: str,
        *,
        message: str,
        level: str = "info",
        resource_kind: str | None = None,
        resource_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.events.emit(
            event_type,
            message=message,
            level=level,
            resource_kind=resource_kind,
            resource_id=resource_id,
            payload=payload,
        )
