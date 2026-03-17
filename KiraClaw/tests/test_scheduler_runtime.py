from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from kiraclaw_agentd.schedule_store import write_schedules
from kiraclaw_agentd.scheduler_runtime import SchedulerRuntime
from kiraclaw_agentd.settings import KiraClawSettings


class FakeSessionManager:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def run(self, session_id: str, prompt: str, metadata: dict | None = None, provider=None, model=None):
        self.calls.append({"session_id": session_id, "prompt": prompt, "metadata": metadata or {}})
        return SimpleNamespace(
            state="completed",
            error=None,
            result=SimpleNamespace(final_response="scheduled response"),
        )


class FakeSlackGateway:
    def __init__(self) -> None:
        self.configured = True
        self.messages: list[dict] = []

    async def send_message(self, channel: str, text: str, thread_ts=None) -> None:
        self.messages.append({"channel": channel, "text": text, "thread_ts": thread_ts})


def test_scheduler_runtime_executes_due_schedule(tmp_path) -> None:
    async def scenario() -> None:
        schedule_file = tmp_path / "workspace" / "schedule_data" / "schedules.json"
        write_schedules(
            schedule_file,
            [
                {
                    "id": "sched-1",
                    "name": "One shot",
                    "schedule_type": "date",
                    "schedule_value": (datetime.now(timezone.utc) + timedelta(milliseconds=300)).isoformat(),
                    "user": "U123",
                    "text": "KIRA, do the thing",
                    "channel": "C123",
                    "is_enabled": True,
                }
            ],
        )

        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            mcp_enabled=True,
            mcp_scheduler_enabled=True,
            schedule_file=schedule_file,
        )
        session_manager = FakeSessionManager()
        slack_gateway = FakeSlackGateway()
        runtime = SchedulerRuntime(settings, session_manager, slack_gateway)

        try:
            await runtime.start()
            await asyncio.sleep(1.0)
        finally:
            await runtime.stop()

        assert runtime.last_error is None
        assert session_manager.calls
        assert session_manager.calls[0]["prompt"] == "KIRA, do the thing"
        assert slack_gateway.messages == [{"channel": "C123", "text": "scheduled response", "thread_ts": None}]

    asyncio.run(scenario())
