from __future__ import annotations

from datetime import datetime, timezone
import threading
from typing import Any
from uuid import uuid4

from kiraclaw_agentd.delivery_targets import DEFAULT_DESKTOP_SESSION_ID


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DesktopDelivery:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._messages: dict[str, list[dict[str, Any]]] = {}
        self._sequence = 0

    async def send_message(
        self,
        session_id: str | None,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        normalized_session_id = str(session_id or DEFAULT_DESKTOP_SESSION_ID).strip() or DEFAULT_DESKTOP_SESSION_ID
        entry = {
            "id": str(uuid4()),
            "session_id": normalized_session_id,
            "text": str(text or ""),
            "created_at": _utc_now(),
            "metadata": dict(metadata or {}),
        }
        with self._lock:
            self._messages.setdefault(normalized_session_id, []).append(entry)
            self._sequence += 1
            self._condition.notify_all()

    def drain_messages(self, session_id: str | None) -> list[dict[str, Any]]:
        normalized_session_id = str(session_id or DEFAULT_DESKTOP_SESSION_ID).strip() or DEFAULT_DESKTOP_SESSION_ID
        with self._lock:
            rows = list(self._messages.get(normalized_session_id, []))
            self._messages.pop(normalized_session_id, None)
        return rows

    def current_sequence(self) -> int:
        with self._lock:
            return int(self._sequence)

    def wait_for_message(self, after_sequence: int, timeout: float = 15.0) -> int | None:
        with self._condition:
            has_new_message = self._condition.wait_for(lambda: self._sequence > int(after_sequence), timeout=timeout)
            if not has_new_message:
                return None
            return int(self._sequence)
