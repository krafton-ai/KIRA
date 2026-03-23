import asyncio

from kiraclaw_agentd.discord_adapter import (
    DiscordGateway,
    _build_delivery_context_prefix,
    _clean_prompt_text,
    _display_name,
    _is_authorized_user_name,
    _is_human_message,
    _matchable_name,
    _reply_to_message_id,
    _resolve_message_mentions,
    _session_id_from_message,
)
from kiraclaw_agentd.engine import RunResult
from kiraclaw_agentd.session_manager import RunRecord
from kiraclaw_agentd.settings import KiraClawSettings


class _FakeUser:
    def __init__(self, *, user_id: int, name: str, display_name: str | None = None, global_name: str | None = None, bot: bool = False) -> None:
        self.id = user_id
        self.name = name
        self.display_name = display_name or name
        self.global_name = global_name
        self.bot = bot


class _FakeChannel:
    def __init__(self, channel_id: int, name: str | None = None, history_messages: list[object] | None = None) -> None:
        self.id = channel_id
        self.name = name or str(channel_id)
        self._history_messages = list(history_messages or [])

    def history(self, **_kwargs):
        async def generator():
            for message in self._history_messages:
                yield message

        return generator()


class _FakeRole:
    def __init__(self, role_id: int, name: str) -> None:
        self.id = role_id
        self.name = name


class _FakeMessage:
    def __init__(
        self,
        *,
        channel_id: int,
        message_id: int,
        content: str,
        author: _FakeUser,
        guild=None,
        raw_mentions: list[int] | None = None,
        attachments: list[object] | None = None,
        mentions: list[object] | None = None,
        channel_mentions: list[object] | None = None,
        role_mentions: list[object] | None = None,
        channel: _FakeChannel | None = None,
    ) -> None:
        self.channel = channel or _FakeChannel(channel_id)
        self.id = message_id
        self.content = content
        self.author = author
        self.guild = guild
        self.raw_mentions = raw_mentions or []
        self.attachments = attachments or []
        self.mentions = mentions or []
        self.channel_mentions = channel_mentions or []
        self.role_mentions = role_mentions or []


class _FakeAttachment:
    def __init__(self, *, filename: str, url: str, content_type: str = "application/pdf", size: int = 0) -> None:
        self.filename = filename
        self.url = url
        self.content_type = content_type
        self.size = size


def test_discord_display_name_and_matchable_name() -> None:
    user = _FakeUser(user_id=10, name="batteryho", display_name="Jiho Jeon", global_name="지호")
    assert _display_name(user) == "Jiho Jeon"
    assert _matchable_name(user) == "@batteryho Jiho Jeon 지호"


def test_discord_prompt_cleanup_strips_bot_mention() -> None:
    assert _clean_prompt_text("  <@123>   check   this  ", 123, mention=True, agent_name="세나") == "세나 check this"
    assert _clean_prompt_text("  hello   there ", 123, mention=False) == "hello there"


def test_discord_resolves_user_channel_and_role_mentions_into_prompt_text() -> None:
    text = _resolve_message_mentions(
        _FakeMessage(
            channel_id=1,
            message_id=1,
            content="<@123> ask <@456> in <#789> with <@&321>",
            author=_FakeUser(user_id=10, name="jiho"),
            mentions=[_FakeUser(user_id=456, name="alice", display_name="Alice")],
            channel_mentions=[_FakeChannel(789, "project-updates")],
            role_mentions=[_FakeRole(321, "backend")],
        ),
        "<@123> ask <@456> in <#789> with <@&321>",
        123,
        mention=True,
        agent_name="세나",
    )
    assert text == "세나 ask @Alice in #project-updates with @backend"


def test_discord_human_message_and_sessions() -> None:
    dm = _FakeMessage(channel_id=1, message_id=50, content="hello", author=_FakeUser(user_id=10, name="jiho"))
    group = _FakeMessage(channel_id=2, message_id=60, content="hello", author=_FakeUser(user_id=10, name="jiho"), guild=object())
    bot_message = _FakeMessage(channel_id=3, message_id=70, content="hello", author=_FakeUser(user_id=11, name="bot", bot=True))

    assert _is_human_message(dm) is True
    assert _is_human_message(group) is True
    assert _is_human_message(
        _FakeMessage(
            channel_id=4,
            message_id=80,
            content="",
            author=_FakeUser(user_id=10, name="jiho"),
            attachments=[_FakeAttachment(filename="report.pdf", url="https://cdn.discordapp.com/report.pdf")],
        )
    ) is True
    assert _is_human_message(bot_message) is False
    assert _session_id_from_message(dm) == "discord:dm:1"
    assert _session_id_from_message(group) == "discord:2:main"
    assert _reply_to_message_id(group) == 60


def test_discord_authorized_names_use_substring_match() -> None:
    assert _is_authorized_user_name("@jiho Jiho Jeon", "jiho, 전지호") is True
    assert _is_authorized_user_name("전지호", "jiho, 전지호") is True
    assert _is_authorized_user_name("someone else", "jiho, 전지호") is False


def test_discord_delivery_context_prefix_includes_channel_and_reply() -> None:
    context = _build_delivery_context_prefix(12345, 99)
    assert "channel_id: 12345" in context
    assert "reply_to_message_id: 99" in context


class _FakeSessionManager:
    def __init__(self, *, spoken: list[str] | None = None, final_response: str = "internal discord ok") -> None:
        self.calls: list[dict] = []
        self._spoken = ["discord ok"] if spoken is None else list(spoken)
        self._final_response = final_response

    async def run(self, **kwargs) -> RunRecord:
        self.calls.append(kwargs)
        return RunRecord(
            run_id="run-1",
            session_id=kwargs["session_id"],
            state="completed",
            prompt=kwargs["prompt"],
            created_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            result=RunResult(
                final_response=self._final_response,
                streamed_text="discord ok",
                spoken_messages=self._spoken,
            ),
            metadata=kwargs.get("metadata", {}),
        )


def test_discord_run_for_message_uses_session_manager_and_publish(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            discord_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = DiscordGateway(session_manager, settings)
        gateway.identity = {"id": 999, "name": "kira"}
        sent: list[dict] = []

        async def fake_send(channel_id, text, reply_to_message_id=None):
            sent.append({"channel_id": channel_id, "text": text, "reply_to_message_id": reply_to_message_id})

        gateway.send_message = fake_send  # type: ignore[method-assign]
        message = _FakeMessage(
            channel_id=123,
            message_id=50,
            content="hello",
            author=_FakeUser(user_id=10, name="jiho", display_name="Jiho"),
        )

        await gateway._run_for_message(
            message=message,
            session_id="discord:dm:123",
            channel_id=123,
            reply_to_message_id=50,
            prompt="hello",
            user_name="Jiho",
            mention=False,
        )

        assert session_manager.calls[0]["metadata"]["source"] == "discord-dm"
        assert "channel_id: 123" in session_manager.calls[0]["context_prefix"]
        assert sent == [{"channel_id": 123, "text": "discord ok", "reply_to_message_id": 50}]

    asyncio.run(scenario())


def test_discord_run_for_group_message_includes_recent_channel_history(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            discord_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = DiscordGateway(session_manager, settings)
        gateway.identity = {"id": 999, "name": "kira"}
        sent: list[dict] = []

        async def fake_send(channel_id, text, reply_to_message_id=None):
            sent.append({"channel_id": channel_id, "text": text, "reply_to_message_id": reply_to_message_id})

        gateway.send_message = fake_send  # type: ignore[method-assign]

        history_messages = [
            _FakeMessage(
                channel_id=123,
                message_id=40,
                content="earlier question",
                author=_FakeUser(user_id=10, name="jiho", display_name="Jiho"),
                guild=object(),
            ),
            _FakeMessage(
                channel_id=123,
                message_id=41,
                content="earlier answer",
                author=_FakeUser(user_id=999, name="kira", display_name="KIRA", bot=True),
                guild=object(),
            ),
        ]
        channel = _FakeChannel(123, history_messages=history_messages)
        message = _FakeMessage(
            channel_id=123,
            message_id=50,
            content="current question",
            author=_FakeUser(user_id=10, name="jiho", display_name="Jiho"),
            guild=object(),
            channel=channel,
        )

        await gateway._run_for_message(
            message=message,
            session_id="discord:123:main",
            channel_id=123,
            reply_to_message_id=50,
            prompt="current question",
            user_name="Jiho",
            mention=False,
        )

        context_prefix = session_manager.calls[0]["context_prefix"]
        assert "Discord conversation history from this channel/thread before the current request:" in context_prefix
        assert "Jiho: earlier question" in context_prefix
        assert f"{settings.agent_name}: earlier answer" in context_prefix
        assert sent == [{"channel_id": 123, "text": "discord ok", "reply_to_message_id": 50}]

    asyncio.run(scenario())


def test_discord_messages_from_same_user_are_debounced_and_merged(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            discord_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = DiscordGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"id": 999, "name": "kira"}
        sent: list[dict] = []

        async def fake_send(channel_id, text, reply_to_message_id=None):
            sent.append({"channel_id": channel_id, "text": text, "reply_to_message_id": reply_to_message_id})

        gateway.send_message = fake_send  # type: ignore[method-assign]

        message1 = _FakeMessage(
            channel_id=123,
            message_id=50,
            content="first",
            author=_FakeUser(user_id=10, name="batteryho", display_name="지호"),
        )
        message2 = _FakeMessage(
            channel_id=123,
            message_id=51,
            content="second",
            author=_FakeUser(user_id=10, name="batteryho", display_name="지호"),
        )

        await gateway._handle_message(message1)
        await gateway._handle_message(message2)
        await asyncio.sleep(0.12)

        assert len(session_manager.calls) == 1
        assert session_manager.calls[0]["prompt"] == "first\nsecond"
        assert sent == [{"channel_id": 123, "text": "discord ok", "reply_to_message_id": 51}]

    asyncio.run(scenario())


def test_discord_attachment_message_without_text_is_processed(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            discord_enabled=False,
        )
        session_manager = _FakeSessionManager()
        gateway = DiscordGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"id": 999, "name": "kira"}
        sent: list[dict] = []

        async def fake_send(channel_id, text, reply_to_message_id=None):
            sent.append({"channel_id": channel_id, "text": text, "reply_to_message_id": reply_to_message_id})

        gateway.send_message = fake_send  # type: ignore[method-assign]

        message = _FakeMessage(
            channel_id=123,
            message_id=50,
            content="",
            author=_FakeUser(user_id=10, name="batteryho", display_name="지호"),
            attachments=[
                _FakeAttachment(
                    filename="report.pdf",
                    url="https://cdn.discordapp.com/attachments/C1/F1/report.pdf",
                    content_type="application/pdf",
                    size=2048,
                )
            ],
        )

        await gateway._handle_message(message)
        await asyncio.sleep(0.12)

        assert len(session_manager.calls) == 1
        prompt = session_manager.calls[0]["prompt"]
        assert "Attached Discord files:" in prompt
        assert "report.pdf (application/pdf, size_bytes=2048)" in prompt
        assert "Use discord_download_attachment" in prompt
        assert "url: https://cdn.discordapp.com/attachments/C1/F1/report.pdf" in prompt
        assert sent == [{"channel_id": 123, "text": "discord ok", "reply_to_message_id": 50}]

    asyncio.run(scenario())


def test_discord_group_messages_are_handled_as_room_transcript_without_direct_call_gate(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            discord_enabled=False,
            agent_name="세나",
        )
        session_manager = _FakeSessionManager(spoken=[], final_response="internal only")
        gateway = DiscordGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"id": 999, "name": "kira"}
        sent: list[dict] = []

        async def fake_send(channel_id, text, reply_to_message_id=None):
            sent.append({"channel_id": channel_id, "text": text, "reply_to_message_id": reply_to_message_id})

        gateway.send_message = fake_send  # type: ignore[method-assign]

        message1 = _FakeMessage(
            channel_id=777,
            message_id=10,
            content="우리 회의 몇시지?",
            author=_FakeUser(user_id=10, name="jiho", display_name="Jiho"),
            guild=object(),
        )
        message2 = _FakeMessage(
            channel_id=777,
            message_id=11,
            content="아까 문서 업데이트됨",
            author=_FakeUser(user_id=11, name="mina", display_name="Mina"),
            guild=object(),
        )

        await gateway._handle_message(message1)
        await gateway._handle_message(message2)
        await asyncio.sleep(0.12)

        assert len(session_manager.calls) == 1
        assert session_manager.calls[0]["metadata"]["source"] == "discord-group"
        assert session_manager.calls[0]["prompt"] == "Recent room messages:\n- Jiho: 우리 회의 몇시지?\n- Mina: 아까 문서 업데이트됨"
        assert sent == []

    asyncio.run(scenario())


def test_discord_handle_message_resolves_inbound_channel_mention(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
            discord_enabled=False,
            agent_name="세나",
        )
        session_manager = _FakeSessionManager(spoken=[], final_response="internal only")
        gateway = DiscordGateway(session_manager, settings, debounce_seconds=0.05)
        gateway.identity = {"id": 999, "name": "kira"}
        sent: list[dict] = []

        async def fake_send(channel_id, text, reply_to_message_id=None):
            sent.append({"channel_id": channel_id, "text": text, "reply_to_message_id": reply_to_message_id})

        gateway.send_message = fake_send  # type: ignore[method-assign]

        message = _FakeMessage(
            channel_id=777,
            message_id=10,
            content="<@999> <#12345> 로 올려줘",
            author=_FakeUser(user_id=10, name="jiho", display_name="Jiho"),
            guild=object(),
            raw_mentions=[999],
            channel_mentions=[_FakeChannel(12345, "announcements")],
        )

        await gateway._handle_message(message)
        await asyncio.sleep(0.12)

        assert len(session_manager.calls) == 1
        assert session_manager.calls[0]["prompt"] == "Recent room messages:\n- Jiho: 세나 #announcements 로 올려줘"
        assert sent == []

    asyncio.run(scenario())
