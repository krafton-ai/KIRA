from __future__ import annotations

import asyncio

from kiraclaw_agentd.engine import RunResult
from kiraclaw_agentd.session_manager import SessionManager
from kiraclaw_agentd.settings import KiraClawSettings


class FakeEngine:
    def __init__(self, settings: KiraClawSettings) -> None:
        self.settings = settings

    def run(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        conversation_context: str | None = None,
        memory_context: str | None = None,
    ) -> RunResult:
        return RunResult(final_response=prompt, streamed_text=prompt)


class CapturingEngine:
    def __init__(self, settings: KiraClawSettings) -> None:
        self.settings = settings
        self.calls: list[dict[str, str | None]] = []

    def run(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        conversation_context: str | None = None,
        memory_context: str | None = None,
    ) -> RunResult:
        self.calls.append(
            {
                "prompt": prompt,
                "conversation_context": conversation_context,
                "memory_context": memory_context,
            }
        )
        return RunResult(
            final_response=f"answer:{prompt}",
            streamed_text=f"answer:{prompt}",
        )


def test_session_manager_caps_record_history_per_session(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            session_record_limit=2,
        )
        manager = SessionManager(FakeEngine(settings))

        await manager.run("desktop:local", "first")
        await manager.run("desktop:local", "second")
        await manager.run("desktop:local", "third")

        records = manager.get_session_records("desktop:local")
        assert [record.prompt for record in records] == ["second", "third"]
        assert all(record.state == "completed" for record in records)

    asyncio.run(scenario())


def test_session_manager_releases_idle_lane_but_keeps_records(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            session_idle_seconds=0.05,
        )
        manager = SessionManager(FakeEngine(settings))

        await manager.run("slack:thread:123", "hello")
        await asyncio.sleep(0.15)

        assert manager.list_sessions() == [
            {
                "session_id": "slack:thread:123",
                "queued_runs": 0,
                "active": False,
                "latest_state": "completed",
                "latest_run_id": manager.get_session_records("slack:thread:123")[-1].run_id,
                "latest_finished_at": manager.get_session_records("slack:thread:123")[-1].finished_at,
            }
        ]
        assert "slack:thread:123" not in manager._lanes
        assert [record.prompt for record in manager.get_session_records("slack:thread:123")] == ["hello"]

        await manager.stop()

    asyncio.run(scenario())


def test_session_manager_passes_recent_conversation_context(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        engine = CapturingEngine(settings)
        manager = SessionManager(engine)

        await manager.run("desktop:local", "hello")
        await manager.run("desktop:local", "what about yesterday?")

        assert engine.calls[0]["conversation_context"] is None
        assert engine.calls[1]["conversation_context"] is not None
        assert "User: hello" in engine.calls[1]["conversation_context"]
        assert "Assistant: answer:hello" in engine.calls[1]["conversation_context"]
        assert engine.calls[1]["memory_context"] is None

    asyncio.run(scenario())


def test_session_manager_uses_memory_context_provider_and_completion_hook(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        engine = CapturingEngine(settings)
        completed_requests = []

        def memory_context_provider(prompt: str, session_id: str, metadata: dict) -> str | None:
            assert prompt == "need project context"
            assert session_id == "desktop:local"
            assert metadata["source"] == "api"
            return "Relevant project memory"

        async def on_record_complete(request) -> None:
            completed_requests.append(request)

        manager = SessionManager(
            engine,
            memory_context_provider=memory_context_provider,
            on_record_complete=on_record_complete,
        )

        await manager.run(
            "desktop:local",
            "need project context",
            metadata={"source": "api"},
        )

        assert engine.calls[0]["memory_context"] == "Relevant project memory"
        assert len(completed_requests) == 1
        assert completed_requests[0].prompt == "need project context"

    asyncio.run(scenario())


def test_session_manager_skips_memory_for_watch_runs(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        engine = CapturingEngine(settings)
        completed_requests = []

        def memory_context_provider(prompt: str, session_id: str, metadata: dict) -> str | None:
            raise AssertionError("watch runs should not request long-term memory")

        async def on_record_complete(request) -> None:
            completed_requests.append(request)

        manager = SessionManager(
            engine,
            memory_context_provider=memory_context_provider,
            on_record_complete=on_record_complete,
        )

        await manager.run(
            "watch:test",
            "check every 5 minutes",
            metadata={"source": "watch"},
        )

        assert engine.calls[0]["memory_context"] is None
        assert completed_requests == []

    asyncio.run(scenario())
