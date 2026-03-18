from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from kiraclaw_agentd.channel_delivery import ChannelDelivery
from kiraclaw_agentd.schedule_store import write_schedules
from kiraclaw_agentd.scheduler_runtime import SchedulerRuntime
from kiraclaw_agentd.settings import KiraClawSettings


class FakeSessionManager:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def run(
        self,
        session_id: str,
        prompt: str,
        metadata: dict | None = None,
        provider=None,
        model=None,
        context_prefix: str | None = None,
    ):
        self.calls.append(
            {
                "session_id": session_id,
                "prompt": prompt,
                "metadata": metadata or {},
                "context_prefix": context_prefix,
            }
        )
        return SimpleNamespace(
            state="completed",
            error=None,
            result=SimpleNamespace(
                final_response="internal scheduled response",
                public_response_text="scheduled response",
            ),
        )


class FakeSlackGateway:
    def __init__(self) -> None:
        self.configured = True
        self.messages: list[dict] = []

    async def send_message(self, channel: str, text: str, thread_ts=None) -> None:
        self.messages.append({"channel": channel, "text": text, "thread_ts": thread_ts})


class FakeTelegramGateway:
    def __init__(self) -> None:
        self.configured = True
        self.messages: list[dict] = []

    async def send_message(self, chat_id: int | str, text: str, reply_to_message_id=None) -> None:
        self.messages.append({"chat_id": chat_id, "text": text, "reply_to_message_id": reply_to_message_id})


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
        telegram_gateway = FakeTelegramGateway()
        runtime = SchedulerRuntime(
            settings,
            session_manager,
            ChannelDelivery(slack_gateway=slack_gateway, telegram_gateway=telegram_gateway),
        )

        try:
            await runtime.start()
            await asyncio.sleep(1.0)
        finally:
            await runtime.stop()

        assert runtime.last_error is None
        assert session_manager.calls
        assert session_manager.calls[0]["prompt"] == "KIRA, do the thing"
        assert "scheduled automation run" in session_manager.calls[0]["context_prefix"]
        assert slack_gateway.messages == [{"channel": "C123", "text": "scheduled response", "thread_ts": None}]
        assert telegram_gateway.messages == []

    asyncio.run(scenario())


def test_scheduler_runtime_can_deliver_to_telegram(tmp_path) -> None:
    async def scenario() -> None:
        schedule_file = tmp_path / "workspace" / "schedule_data" / "schedules.json"
        write_schedules(
            schedule_file,
            [
                {
                    "id": "sched-1",
                    "name": "Telegram shot",
                    "schedule_type": "date",
                    "schedule_value": (datetime.now(timezone.utc) + timedelta(milliseconds=300)).isoformat(),
                    "user": "U123",
                    "text": "Summarize the update",
                    "channel_type": "telegram",
                    "channel_target": "123456",
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
        telegram_gateway = FakeTelegramGateway()
        runtime = SchedulerRuntime(
            settings,
            session_manager,
            ChannelDelivery(slack_gateway=slack_gateway, telegram_gateway=telegram_gateway),
        )

        try:
            await runtime.start()
            await asyncio.sleep(1.0)
        finally:
            await runtime.stop()

        assert runtime.last_error is None
        assert telegram_gateway.messages == [{"chat_id": "123456", "text": "scheduled response", "reply_to_message_id": None}]
        assert slack_gateway.messages == []

        asyncio.run(scenario())


def test_scheduler_runtime_prefers_spoken_public_response_when_available(tmp_path) -> None:
    async def scenario() -> None:
        schedule_file = tmp_path / "workspace" / "schedule_data" / "schedules.json"
        write_schedules(
            schedule_file,
            [
                {
                    "id": "sched-1",
                    "name": "Slack spoken shot",
                    "schedule_type": "date",
                    "schedule_value": (datetime.now(timezone.utc) + timedelta(milliseconds=300)).isoformat(),
                    "user": "U123",
                    "text": "Summarize the update",
                    "channel_target": "C123",
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

        class SpokenSessionManager(FakeSessionManager):
            async def run(
                self,
                session_id: str,
                prompt: str,
                metadata: dict | None = None,
                provider=None,
                model=None,
                context_prefix: str | None = None,
            ):
                self.calls.append(
                    {
                        "session_id": session_id,
                        "prompt": prompt,
                        "metadata": metadata or {},
                        "context_prefix": context_prefix,
                    }
                )
                return SimpleNamespace(
                    state="completed",
                    error=None,
                    result=SimpleNamespace(
                        final_response="internal summary",
                        public_response_text="spoken outward reply",
                    ),
                )

        session_manager = SpokenSessionManager()
        slack_gateway = FakeSlackGateway()
        telegram_gateway = FakeTelegramGateway()
        runtime = SchedulerRuntime(
            settings,
            session_manager,
            ChannelDelivery(slack_gateway=slack_gateway, telegram_gateway=telegram_gateway),
        )

        try:
            await runtime.start()
            await asyncio.sleep(1.0)
        finally:
            await runtime.stop()

        assert slack_gateway.messages == [{"channel": "C123", "text": "spoken outward reply", "thread_ts": None}]

    asyncio.run(scenario())


def test_scheduler_runtime_stays_silent_without_public_response(tmp_path) -> None:
    async def scenario() -> None:
        schedule_file = tmp_path / "workspace" / "schedule_data" / "schedules.json"
        write_schedules(
            schedule_file,
            [
                {
                    "id": "sched-1",
                    "name": "Silent shot",
                    "schedule_type": "date",
                    "schedule_value": (datetime.now(timezone.utc) + timedelta(milliseconds=300)).isoformat(),
                    "user": "U123",
                    "text": "Check quietly",
                    "channel_target": "C123",
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

        class SilentSessionManager(FakeSessionManager):
            async def run(
                self,
                session_id: str,
                prompt: str,
                metadata: dict | None = None,
                provider=None,
                model=None,
                context_prefix: str | None = None,
            ):
                self.calls.append(
                    {
                        "session_id": session_id,
                        "prompt": prompt,
                        "metadata": metadata or {},
                        "context_prefix": context_prefix,
                    }
                )
                return SimpleNamespace(
                    state="completed",
                    error=None,
                    result=SimpleNamespace(
                        final_response="internal only",
                        public_response_text="",
                    ),
                )

        session_manager = SilentSessionManager()
        slack_gateway = FakeSlackGateway()
        telegram_gateway = FakeTelegramGateway()
        runtime = SchedulerRuntime(
            settings,
            session_manager,
            ChannelDelivery(slack_gateway=slack_gateway, telegram_gateway=telegram_gateway),
        )

        try:
            await runtime.start()
            await asyncio.sleep(1.0)
        finally:
            await runtime.stop()

        assert session_manager.calls
        assert slack_gateway.messages == []
        assert telegram_gateway.messages == []

    asyncio.run(scenario())


def test_scheduler_runtime_reloads_new_schedules_on_explicit_request(tmp_path) -> None:
    async def scenario() -> None:
        schedule_file = tmp_path / "workspace" / "schedule_data" / "schedules.json"
        write_schedules(schedule_file, [])

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
        telegram_gateway = FakeTelegramGateway()
        runtime = SchedulerRuntime(
            settings,
            session_manager,
            ChannelDelivery(slack_gateway=slack_gateway, telegram_gateway=telegram_gateway),
        )

        try:
            await runtime.start()
            assert runtime.job_count == 0

            write_schedules(
                schedule_file,
                [
                    {
                        "id": "sched-1",
                        "name": "Reloaded shot",
                        "schedule_type": "date",
                        "schedule_value": (datetime.now(timezone.utc) + timedelta(milliseconds=300)).isoformat(),
                        "user": "U123",
                        "text": "Run after reload",
                        "channel_target": "C123",
                        "is_enabled": True,
                    }
                ],
            )

            await runtime.reload_from_file(force=True)
            assert runtime.job_count == 1
            await asyncio.sleep(1.0)
        finally:
            await runtime.stop()

        assert session_manager.calls
        assert session_manager.calls[0]["prompt"] == "Run after reload"
        assert slack_gateway.messages == [{"channel": "C123", "text": "scheduled response", "thread_ts": None}]

    asyncio.run(scenario())
