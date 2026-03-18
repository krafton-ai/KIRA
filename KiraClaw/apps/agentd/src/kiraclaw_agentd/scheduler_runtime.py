from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from kiraclaw_agentd.channel_delivery import ChannelDelivery
from kiraclaw_agentd.schedule_store import ensure_schedule_file, read_schedules
from kiraclaw_agentd.session_manager import RunRecord, SessionManager
from kiraclaw_agentd.settings import KiraClawSettings

logger = logging.getLogger(__name__)


class SchedulerRuntime:
    def __init__(
        self,
        settings: KiraClawSettings,
        session_manager: SessionManager,
        channel_delivery: ChannelDelivery,
    ) -> None:
        self.settings = settings
        self.session_manager = session_manager
        self.channel_delivery = channel_delivery
        self.scheduler = AsyncIOScheduler(job_defaults={"coalesce": False, "max_instances": 1, "misfire_grace_time": 30})
        self.state: str = "disabled"
        self.last_error: str | None = None
        self._known_mtime: float | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.settings.mcp_enabled and self.settings.mcp_scheduler_enabled and self.settings.schedule_file)

    @property
    def job_count(self) -> int:
        return len(self.scheduler.get_jobs()) if self.scheduler.running else 0

    async def start(self) -> None:
        if not self.enabled:
            self.state = "disabled"
            return

        ensure_schedule_file(self.settings.schedule_file)
        await self.reload_from_file(force=True)
        self.scheduler.start()
        self.state = "running"

    async def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self.state = "disabled" if not self.enabled else "configured"

    async def reload_from_file(self, *, force: bool = False) -> None:
        if not self.enabled:
            self.state = "disabled"
            return

        schedule_file = self.settings.schedule_file
        ensure_schedule_file(schedule_file)
        mtime = schedule_file.stat().st_mtime
        if not force and self._known_mtime == mtime:
            return

        for job in self.scheduler.get_jobs():
            self.scheduler.remove_job(job.id)

        count = 0
        for schedule in read_schedules(schedule_file):
            if not schedule.get("is_enabled", True):
                continue

            schedule_id = schedule.get("id")
            schedule_name = schedule.get("name", schedule_id)
            schedule_type = schedule.get("schedule_type")
            schedule_value = schedule.get("schedule_value")
            job_args = [schedule]

            try:
                if schedule_type == "cron":
                    trigger = CronTrigger.from_crontab(schedule_value)
                    self.scheduler.add_job(self._execute_schedule, trigger=trigger, id=schedule_id, name=schedule_name, args=job_args)
                elif schedule_type == "date":
                    run_date = datetime.fromisoformat(schedule_value.replace("Z", "+00:00"))
                    if run_date <= datetime.now(run_date.tzinfo):
                        continue
                    self.scheduler.add_job(self._execute_schedule, trigger="date", run_date=run_date, id=schedule_id, name=schedule_name, args=job_args)
                else:
                    continue
                count += 1
            except Exception as exc:
                logger.exception("Failed to register schedule %s", schedule_id)
                self.last_error = f"{schedule_id}: {exc}"

        self._known_mtime = mtime
        self.last_error = None
        self.state = "running"
        logger.info("Scheduler runtime loaded %s schedules", count)

    async def _execute_schedule(self, schedule: dict[str, Any]) -> None:
        schedule_id = schedule.get("id", "unknown")
        channel_type = schedule.get("channel_type") or ""
        channel_target = schedule.get("channel_target") or ""
        prompt = schedule.get("text", "")
        user = schedule.get("user", "")

        record = await self.session_manager.run(
            session_id=f"schedule:{schedule_id}",
            prompt=prompt,
            context_prefix=self._schedule_context_prefix(channel_type, channel_target),
            metadata={
                "source": "scheduler",
                "channel_type": channel_type,
                "channel_target": channel_target,
                "user": user,
                "schedule_id": schedule_id,
                "schedule_name": schedule.get("name", ""),
            },
        )

        if channel_target:
            result_text = self._result_text(record)
            if result_text:
                await self.channel_delivery.send_text(channel_type, channel_target, result_text)

    def _result_text(self, record: RunRecord) -> str:
        if record.state == "failed":
            return f"Scheduled run failed.\n{record.error or 'Unknown error'}"
        if record.result:
            public_response = getattr(record.result, "public_response_text", "")
            if public_response:
                return public_response
        return ""

    def _schedule_context_prefix(self, channel_type: str, channel_target: str) -> str:
        target_type = str(channel_type or "slack").strip() or "slack"
        target_value = str(channel_target or "").strip()
        if target_value:
            return (
                "This is a scheduled automation run.\n"
                f"If you use speak, your outward words will be delivered to {target_type}:{target_value}.\n"
                "If no outward delivery is useful, stay silent and finish the run without speak."
            )
        return (
            "This is a scheduled automation run with no automatic outward delivery target.\n"
            "Think and act first. Stay silent unless you deliberately use tools to send something elsewhere."
        )
