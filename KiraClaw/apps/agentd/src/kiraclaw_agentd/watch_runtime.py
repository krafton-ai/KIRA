from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from kiraclaw_agentd.session_manager import RunRecord, SessionManager
from kiraclaw_agentd.settings import KiraClawSettings
from kiraclaw_agentd.watch_models import WatchRunRecord, WatchSpec, derive_watch_title, utc_now
from kiraclaw_agentd.watch_store import (
    WatchStateStore,
    ensure_watch_files,
    read_watches,
    validate_interval_minutes,
    write_watches,
)

logger = logging.getLogger(__name__)


class WatchRuntime:
    def __init__(
        self,
        settings: KiraClawSettings,
        session_manager: SessionManager,
    ) -> None:
        if not settings.watch_file or not settings.watch_state_file:
            raise ValueError("watch files must be configured")

        self.settings = settings
        self.session_manager = session_manager
        self.scheduler = self._create_scheduler()
        self.store = WatchStateStore(settings.watch_state_file, settings.watch_history_limit)
        self.state: str = "disabled" if not settings.watch_enabled else "stopped"
        self.last_error: str | None = None
        self._lock = asyncio.Lock()

    def _create_scheduler(self) -> AsyncIOScheduler:
        return AsyncIOScheduler(
            job_defaults={"coalesce": False, "max_instances": 1, "misfire_grace_time": 30}
        )

    @property
    def enabled(self) -> bool:
        return bool(self.settings.watch_enabled and self.settings.watch_file and self.settings.watch_state_file)

    @property
    def job_count(self) -> int:
        return len(self.scheduler.get_jobs()) if self.scheduler.running else 0

    def list_watches(self) -> list[WatchSpec]:
        if not self.settings.watch_file:
            return []
        ensure_watch_files(self.settings.watch_file, self.settings.watch_state_file)
        return read_watches(self.settings.watch_file)

    def list_runs(self, limit: int = 50, watch_id: str | None = None) -> list[WatchRunRecord]:
        return self.store.list_runs(limit=limit, watch_id=watch_id)

    async def start(self) -> None:
        if not self.enabled:
            self.state = "disabled"
            return

        ensure_watch_files(self.settings.watch_file, self.settings.watch_state_file)
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.scheduler = self._create_scheduler()
        self.scheduler.start()
        await self.reload_from_file()
        self.state = "running"
        self.last_error = None

    async def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self.scheduler = self._create_scheduler()
        self.state = "disabled" if not self.enabled else "stopped"

    async def reload_from_file(self) -> None:
        if not self.enabled:
            self.state = "disabled"
            return

        watch_file = self.settings.watch_file
        state_file = self.settings.watch_state_file
        ensure_watch_files(watch_file, state_file)

        for job in self.scheduler.get_jobs():
            self.scheduler.remove_job(job.id)

        count = 0
        for watch in read_watches(watch_file):
            if not watch.is_enabled:
                continue

            try:
                self.scheduler.add_job(
                    self._execute_watch,
                    trigger="interval",
                    minutes=watch.interval_minutes,
                    id=watch.watch_id,
                    name=_watch_label(watch),
                    args=[watch],
                )
                count += 1
            except Exception as exc:
                logger.exception("Failed to register watch %s", watch.watch_id)
                self.last_error = f"{watch.watch_id}: {exc}"

        self.last_error = None
        self.state = "running"
        logger.info("Watch runtime loaded %s watches", count)

    async def upsert_watch(self, spec: WatchSpec) -> WatchSpec:
        error = validate_interval_minutes(spec.interval_minutes)
        if error:
            raise ValueError(error)

        async with self._lock:
            ensure_watch_files(self.settings.watch_file, self.settings.watch_state_file)
            watches = read_watches(self.settings.watch_file)
            updated = False
            next_rows: list[WatchSpec] = []
            for row in watches:
                if row.watch_id == spec.watch_id:
                    next_rows.append(
                        spec.model_copy(
                            update={
                                "created_at": row.created_at,
                                "updated_at": utc_now(),
                            }
                        )
                    )
                    updated = True
                else:
                    next_rows.append(row)
            if not updated:
                next_rows.append(spec.model_copy(update={"updated_at": utc_now()}))
            write_watches(self.settings.watch_file, next_rows)

        await self.reload_from_file()
        return next((row for row in read_watches(self.settings.watch_file) if row.watch_id == spec.watch_id), spec)

    async def delete_watch(self, watch_id: str) -> bool:
        async with self._lock:
            ensure_watch_files(self.settings.watch_file, self.settings.watch_state_file)
            watches = read_watches(self.settings.watch_file)
            next_rows = [row for row in watches if row.watch_id != watch_id]
            changed = len(next_rows) != len(watches)
            if changed:
                write_watches(self.settings.watch_file, next_rows)

        if changed:
            await self.reload_from_file()
        return changed

    async def run_now(self, watch_id: str) -> WatchRunRecord:
        watch = next((row for row in self.list_watches() if row.watch_id == watch_id), None)
        if watch is None:
            raise ValueError(f"Unknown watch: {watch_id}")
        return await self._execute_watch(watch)

    async def _execute_watch(self, watch: WatchSpec) -> WatchRunRecord:
        record = await self.session_manager.run(
            session_id=f"watch:{watch.watch_id}",
            prompt=_build_watch_prompt(watch),
            provider=watch.provider,
            model=watch.model,
            metadata={
                "source": "watch",
                "watch_id": watch.watch_id,
                "watch_name": _watch_label(watch),
                "watch_channel_id": watch.channel_id or "",
                "watch_interval_minutes": str(watch.interval_minutes),
            },
        )
        watch_run = _build_watch_run_record(watch, record)
        self.store.record_run(watch_run)
        return watch_run


def _build_watch_prompt(watch: WatchSpec) -> str:
    lines = [
        "You are running as a scheduled watch inside KiraClaw.",
        "This is not a user chat turn. Use tools and MCP when needed, but stay focused on the watch purpose.",
        f"Watch focus: {_watch_label(watch)}",
        f"Repeat interval: every {watch.interval_minutes} minute(s).",
    ]

    lines.extend(
        [
            "Condition to evaluate:",
            watch.condition.strip(),
            "Action to take when the condition is met:",
            watch.action.strip(),
        ]
    )

    if watch.channel_id:
        lines.extend(
            [
                "Default Slack channel context:",
                watch.channel_id,
            ]
        )

    lines.extend(
        [
            "If the condition is not met, do not take external action and submit a short summary that says no action was needed.",
            "If the condition is met, perform the action and then submit a short summary of what changed and what you did.",
            "Keep the final summary concise.",
        ]
    )
    return "\n\n".join(lines)


def _build_watch_run_record(watch: WatchSpec, record: RunRecord) -> WatchRunRecord:
    tool_names: list[str] = []
    seen: set[str] = set()
    if record.result is not None:
        for event in record.result.tool_events:
            if event.get("phase") != "start":
                continue
            name = str(event.get("name", "")).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            tool_names.append(name)

    return WatchRunRecord(
        watch_id=watch.watch_id,
        watch_name=_watch_label(watch),
        session_id=record.session_id,
        state=record.state,
        summary=record.result.final_response if record.result else "",
        error=record.error,
        tool_names=tool_names,
        created_at=record.created_at,
        started_at=record.started_at,
        finished_at=record.finished_at,
        metadata={k: str(v) for k, v in record.metadata.items()},
    )


def _watch_label(watch: WatchSpec) -> str:
    return derive_watch_title(watch.condition, watch.action)
