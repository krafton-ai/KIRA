import asyncio
import logging
from types import SimpleNamespace

from kiraclaw_agentd.engine import RunResult
from kiraclaw_agentd.observer_service import InflightMessageContext
from kiraclaw_agentd.slack_adapter import (
    SlackGateway,
    _build_delivery_context_prefix,
    _clean_prompt_text,
    _is_authorized_user_name,
    _is_human_message_event,
    _parse_allowed_names,
    _reply_thread_ts_from_event,
    _session_id_from_event,
)
from kiraclaw_agentd.session_manager import RunRecord
from kiraclaw_agentd.settings import KiraClawSettings


def test_clean_prompt_text_strips_app_mentions_and_normalizes_whitespace() -> None:
    text = "  <@U123ABC>   please   summarize   this thread  "
    assert _clean_prompt_text(text, "U123ABC", mention=True, agent_name="세나") == "세나 please summarize this thread"


def test_clean_prompt_text_keeps_dm_text_intact() -> None:
    assert _clean_prompt_text("  hello   from   dm  ", None, mention=False) == "hello from dm"


def test_clean_prompt_text_keeps_other_user_mentions_intact() -> None:
    text = " <@UBOT>   <@U456DEF>  에게   보내줘 "
    assert _clean_prompt_text(text, "UBOT", mention=True, agent_name="세나") == "세나 <@U456DEF> 에게 보내줘"


def test_clean_prompt_text_keeps_channel_mentions_intact_before_resolution() -> None:
    text = " <@UBOT>   <#C123|project-updates> 로   공유해줘 "
    assert _clean_prompt_text(text, "UBOT", mention=True, agent_name="세나") == "세나 <#C123|project-updates> 로 공유해줘"


def test_is_human_message_event_only_accepts_human_messages() -> None:
    assert _is_human_message_event({"channel_type": "im", "user": "U1"}) is True
    assert _is_human_message_event({"channel_type": "channel", "user": "U1", "text": "hello"}) is True
    assert _is_human_message_event({"channel_type": "im", "subtype": "file_share", "user": "U1", "files": [{}]}) is True
    assert _is_human_message_event({"channel_type": "im", "subtype": "message_changed", "user": "U1"}) is False
    assert _is_human_message_event({"channel_type": "im", "bot_id": "B123", "user": "U1"}) is False
    assert _is_human_message_event({"channel_type": "im"}) is False


def test_dm_messages_use_channel_session_and_main_channel_reply() -> None:
    event = {"channel": "D123", "channel_type": "im", "ts": "111.222"}
    assert _session_id_from_event(event) == "slack:dm:D123"
    assert _reply_thread_ts_from_event(event) is None


def test_channel_messages_reply_in_thread() -> None:
    event = {"channel": "C123", "channel_type": "channel", "ts": "111.222"}
    assert _session_id_from_event(event) == "slack:C123:main"
    assert _reply_thread_ts_from_event(event) == "111.222"


def test_parse_allowed_names_splits_and_trims_commas() -> None:
    assert _parse_allowed_names(" Jiho, 전지호 , Kris ") == ["Jiho", "전지호", "Kris"]


def test_authorized_user_name_uses_case_insensitive_substring_match() -> None:
    assert _is_authorized_user_name("Jiho Jeon", "Jiho, Kris") is True
    assert _is_authorized_user_name("전지호", "Jiho, 전지호") is True
    assert _is_authorized_user_name("Someone Else", "Jiho, 전지호") is False
    assert _is_authorized_user_name("Anyone", "") is True


def test_build_delivery_context_prefix_includes_channel_and_thread_when_present() -> None:
    context = _build_delivery_context_prefix("C123", "111.222")
    assert "channel_id: C123" in context
    assert "thread_ts: 111.222" in context


def test_slack_gateway_restart_recreates_handler_after_failure(tmp_path, monkeypatch) -> None:
    import kiraclaw_agentd.slack_adapter as slack_adapter_module

    created_handlers: list[object] = []

    class _FakeHandler:
        def __init__(self, app, token) -> None:
            self.app = app
            self.token = token
            self.closed = False
            created_handlers.append(self)

        async def start_async(self) -> None:
            await asyncio.sleep(0)

        async def close_async(self) -> None:
            self.closed = True

    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=True,
            slack_bot_token="xoxb-test",
            slack_app_token="xapp-test",
            slack_signing_secret="secret",
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        monkeypatch.setattr(slack_adapter_module, "AsyncSocketModeHandler", _FakeHandler)
        gateway._ensure_app = lambda: setattr(gateway, "app", SimpleNamespace(client=None))  # type: ignore[method-assign]

        async def fake_validate() -> None:
            gateway.identity = {"user_id": "UBOT"}
            gateway.socket_mode_validated = True

        gateway._validate_tokens = fake_validate  # type: ignore[method-assign]

        await gateway.start()
        first_handler = gateway.handler
        assert first_handler is not None

        await gateway.start()
        second_handler = gateway.handler
        assert second_handler is not None
        assert second_handler is not first_handler
        assert getattr(first_handler, "closed", False) is True

        await gateway.stop()

    asyncio.run(scenario())


def test_slack_gateway_recovers_after_runner_failure(tmp_path, monkeypatch) -> None:
    import kiraclaw_agentd.slack_adapter as slack_adapter_module

    handler_started = asyncio.Event()
    recovery_started = asyncio.Event()
    attempts = {"count": 0}

    class _FakeHandler:
        def __init__(self, app, token) -> None:
            self.app = app
            self.token = token

        async def start_async(self) -> None:
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("socket mode dropped")
            recovery_started.set()
            await handler_started.wait()

        async def close_async(self) -> None:
            return None

    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=True,
            slack_bot_token="xoxb-test",
            slack_app_token="xapp-test",
            slack_signing_secret="secret",
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        gateway._reconnect_delay_seconds = 0.01
        monkeypatch.setattr(slack_adapter_module, "AsyncSocketModeHandler", _FakeHandler)
        gateway._ensure_app = lambda: setattr(gateway, "app", SimpleNamespace(client=None))  # type: ignore[method-assign]

        async def fake_validate() -> None:
            gateway.identity = {"user_id": "UBOT"}
            gateway.socket_mode_validated = True

        gateway._validate_tokens = fake_validate  # type: ignore[method-assign]

        await gateway.start()
        await asyncio.wait_for(recovery_started.wait(), timeout=1.0)
        assert attempts["count"] >= 2
        assert gateway.state == "running"

        handler_started.set()
        await gateway.stop()

    asyncio.run(scenario())


class _FakeSlackClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, str | None]] = []

    async def users_info(self, user: str) -> dict:
        names = {
            "U1": {"display_name": "Jiho Jeon"},
            "U2": {"display_name": "Alice"},
        }
        return {"ok": True, "user": {"profile": names.get(user, {}), "name": user}}

    async def conversations_info(self, channel: str) -> dict:
        names = {
            "C123": {"name": "project-updates"},
            "C456": {"name": "design-review"},
        }
        return {"ok": True, "channel": names.get(channel, {"name": channel})}

    async def conversations_history(self, **_kwargs) -> dict:
        return {
            "messages": [
                {"ts": "102.0", "user": "U2", "text": "  second question  "},
                {"ts": "101.0", "bot_id": "B1", "subtype": "bot_message", "text": "<@UBOT> previous answer"},
                {"ts": "100.0", "user": "U1", "text": " first question "},
            ]
        }

    async def conversations_replies(self, **_kwargs) -> dict:
        return {
            "messages": [
                {"ts": "200.0", "user": "U1", "text": "thread start"},
                {"ts": "201.0", "bot_id": "B1", "subtype": "bot_message", "text": "thread answer"},
                {"ts": "202.0", "user": "U2", "text": "current question"},
            ]
        }

    async def chat_postMessage(self, channel: str, text: str, thread_ts: str | None = None) -> None:
        self.sent_messages.append({"channel": channel, "text": text, "thread_ts": thread_ts})


class _FakeSessionManager:
    def __init__(self, records: list[RunRecord] | None = None) -> None:
        self.records = records or []
        self.calls: list[dict] = []

    def get_session_records(self, _session_id: str) -> list[RunRecord]:
        return list(self.records)

    async def run(self, **kwargs) -> RunRecord:
        self.calls.append(kwargs)
        return RunRecord(
            run_id="run-1",
            session_id=kwargs["session_id"],
            state="completed",
            prompt=kwargs["prompt"],
            created_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            result=RunResult(final_response="internal ok", streamed_text="ok", spoken_messages=["ok"]),
            metadata=kwargs.get("metadata", {}),
        )


class _FakeObserverService:
    def __init__(self) -> None:
        self.last_inbound = None

    def classify_inflight(self, prompt: str, snapshot: dict, inbound=None) -> object:
        from kiraclaw_agentd.observer_service import ObserverDecision

        self.last_inbound = inbound

        if "어디까지" in prompt:
            return ObserverDecision("status_query", "지금 상태를 확인 중입니다.")
        return ObserverDecision("queue_next", "끝난 뒤 이어서 처리할게요.")

    def summarize_heartbeat(self, snapshot: dict) -> str:
        return "아직 작업 중입니다."


def test_build_slack_bootstrap_context_formats_recent_dm_history(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        context = await gateway._build_slack_bootstrap_context(
            client,
            {"channel": "D1", "channel_type": "im", "ts": "103.0"},
        )

        assert context is not None
        lines = context.splitlines()
        assert lines[0] == "Slack conversation history from this thread/channel before the current request:"
        assert lines[1] == "Jiho Jeon: first question"
        assert lines[2] == "KIRA: previous answer"
        assert lines[3] == "Alice: second question"

    asyncio.run(scenario())


def test_slack_inflight_status_query_is_answered_without_queueing(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager()
        session_manager.has_active_run = lambda session_id: True  # type: ignore[attr-defined]
        session_manager.build_observer_snapshot = lambda session_id: {  # type: ignore[attr-defined]
            "session_id": session_id,
            "state": "running",
            "prompt": "작업 중",
            "elapsed_seconds": 5,
            "recent_tool_events": [],
            "active_processes": [],
        }
        observer = _FakeObserverService()
        gateway = SlackGateway(session_manager, settings, observer_service=observer)
        client = _FakeSlackClient()

        handled = await gateway._maybe_handle_inflight_event(
            session_id="slack:C1:main",
            prompt="지금 어디까지 했어?",
            channel="C1",
            reply_thread_ts="111.222",
            client=client,
            inbound=InflightMessageContext(
                source="slack-group",
                mention=True,
                is_private=False,
                user_name="Jiho Jeon",
            ),
        )

        assert handled is True
        assert session_manager.calls == []
        assert observer.last_inbound is not None
        assert observer.last_inbound.mention is True
        assert client.sent_messages == [
            {"channel": "C1", "text": "지금 상태를 확인 중입니다.", "thread_ts": "111.222"}
        ]

    asyncio.run(scenario())


def test_slack_inflight_group_queue_next_is_silent_and_still_queues(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager()
        session_manager.has_active_run = lambda session_id: True  # type: ignore[attr-defined]
        session_manager.build_observer_snapshot = lambda session_id: {  # type: ignore[attr-defined]
            "session_id": session_id,
            "state": "running",
            "prompt": "작업 중",
            "elapsed_seconds": 5,
            "recent_tool_events": [],
            "active_processes": [],
        }

        class _QueueOnlyObserver:
            def classify_inflight(self, prompt: str, snapshot: dict, inbound=None) -> object:
                from kiraclaw_agentd.observer_service import ObserverDecision

                return ObserverDecision("queue_next", "")

        gateway = SlackGateway(session_manager, settings, observer_service=_QueueOnlyObserver())
        client = _FakeSlackClient()

        handled = await gateway._maybe_handle_inflight_event(
            session_id="slack:C1:main",
            prompt="그리고 이것도 봐줘",
            channel="C1",
            reply_thread_ts="111.222",
            client=client,
            inbound=InflightMessageContext(
                source="slack-group",
                mention=False,
                is_private=False,
                user_name="Jiho Jeon",
            ),
        )

        assert handled is False
        assert client.sent_messages == []

    asyncio.run(scenario())


def test_slack_run_for_event_emits_heartbeat_before_final_reply_when_explicitly_mentioned(tmp_path) -> None:
    class _SlowSessionManager(_FakeSessionManager):
        def __init__(self) -> None:
            super().__init__()
            self._running = False

        def has_active_run(self, session_id: str) -> bool:
            return self._running

        def build_observer_snapshot(self, session_id: str) -> dict | None:
            if not self._running:
                return None
            return {
                "session_id": session_id,
                "state": "running",
                "prompt": "브라우저 확인 중",
                "elapsed_seconds": 12,
                "recent_tool_events": [{"phase": "start", "name": "browser_navigate"}],
                "active_processes": [],
                "run_mention": True,
                "run_is_private": False,
            }

        async def run(self, **kwargs) -> RunRecord:
            self._running = True
            self.calls.append(kwargs)
            await asyncio.sleep(0.05)
            self._running = False
            return RunRecord(
                run_id="run-1",
                session_id=kwargs["session_id"],
                state="completed",
                prompt=kwargs["prompt"],
                created_at="2026-01-01T00:00:00Z",
                finished_at="2026-01-01T00:00:01Z",
                result=RunResult(final_response="internal ok", streamed_text="ok", spoken_messages=["ok"]),
                metadata=kwargs.get("metadata", {}),
            )

    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            observer_heartbeat_initial_seconds=0.01,
            observer_heartbeat_interval_seconds=0.02,
        )
        session_manager = _SlowSessionManager()
        gateway = SlackGateway(session_manager, settings, observer_service=_FakeObserverService())
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        await gateway._run_for_event(
            event={"channel": "C1", "channel_type": "channel", "ts": "111.222"},
            session_id="slack:C1:main",
            channel="C1",
            reply_thread_ts="111.222",
            user="U1",
            user_name="Jiho Jeon",
            prompt="hello",
            inbound=InflightMessageContext(source="slack-group", mention=True, is_private=False, user_name="Jiho Jeon"),
            client=client,
        )

        assert len(client.sent_messages) >= 2
        assert client.sent_messages[0]["text"] == "아직 작업 중입니다."
        assert client.sent_messages[-1]["text"] == "ok"

    asyncio.run(scenario())


def test_slack_queued_followup_does_not_start_duplicate_heartbeat(tmp_path) -> None:
    class _QueuedSessionManager(_FakeSessionManager):
        def __init__(self) -> None:
            super().__init__()
            self._running = True
            self.snapshot_calls = 0

        def has_active_run(self, session_id: str) -> bool:
            return self._running

        def build_observer_snapshot(self, session_id: str) -> dict | None:
            self.snapshot_calls += 1
            return {
                "session_id": session_id,
                "state": "running",
                "prompt": "이미 진행 중인 작업",
                "elapsed_seconds": 20,
                "recent_tool_events": [{"phase": "start", "name": "exec"}],
                "active_processes": [],
            }

        async def run(self, **kwargs) -> RunRecord:
            self.calls.append(kwargs)
            await asyncio.sleep(0.03)
            return RunRecord(
                run_id="run-2",
                session_id=kwargs["session_id"],
                state="completed",
                prompt=kwargs["prompt"],
                created_at="2026-01-01T00:00:00Z",
                finished_at="2026-01-01T00:00:01Z",
                result=RunResult(final_response="internal ok", streamed_text="ok", spoken_messages=["queued ok"]),
                metadata=kwargs.get("metadata", {}),
            )

    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            observer_heartbeat_initial_seconds=0.01,
            observer_heartbeat_interval_seconds=0.02,
        )
        session_manager = _QueuedSessionManager()
        gateway = SlackGateway(session_manager, settings, observer_service=_FakeObserverService())
        client = _FakeSlackClient()

        await gateway._run_for_event(
            event={"channel": "C1", "channel_type": "channel", "ts": "222.333"},
            session_id="slack:C1:main",
            channel="C1",
            reply_thread_ts="222.333",
            user="U1",
            user_name="Jiho Jeon",
            prompt="다음엔 이것도 해줘",
            inbound=InflightMessageContext(source="slack-group", mention=False, is_private=False, user_name="Jiho Jeon"),
            client=client,
        )

        assert session_manager.snapshot_calls == 0
        assert client.sent_messages == [
            {"channel": "C1", "text": "queued ok", "thread_ts": "222.333"}
        ]

    asyncio.run(scenario())


def test_build_slack_bootstrap_context_formats_recent_channel_history(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        context = await gateway._build_slack_bootstrap_context(
            client,
            {"channel": "C1", "channel_type": "channel", "ts": "103.0"},
        )

        assert context is not None
        lines = context.splitlines()
        assert lines[0] == "Slack conversation history from this thread/channel before the current request:"
        assert lines[1] == "Jiho Jeon: first question"
        assert lines[2] == "KIRA: previous answer"
        assert lines[3] == "Alice: second question"

    asyncio.run(scenario())


def test_run_for_event_bootstraps_only_when_session_has_no_local_records(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = SlackGateway(session_manager, settings)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return "Slack bootstrap"

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        event = {"channel": "D1", "channel_type": "im", "ts": "101.0"}
        await gateway._run_for_event(
            event=event,
            session_id="slack:dm:D1",
            channel="D1",
            reply_thread_ts=None,
            user="U1",
            user_name="Jiho Jeon",
            prompt="hello",
            inbound=InflightMessageContext(source="slack-dm", mention=False, is_private=True, user_name="Jiho Jeon"),
            client=client,
        )
        assert session_manager.calls[0]["metadata"]["source"] == "slack-dm"
        assert session_manager.calls[0]["metadata"]["mention"] is False
        assert session_manager.calls[0]["metadata"]["is_private"] is True
        assert "channel_id: D1" in session_manager.calls[0]["context_prefix"]
        assert "Slack bootstrap" in session_manager.calls[0]["context_prefix"]

        session_manager.records = [
            RunRecord(
                run_id="existing",
                session_id="slack:dm:D1",
                state="completed",
                prompt="older",
                created_at="2026-01-01T00:00:00Z",
                finished_at="2026-01-01T00:00:01Z",
                result=RunResult(final_response="older answer", streamed_text="older answer"),
            )
        ]
        await gateway._run_for_event(
            event=event,
            session_id="slack:dm:D1",
            channel="D1",
            reply_thread_ts=None,
            user="U1",
            user_name="Jiho Jeon",
            prompt="hello again",
            inbound=InflightMessageContext(source="slack-dm", mention=False, is_private=True, user_name="Jiho Jeon"),
            client=client,
        )
        assert "channel_id: D1" in session_manager.calls[1]["context_prefix"]
        assert "Slack bootstrap" not in session_manager.calls[1]["context_prefix"]

    asyncio.run(scenario())


def test_run_for_channel_event_refreshes_bootstrap_even_with_local_records(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager(
            records=[
                RunRecord(
                    run_id="existing",
                    session_id="slack:C1:main",
                    state="completed",
                    prompt="older",
                    created_at="2026-01-01T00:00:00Z",
                    finished_at="2026-01-01T00:00:01Z",
                    result=RunResult(final_response="older answer", streamed_text="older answer"),
                )
            ]
        )
        gateway = SlackGateway(session_manager, settings)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return "Slack bootstrap"

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        event = {"channel": "C1", "channel_type": "channel", "ts": "202.0"}
        await gateway._run_for_event(
            event=event,
            session_id="slack:C1:main",
            channel="C1",
            reply_thread_ts="202.0",
            user="U1",
            user_name="Jiho Jeon",
            prompt="channel question",
            inbound=InflightMessageContext(source="slack-group", mention=False, is_private=False, user_name="Jiho Jeon"),
            client=client,
        )

        assert "Slack bootstrap" in session_manager.calls[0]["context_prefix"]

    asyncio.run(scenario())


def test_run_for_thread_event_refreshes_bootstrap_even_with_local_records(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager(
            records=[
                RunRecord(
                    run_id="existing",
                    session_id="slack:C1:200.0",
                    state="completed",
                    prompt="older",
                    created_at="2026-01-01T00:00:00Z",
                    finished_at="2026-01-01T00:00:01Z",
                    result=RunResult(final_response="older answer", streamed_text="older answer"),
                )
            ]
        )
        gateway = SlackGateway(session_manager, settings)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return "Slack bootstrap"

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        event = {"channel": "C1", "channel_type": "channel", "thread_ts": "200.0", "ts": "202.0"}
        await gateway._run_for_event(
            event=event,
            session_id="slack:C1:200.0",
            channel="C1",
            reply_thread_ts="200.0",
            user="U1",
            user_name="Jiho Jeon",
            prompt="thread question",
            inbound=InflightMessageContext(source="slack-group", mention=False, is_private=False, user_name="Jiho Jeon"),
            client=client,
        )

        assert "Slack bootstrap" in session_manager.calls[0]["context_prefix"]

    asyncio.run(scenario())


def test_run_for_thread_event_warns_when_history_unavailable(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = SlackGateway(session_manager, settings)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return None

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        event = {"channel": "C1", "channel_type": "channel", "thread_ts": "200.0", "ts": "202.0"}
        await gateway._run_for_event(
            event=event,
            session_id="slack:C1:200.0",
            channel="C1",
            reply_thread_ts="200.0",
            user="U1",
            user_name="Jiho Jeon",
            prompt="thread question",
            inbound=InflightMessageContext(source="slack-group", mention=False, is_private=False, user_name="Jiho Jeon"),
            client=client,
        )

        assert "could not be loaded for this turn" in session_manager.calls[0]["context_prefix"]

    asyncio.run(scenario())


def test_build_slack_bootstrap_context_for_thread_excludes_current_message(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        context = await gateway._build_slack_bootstrap_context(
            client,
            {"channel": "C1", "channel_type": "channel", "thread_ts": "200.0", "ts": "202.0"},
        )

        assert context is not None
        assert "Jiho Jeon: thread start" in context
        assert "KIRA: thread answer" in context
        assert "current question" not in context

    asyncio.run(scenario())


def test_build_slack_bootstrap_context_falls_back_to_retrieve_token(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            slack_retrieve_enabled=True,
            slack_retrieve_token="xoxp-test",
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def broken_replies(**_kwargs) -> dict:
            raise RuntimeError("bot token cannot read thread")

        client.conversations_replies = broken_replies  # type: ignore[method-assign]

        retrieve_client = _FakeSlackClient()
        gateway._get_retrieve_client = lambda: retrieve_client  # type: ignore[method-assign]

        context = await gateway._build_slack_bootstrap_context(
            client,
            {"channel": "C1", "channel_type": "channel", "thread_ts": "200.0", "ts": "202.0"},
        )

        assert context is not None
        assert "Jiho Jeon: thread start" in context
        assert "KIRA: thread answer" in context

    asyncio.run(scenario())


def test_slack_messages_from_same_user_are_debounced_and_merged(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = SlackGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return None

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        event1 = {"channel": "D1", "channel_type": "im", "ts": "101.0", "user": "U1", "text": "first"}
        event2 = {"channel": "D1", "channel_type": "im", "ts": "102.0", "user": "U1", "text": "second"}

        await gateway._schedule_event(event1, client, logging.getLogger("test-slack"), mention=False)
        await gateway._schedule_event(event2, client, logging.getLogger("test-slack"), mention=False)
        await asyncio.sleep(0.12)

        assert len(session_manager.calls) == 1
        assert session_manager.calls[0]["prompt"] == "first\nsecond"
        assert client.sent_messages == [{"channel": "D1", "text": "ok", "thread_ts": None}]

    asyncio.run(scenario())


def test_schedule_event_resolves_tagged_user_name_into_prompt(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = SlackGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return None

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        async def fake_users_info(user: str) -> dict:
            names = {
                "U1": {"display_name": "Jiho Jeon"},
                "U2": {"display_name": "Gisang Lee (이기상) [KAI]"},
            }
            return {"ok": True, "user": {"profile": names.get(user, {}), "name": user}}

        client.users_info = fake_users_info  # type: ignore[method-assign]

        event = {
            "channel": "D1",
            "channel_type": "im",
            "ts": "101.0",
            "user": "U1",
            "text": "<@UBOT> <@U2> 님한테 전달해줘",
        }

        await gateway._schedule_event(event, client, logging.getLogger("test-slack"), mention=True)
        await asyncio.sleep(0.12)

        assert len(session_manager.calls) == 1
        assert session_manager.calls[0]["prompt"] == "KIRA @Gisang Lee (이기상) [KAI] 님한테 전달해줘"
        assert "Slack references explicitly mentioned in the current conversation:" in session_manager.calls[0]["context_prefix"]
        assert "- user @Gisang Lee (이기상) [KAI]: user_id=U2, mention_token=<@U2>" in session_manager.calls[0]["context_prefix"]

    asyncio.run(scenario())


def test_schedule_event_resolves_tagged_channel_name_into_prompt(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = SlackGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return None

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        event = {
            "channel": "C1",
            "channel_type": "channel",
            "ts": "101.0",
            "user": "U1",
            "text": " <@UBOT>  <#C123|project-updates> 에 전달해줘 ",
        }
        await gateway._schedule_event(event, client, logging.getLogger("test-slack"), mention=True)
        await asyncio.sleep(0.1)

        assert "Jiho Jeon: KIRA #project-updates 에 전달해줘" in session_manager.calls[0]["prompt"]
        assert "- channel #project-updates: channel_id=C123, mention_token=<#C123|project-updates>" in session_manager.calls[0]["context_prefix"]

    asyncio.run(scenario())


def test_schedule_event_resolves_channel_name_from_channel_info_when_label_missing(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = SlackGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return None

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        event = {
            "channel": "C1",
            "channel_type": "channel",
            "ts": "101.0",
            "user": "U1",
            "text": " <@UBOT>  <#C456> 로 올려줘 ",
        }
        await gateway._schedule_event(event, client, logging.getLogger("test-slack"), mention=True)
        await asyncio.sleep(0.1)

        assert "Jiho Jeon: KIRA #design-review 로 올려줘" in session_manager.calls[0]["prompt"]
        assert "- channel #design-review: channel_id=C456, mention_token=<#C456|design-review>" in session_manager.calls[0]["context_prefix"]

    asyncio.run(scenario())


def test_slack_file_share_message_without_text_is_processed(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = SlackGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return None

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        event = {
            "channel": "D1",
            "channel_type": "im",
            "ts": "101.0",
            "user": "U1",
            "subtype": "file_share",
            "files": [
                {
                    "name": "report.pdf",
                    "mimetype": "application/pdf",
                    "size": 2048,
                    "url_private": "https://files.slack.com/files-pri/T1-F1/report.pdf",
                }
            ],
        }

        await gateway._schedule_event(event, client, logging.getLogger("test-slack"), mention=False)
        await asyncio.sleep(0.12)

        assert len(session_manager.calls) == 1
        prompt = session_manager.calls[0]["prompt"]
        assert "Attached Slack files:" in prompt
        assert "report.pdf (application/pdf, size_bytes=2048)" in prompt
        assert "Use slack_download_file" in prompt
        assert "url_private: https://files.slack.com/files-pri/T1-F1/report.pdf" in prompt
        assert client.sent_messages == [{"channel": "D1", "text": "ok", "thread_ts": None}]

    asyncio.run(scenario())


def test_slack_group_messages_are_handled_as_room_transcript_without_direct_call_gate(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            agent_name="세나",
        )
        class _SilentGroupSessionManager(_FakeSessionManager):
            async def run(self, **kwargs) -> RunRecord:
                self.calls.append(kwargs)
                return RunRecord(
                    run_id="run-1",
                    session_id=kwargs["session_id"],
                    state="completed",
                    prompt=kwargs["prompt"],
                    created_at="2026-01-01T00:00:00Z",
                    finished_at="2026-01-01T00:00:01Z",
                    result=RunResult(final_response="internal only", streamed_text=""),
                    metadata=kwargs.get("metadata", {}),
                )

        session_manager = _SilentGroupSessionManager()
        gateway = SlackGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return None

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        event = {
            "channel": "C1",
            "channel_type": "channel",
            "ts": "101.0",
            "user": "U1",
            "text": "상태 알려줘",
        }

        await gateway._schedule_event(event, client, logging.getLogger("test-slack"), mention=False)
        await asyncio.sleep(0.12)

        assert len(session_manager.calls) == 1
        assert session_manager.calls[0]["prompt"] == "Recent room messages:\n- Jiho Jeon: 상태 알려줘"
        assert client.sent_messages == []

    asyncio.run(scenario())


def test_slack_group_messages_share_one_room_debounce_window(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            agent_name="세나",
        )
        class _SilentGroupSessionManager(_FakeSessionManager):
            async def run(self, **kwargs) -> RunRecord:
                self.calls.append(kwargs)
                return RunRecord(
                    run_id="run-1",
                    session_id=kwargs["session_id"],
                    state="completed",
                    prompt=kwargs["prompt"],
                    created_at="2026-01-01T00:00:00Z",
                    finished_at="2026-01-01T00:00:01Z",
                    result=RunResult(final_response="internal only", streamed_text=""),
                    metadata=kwargs.get("metadata", {}),
                )

        session_manager = _SilentGroupSessionManager()
        gateway = SlackGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"user_id": "UBOT"}
        client = _FakeSlackClient()

        async def fake_bootstrap_context(*, client, event, excluded_timestamps=None):
            return None

        gateway._build_slack_bootstrap_context = fake_bootstrap_context  # type: ignore[method-assign]

        event1 = {"channel": "C1", "channel_type": "channel", "ts": "101.0", "user": "U1", "text": "첫번째"}
        event2 = {"channel": "C1", "channel_type": "channel", "ts": "102.0", "user": "U2", "text": "두번째"}

        await gateway._schedule_event(event1, client, logging.getLogger("test-slack"), mention=False)
        await gateway._schedule_event(event2, client, logging.getLogger("test-slack"), mention=False)
        await asyncio.sleep(0.12)

        assert len(session_manager.calls) == 1
        assert session_manager.calls[0]["prompt"] == (
            "Recent room messages:\n"
            "- Jiho Jeon: 첫번째\n"
            "- Alice: 두번째"
        )
        assert client.sent_messages == []

    asyncio.run(scenario())


def test_slack_publish_result_prefers_spoken_messages(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        client = _FakeSlackClient()
        record = RunRecord(
            run_id="run-1",
            session_id="slack:C1:main",
            state="completed",
            prompt="hello",
            created_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            result=RunResult(
                final_response="internal summary",
                streamed_text="",
                spoken_messages=["첫번째 말", "두번째 말"],
            ),
        )

        await gateway._publish_result(client, "C1", "111.222", record)

        assert client.sent_messages == [
            {"channel": "C1", "text": "첫번째 말", "thread_ts": "111.222"},
            {"channel": "C1", "text": "두번째 말", "thread_ts": "111.222"},
        ]

    asyncio.run(scenario())


def test_slack_publish_result_appends_tool_summary_to_last_spoken_message(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            response_trace_enabled=True,
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        client = _FakeSlackClient()
        record = RunRecord(
            run_id="run-1",
            session_id="slack:C1:main",
            state="completed",
            prompt="hello",
            created_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            result=RunResult(
                final_response="internal summary",
                streamed_text="",
                tool_events=[
                    {"phase": "start", "name": "read", "args": {}},
                    {"phase": "end", "name": "read", "result": "ok"},
                    {"phase": "start", "name": "bash", "args": {}},
                    {"phase": "end", "name": "bash", "result": "ok"},
                ],
                spoken_messages=["첫번째 말", "두번째 말"],
            ),
        )

        await gateway._publish_result(client, "C1", "111.222", record)

        assert client.sent_messages == [
            {"channel": "C1", "text": "첫번째 말", "thread_ts": "111.222"},
            {"channel": "C1", "text": "두번째 말\n\nUsed: read, bash\nElapsed: 1.0s", "thread_ts": "111.222"},
        ]

    asyncio.run(scenario())


def test_slack_group_publish_is_silent_without_speak(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        client = _FakeSlackClient()
        record = RunRecord(
            run_id="run-1",
            session_id="slack:C1:main",
            state="completed",
            prompt="hello",
            created_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            result=RunResult(final_response="internal summary", streamed_text=""),
            metadata={"source": "slack-group"},
        )

        await gateway._publish_result(client, "C1", "111.222", record)

        assert client.sent_messages == []

    asyncio.run(scenario())


def test_slack_dm_publish_is_silent_without_speak(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        client = _FakeSlackClient()
        record = RunRecord(
            run_id="run-1",
            session_id="slack:dm:D1",
            state="completed",
            prompt="hello",
            created_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            result=RunResult(final_response="internal summary", streamed_text=""),
            metadata={"source": "slack-dm"},
        )

        await gateway._publish_result(client, "D1", None, record)

        assert client.sent_messages == []

    asyncio.run(scenario())


def test_slack_dm_publish_uses_terminal_fallback_after_max_turns(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        gateway = SlackGateway(_FakeSessionManager(), settings)
        client = _FakeSlackClient()
        record = RunRecord(
            run_id="run-1",
            session_id="slack:dm:D1",
            state="completed",
            prompt="hello",
            created_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            result=RunResult(final_response="최종 정리입니다.", streamed_text="", max_turns_reached=True),
            metadata={"source": "slack-dm", "is_private": True, "mention": False},
        )

        await gateway._publish_result(client, "D1", None, record)

        assert client.sent_messages == [
            {"channel": "D1", "text": "최종 정리입니다.", "thread_ts": None}
        ]

    asyncio.run(scenario())
