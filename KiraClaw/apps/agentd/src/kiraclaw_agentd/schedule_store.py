from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_schedule_file(schedule_file: Path) -> None:
    schedule_file.parent.mkdir(parents=True, exist_ok=True)
    if not schedule_file.exists():
        schedule_file.write_text("[]\n", encoding="utf-8")


def read_schedules(schedule_file: Path) -> list[dict[str, Any]]:
    ensure_schedule_file(schedule_file)
    try:
        return json.loads(schedule_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def write_schedules(schedule_file: Path, schedules: list[dict[str, Any]]) -> None:
    ensure_schedule_file(schedule_file)
    schedule_file.write_text(
        json.dumps(schedules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
