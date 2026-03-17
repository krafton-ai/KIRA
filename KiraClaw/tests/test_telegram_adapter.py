import asyncio
from kiraclaw_agentd.engine import RunResult
from kiraclaw_agentd.session_manager import RunRecord
from kiraclaw_agentd.settings import KiraClawSettings
from kiraclaw_agentd.telegram_adapter import (
    TelegramGateway,
    _build_delivery_context_prefix,
    _clean_prompt_text,
    _display_name,
    _is_authorized_user_name,
    _matchable_name,
    _reply_to_message_id,
    _session_id_from_message,
    _should_handle_message,
)


def test_display_name_prefers_username() -> None:
    assert _display_name({"username": "jiho"}) == "@jiho"
    assert _display_name({"first_name": "Jiho", "last_name": "Jeon"}) == "Jiho Jeon"


def test_matchable_name_includes_username_and_full_name() -> None:
    assert _matchable_name({"username": "jiho", "first_name": "Jiho", "last_name": "Jeon"}) == "@jiho Jiho Jeon"
    assert _matchable_name({"first_name": "전", "last_name": "지호"}) == "전 지호"


def test_telegram_prompt_cleanup_strips_bot_mention() -> None:
    assert _clean_prompt_text("  @kira_bot   check   this  ", "kira_bot", mention=True) == "check this"
    assert _clean_prompt_text("  hello   there ", "kira_bot", mention=False) == "hello there"


def test_telegram_message_filter_accepts_private_and_mentions() -> None:
    private = {
        "chat": {"id": 1, "type": "private"},
        "from": {"id": 10, "is_bot": False},
        "text": "hello",
    }
    group = {
        "chat": {"id": -1, "type": "group"},
        "from": {"id": 10, "is_bot": False},
        "text": "@kira_bot hello",
    }
    reply = {
        "chat": {"id": -1, "type": "group"},
        "from": {"id": 10, "is_bot": False},
        "text": "follow up",
        "reply_to_message": {"from": {"id": 999}},
    }

    assert _should_handle_message(private, "kira_bot", 999) is True
    assert _should_handle_message(group, "kira_bot", 999) is True
    assert _should_handle_message(reply, "kira_bot", 999) is True
    assert _should_handle_message({"chat": {"type": "group"}, "from": {"is_bot": False}, "text": "hello"}, "kira_bot", 999) is False


def test_telegram_message_sessions_and_reply_targets() -> None:
    private = {"chat": {"id": 1, "type": "private"}, "message_id": 77}
    group = {
        "chat": {"id": -2, "type": "group"},
        "message_id": 88,
        "reply_to_message": {"message_id": 10},
    }

    assert _session_id_from_message(private) == "telegram:dm:1"
    assert _reply_to_message_id(private) is None
    assert _session_id_from_message(group) == "telegram:-2:10"
    assert _reply_to_message_id(group) == 88


def test_telegram_authorized_names_use_substring_match() -> None:
    assert _is_authorized_user_name("@jiho", "jiho, kris") is True
    assert _is_authorized_user_name("전지호", "jiho, 전지호") is True
    assert _is_authorized_user_name("전 지호", "jiho, 전지호") is True
    assert _is_authorized_user_name("someone else", "jiho, 전지호") is False


def test_telegram_delivery_context_prefix_includes_chat_and_reply() -> None:
    context = _build_delivery_context_prefix(12345, 99)
    assert "chat_id: 12345" in context
    assert "reply_to_message_id: 99" in context


class _FakeSessionManager:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def run(self, **kwargs) -> RunRecord:
        self.calls.append(kwargs)
        return RunRecord(
            run_id="run-1",
            session_id=kwargs["session_id"],
            state="completed",
            prompt=kwargs["prompt"],
            created_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            result=RunResult(final_response="telegram ok", streamed_text="telegram ok"),
            metadata=kwargs.get("metadata", {}),
        )


def test_telegram_run_for_message_uses_session_manager_and_publish(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            telegram_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = TelegramGateway(session_manager, settings)
        sent: list[dict] = []

        async def fake_send(chat_id, text, reply_to_message_id=None):
            sent.append(
                {
                    "chat_id": chat_id,
                    "text": text,
                    "reply_to_message_id": reply_to_message_id,
                }
            )

        gateway.send_message = fake_send  # type: ignore[method-assign]

        message = {
            "chat": {"id": 123, "type": "private"},
            "from": {"id": 10, "username": "jiho"},
            "message_id": 50,
            "text": "hello",
        }

        await gateway._run_for_message(
            message=message,
            session_id="telegram:dm:123",
            chat_id=123,
            reply_to_message_id=None,
            prompt="hello",
            user_name="@jiho",
            mention=False,
        )

        assert session_manager.calls[0]["metadata"]["source"] == "telegram-dm"
        assert "chat_id: 123" in session_manager.calls[0]["context_prefix"]
        assert sent == [{"chat_id": 123, "text": "telegram ok", "reply_to_message_id": None}]

    asyncio.run(scenario())


def test_telegram_poll_loop_recovers_after_transient_error(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            telegram_enabled=False,
        )
        gateway = TelegramGateway(_FakeSessionManager(), settings)
        calls = {"count": 0}

        async def fake_api(method, payload=None):
            await asyncio.sleep(0)
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("temporary polling error")
            return {"ok": True, "result": []}

        gateway._api = fake_api  # type: ignore[method-assign]

        task = asyncio.create_task(gateway._poll_loop())
        await asyncio.sleep(2.3)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert calls["count"] >= 2
        assert gateway.state == "running"
        assert gateway.last_error is None

    asyncio.run(scenario())


def test_telegram_messages_from_same_user_are_debounced_and_merged(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            telegram_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = TelegramGateway(session_manager, settings, debounce_seconds=0.05)
        sent: list[dict] = []

        async def fake_send(chat_id, text, reply_to_message_id=None):
            sent.append(
                {
                    "chat_id": chat_id,
                    "text": text,
                    "reply_to_message_id": reply_to_message_id,
                }
            )

        gateway.send_message = fake_send  # type: ignore[method-assign]
        gateway.identity = {"id": 999, "username": "jiho_kira_bot", "first_name": "지호봇"}

        message1 = {
            "chat": {"id": 123, "type": "private"},
            "from": {"id": 10, "username": "batteryho", "first_name": "지호", "last_name": "전", "is_bot": False},
            "message_id": 50,
            "text": "first",
        }
        message2 = {
            "chat": {"id": 123, "type": "private"},
            "from": {"id": 10, "username": "batteryho", "first_name": "지호", "last_name": "전", "is_bot": False},
            "message_id": 51,
            "text": "second",
        }

        await gateway._handle_message(message1)
        await gateway._handle_message(message2)
        await asyncio.sleep(0.12)

        assert len(session_manager.calls) == 1
        assert session_manager.calls[0]["prompt"] == "first\nsecond"
        assert sent == [{"chat_id": 123, "text": "telegram ok", "reply_to_message_id": None}]

    asyncio.run(scenario())
