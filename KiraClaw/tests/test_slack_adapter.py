import asyncio
import logging

from kiraclaw_agentd.engine import RunResult
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
            mention=False,
            client=client,
        )
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
            mention=False,
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
            mention=False,
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
            mention=False,
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
            mention=False,
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
            {"channel": "C1", "text": "두번째 말\n\nUsed: read, bash", "thread_ts": "111.222"},
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
