from __future__ import annotations

import asyncio

from kiraclaw_agentd.engine import RunResult
from kiraclaw_agentd.session_manager import RunRecord, utc_now
from kiraclaw_agentd.settings import KiraClawSettings
from kiraclaw_agentd.watch_models import WatchSpec
from kiraclaw_agentd.watch_runtime import WatchRuntime


class FakeSessionManager:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def run(self, session_id: str, prompt: str, metadata: dict | None = None, provider=None, model=None):
        self.calls.append(
            {
                "session_id": session_id,
                "prompt": prompt,
                "metadata": metadata or {},
                "provider": provider,
                "model": model,
            }
        )
        created_at = utc_now()
        return RunRecord(
            run_id="run-1",
            session_id=session_id,
            state="completed",
            prompt=prompt,
            created_at=created_at,
            started_at=created_at,
            finished_at=created_at,
            result=RunResult(
                final_response="No action needed.",
                streamed_text="",
                tool_events=[{"phase": "start", "name": "current_time", "args": {}}],
            ),
            metadata=metadata or {},
        )


def test_watch_runtime_executes_due_watch(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            watch_enabled=True,
        )
        session_manager = FakeSessionManager()
        runtime = WatchRuntime(settings, session_manager)
        watch = WatchSpec(
            interval_minutes=1,
            condition="If there is something blocked.",
            action="Send a concise Slack update.",
        )
        await runtime.upsert_watch(watch)

        try:
            await runtime.start()
            await runtime.run_now(watch.watch_id)
        finally:
            await runtime.stop()

        assert runtime.last_error is None
        assert session_manager.calls
        assert session_manager.calls[0]["session_id"] == f"watch:{watch.watch_id}"
        assert "Watch focus:" in session_manager.calls[0]["prompt"]
        assert "Condition to evaluate:" in session_manager.calls[0]["prompt"]
        runs = runtime.list_runs(limit=10, watch_id=watch.watch_id)
        assert len(runs) == 1
        assert runs[0].summary == "No action needed."
        assert runs[0].tool_names == ["current_time"]

    asyncio.run(scenario())


def test_watch_runtime_can_delete_watch(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            watch_enabled=True,
        )
        runtime = WatchRuntime(settings, FakeSessionManager())
        watch = WatchSpec(
            interval_minutes=15,
            condition="If a new urgent item appears.",
            action="Summarize it briefly.",
        )
        saved = await runtime.upsert_watch(watch)
        deleted = await runtime.delete_watch(saved.watch_id)

        assert deleted is True
        assert runtime.list_watches() == []

    asyncio.run(scenario())
