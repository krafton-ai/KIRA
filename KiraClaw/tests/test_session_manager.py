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
        tool_context: dict | None = None,
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
        tool_context: dict | None = None,
    ) -> RunResult:
        self.calls.append(
            {
                "prompt": prompt,
                "conversation_context": conversation_context,
                "memory_context": memory_context,
                "tool_context": tool_context,
            }
        )
        return RunResult(
            final_response=f"answer:{prompt}",
            streamed_text=f"answer:{prompt}",
        )


class StaticResultEngine:
    def __init__(self, settings: KiraClawSettings, result: RunResult) -> None:
        self.settings = settings
        self._result = result

    def run(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        conversation_context: str | None = None,
        memory_context: str | None = None,
        tool_context: dict | None = None,
    ) -> RunResult:
        return self._result


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
            assert prompt == "Remember the latest Project Coral context and continue from it."
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
            "Remember the latest Project Coral context and continue from it.",
            metadata={"source": "api"},
        )

        assert engine.calls[0]["memory_context"] == "Relevant project memory"
        assert engine.calls[0]["tool_context"] == {
            "source": "api",
            "session_id": "desktop:local",
        }
        assert len(completed_requests) == 1
        assert completed_requests[0].prompt == "Remember the latest Project Coral context and continue from it."

    asyncio.run(scenario())


def test_session_manager_uses_spoken_messages_for_group_conversation_history(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        engine = CapturingEngine(settings)
        manager = SessionManager(engine)

        async def run_with_speak(prompt: str, spoken: list[str]) -> None:
            await manager.run(
                "slack:C1:main",
                prompt,
                metadata={"source": "slack-group"},
            )
            manager.get_session_records("slack:C1:main")[-1].result = RunResult(
                final_response=f"internal:{prompt}",
                streamed_text="",
                spoken_messages=spoken,
            )

        await run_with_speak("세나, 첫번째", ["첫번째에 대한 답"])
        await manager.run(
            "slack:C1:main",
            "세나, 두번째",
            metadata={"source": "slack-group"},
        )

        assert engine.calls[-1]["conversation_context"] is not None
        assert "Assistant: 첫번째에 대한 답" in engine.calls[-1]["conversation_context"]
        assert "internal:세나, 첫번째" not in engine.calls[-1]["conversation_context"]

    asyncio.run(scenario())


def test_session_manager_keeps_group_runs_silent_without_speak_in_history(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        engine = CapturingEngine(settings)
        manager = SessionManager(engine)

        await manager.run(
            "slack:C1:main",
            "room message one",
            metadata={"source": "slack-group"},
        )
        await manager.run(
            "slack:C1:main",
            "room message two",
            metadata={"source": "slack-group"},
        )

        assert engine.calls[-1]["conversation_context"] is None

    asyncio.run(scenario())


def test_session_manager_keeps_channel_dm_runs_silent_without_speak_in_history(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        engine = CapturingEngine(settings)
        manager = SessionManager(engine)

        await manager.run(
            "telegram:dm:1",
            "dm message one",
            metadata={"source": "telegram-dm"},
        )
        await manager.run(
            "telegram:dm:1",
            "dm message two",
            metadata={"source": "telegram-dm"},
        )

        assert engine.calls[-1]["conversation_context"] is None

    asyncio.run(scenario())


def test_session_manager_calls_record_observer_after_run_completion(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        observed: list[tuple[str, str]] = []

        def record_observer(record) -> None:
            observed.append((record.run_id, record.state))

        manager = SessionManager(
            FakeEngine(settings),
            record_observer=record_observer,
        )

        record = await manager.run("desktop:local", "hello")

        assert observed == [(record.run_id, "completed")]

    asyncio.run(scenario())


def test_session_manager_skips_memory_save_for_silent_group_runs(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        saved_requests = []

        async def on_record_complete(request) -> None:
            saved_requests.append(request)

        manager = SessionManager(
            CapturingEngine(settings),
            on_record_complete=on_record_complete,
        )

        await manager.run(
            "discord:123:main",
            "room message one",
            metadata={"source": "discord-group"},
        )

        assert saved_requests == []

    asyncio.run(scenario())


def test_session_manager_skips_memory_save_for_short_small_talk(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        saved_requests = []

        async def on_record_complete(request) -> None:
            saved_requests.append(request)

        manager = SessionManager(
            StaticResultEngine(
                settings,
                RunResult(
                    final_response="안녕! 반가워.",
                    streamed_text="",
                    spoken_messages=["안녕! 반가워."],
                ),
            ),
            on_record_complete=on_record_complete,
        )

        await manager.run(
            "desktop:local",
            "안녕",
            metadata={"source": "api"},
        )

        assert saved_requests == []

    asyncio.run(scenario())


def test_session_manager_saves_explicit_memory_request(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        saved_requests = []

        async def on_record_complete(request) -> None:
            saved_requests.append(request)

        manager = SessionManager(
            StaticResultEngine(
                settings,
                RunResult(
                    final_response="기억해둘게. 앞으로 보고서는 PDF로 줄게.",
                    streamed_text="",
                    spoken_messages=["기억해둘게. 앞으로 보고서는 PDF로 줄게."],
                ),
            ),
            on_record_complete=on_record_complete,
        )

        await manager.run(
            "desktop:local",
            "앞으로 보고서는 PDF로 줘. 기억해줘.",
            metadata={"source": "api"},
        )

        assert len(saved_requests) == 1
        assert saved_requests[0].response == "기억해둘게. 앞으로 보고서는 PDF로 줄게."

    asyncio.run(scenario())


def test_session_manager_saves_toolful_run_even_without_memory_words(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        saved_requests = []

        async def on_record_complete(request) -> None:
            saved_requests.append(request)

        manager = SessionManager(
            StaticResultEngine(
                settings,
                RunResult(
                    final_response="Confluence 연결을 완료했고 기본 페이지 ID도 설정했어.",
                    streamed_text="",
                    spoken_messages=["Confluence 연결을 완료했고 기본 페이지 ID도 설정했어."],
                    tool_events=[{"phase": "start", "name": "write"}],
                ),
            ),
            on_record_complete=on_record_complete,
        )

        await manager.run(
            "desktop:local",
            "Confluence 연동을 마무리해줘.",
            metadata={"source": "api"},
        )

        assert len(saved_requests) == 1

    asyncio.run(scenario())
