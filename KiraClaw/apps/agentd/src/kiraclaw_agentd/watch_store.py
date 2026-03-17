from __future__ import annotations

import json
from pathlib import Path

from kiraclaw_agentd.watch_models import WatchRunRecord, WatchSpec, WatchState


def ensure_watch_files(watch_file: Path, state_file: Path) -> None:
    watch_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    if not watch_file.exists():
        watch_file.write_text("[]\n", encoding="utf-8")
    if not state_file.exists():
        state_file.write_text(WatchState().model_dump_json(indent=2) + "\n", encoding="utf-8")


def validate_interval_minutes(interval_minutes: int) -> str | None:
    if interval_minutes < 1:
        return "Interval minutes must be at least 1."
    if interval_minutes > 10_080:
        return "Interval minutes must be 10080 or less."
    return None


def read_watches(watch_file: Path) -> list[WatchSpec]:
    if not watch_file.exists():
        return []
    payload = json.loads(watch_file.read_text(encoding="utf-8"))
    return [WatchSpec.model_validate(item) for item in payload]


def write_watches(watch_file: Path, watches: list[WatchSpec]) -> None:
    watch_file.parent.mkdir(parents=True, exist_ok=True)
    watch_file.write_text(
        json.dumps([watch.model_dump() for watch in watches], indent=2) + "\n",
        encoding="utf-8",
    )


class WatchStateStore:
    def __init__(self, state_file: Path, history_limit: int) -> None:
        self.state_file = state_file
        self.history_limit = max(1, history_limit)

    def read_state(self) -> WatchState:
        if not self.state_file.exists():
            return WatchState()
        payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        return WatchState.model_validate(payload)

    def write_state(self, state: WatchState) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(state.model_dump_json(indent=2) + "\n", encoding="utf-8")

    def record_run(self, run: WatchRunRecord) -> None:
        state = self.read_state()
        state.runs.append(run)
        if len(state.runs) > self.history_limit:
            state.runs = state.runs[-self.history_limit :]
        self.write_state(state)

    def list_runs(self, limit: int = 50, watch_id: str | None = None) -> list[WatchRunRecord]:
        state = self.read_state()
        rows = state.runs
        if watch_id:
            rows = [run for run in rows if run.watch_id == watch_id]
        return list(reversed(rows[-max(1, limit) :]))
