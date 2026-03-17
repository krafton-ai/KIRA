import asyncio

from kiraclaw_agentd.engine import RunResult
from kiraclaw_agentd.slack_adapter import (
    SlackGateway,
    _clean_prompt_text,
    _is_authorized_user_name,
    _parse_allowed_names,
    _reply_thread_ts_from_event,
    _session_id_from_event,
    _should_handle_message,
)
from kiraclaw_agentd.session_manager import RunRecord
from kiraclaw_agentd.settings import KiraClawSettings


def test_clean_prompt_text_strips_app_mentions_and_normalizes_whitespace() -> None:
    text = "  <@U123ABC>   please   summarize   this thread  "
    assert _clean_prompt_text(text, mention=True) == "please summarize this thread"


def test_clean_prompt_text_keeps_dm_text_intact() -> None:
    assert _clean_prompt_text("  hello   from   dm  ", mention=False) == "hello from dm"


def test_should_handle_message_only_accepts_human_dms() -> None:
    assert _should_handle_message({"channel_type": "im"}) is True
    assert _should_handle_message({"channel_type": "channel"}) is False
    assert _should_handle_message({"channel_type": "im", "subtype": "message_changed"}) is False
    assert _should_handle_message({"channel_type": "im", "bot_id": "B123"}) is False


def test_dm_messages_use_channel_session_and_main_channel_reply() -> None:
    event = {"channel": "D123", "channel_type": "im", "ts": "111.222"}
    assert _session_id_from_event(event) == "slack:dm:D123"
    assert _reply_thread_ts_from_event(event) is None


def test_channel_messages_reply_in_thread() -> None:
    event = {"channel": "C123", "channel_type": "channel", "ts": "111.222"}
    assert _session_id_from_event(event) == "slack:C123:111.222"
    assert _reply_thread_ts_from_event(event) == "111.222"


def test_parse_allowed_names_splits_and_trims_commas() -> None:
    assert _parse_allowed_names(" Jiho, 전지호 , Kris ") == ["Jiho", "전지호", "Kris"]


def test_authorized_user_name_uses_case_insensitive_substring_match() -> None:
    assert _is_authorized_user_name("Jiho Jeon", "Jiho, Kris") is True
    assert _is_authorized_user_name("전지호", "Jiho, 전지호") is True
    assert _is_authorized_user_name("Someone Else", "Jiho, 전지호") is False
    assert _is_authorized_user_name("Anyone", "") is True


class _FakeSlackClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, str | None]] = []

    async def users_info(self, user: str) -> dict:
        names = {
            "U1": {"display_name": "Jiho Jeon"},
            "U2": {"display_name": "Alice"},
        }
        return {"ok": True, "user": {"profile": names.get(user, {}), "name": user}}

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
            result=RunResult(final_response="ok", streamed_text="ok"),
            metadata=kwargs.get("metadata", {}),
        )


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

        async def fake_bootstrap_context(*, client, event):
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
            mention=False,
            client=client,
        )
        assert session_manager.calls[0]["context_prefix"] == "Slack bootstrap"

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
            mention=False,
            client=client,
        )
        assert session_manager.calls[1]["context_prefix"] is None

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
