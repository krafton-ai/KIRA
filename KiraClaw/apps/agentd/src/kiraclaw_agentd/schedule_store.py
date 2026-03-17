from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_SUPPORTED_CHANNEL_TYPES = {"slack", "telegram"}


def ensure_schedule_file(schedule_file: Path) -> None:
    schedule_file.parent.mkdir(parents=True, exist_ok=True)
    if not schedule_file.exists():
        schedule_file.write_text("[]\n", encoding="utf-8")


def read_schedules(schedule_file: Path) -> list[dict[str, Any]]:
    ensure_schedule_file(schedule_file)
    try:
        payload = json.loads(schedule_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [_normalize_schedule(row) for row in payload if isinstance(row, dict)]


def write_schedules(schedule_file: Path, schedules: list[dict[str, Any]]) -> None:
    ensure_schedule_file(schedule_file)
    schedule_file.write_text(
        json.dumps([_normalize_schedule(row) for row in schedules], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _normalize_schedule(schedule: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(schedule)

    channel_target = str(
        normalized.get("channel_target")
        or normalized.get("channel")
        or normalized.get("channel_id")
        or ""
    ).strip()
    channel_type = str(normalized.get("channel_type") or "").strip().lower()
    if channel_type not in _SUPPORTED_CHANNEL_TYPES:
        channel_type = "slack" if channel_target else ""

    normalized["channel_type"] = channel_type or None
    normalized["channel_target"] = channel_target or None
    normalized.pop("channel", None)
    normalized.pop("channel_id", None)
    return normalized
