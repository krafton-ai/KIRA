from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

from kiraclaw_agentd.scheduler_mcp_tools import add_schedule, list_schedules, remove_schedule, update_schedule


def _payload(result: dict) -> dict:
    return json.loads(result["content"][0]["text"])


def test_scheduler_tools_crud_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KIRACLAW_SCHEDULE_FILE", str(tmp_path / "schedules.json"))
    reload_calls: list[bool] = []

    async def fake_reload() -> tuple[bool, str | None]:
        reload_calls.append(True)
        return True, None

    monkeypatch.setattr("kiraclaw_agentd.scheduler_mcp_tools._notify_scheduler_reload", fake_reload)

    async def scenario() -> None:
        created = _payload(
            await add_schedule(
                {
                    "name": "Daily report",
                    "schedule_type": "date",
                    "schedule_value": (datetime.now(timezone.utc) + timedelta(minutes=5)).replace(microsecond=0).isoformat(),
                    "user_id": "U123",
                    "text": "KIRA, send the report",
                    "channel_id": "C123",
                }
            )
        )
        assert created["success"] is True
        assert created["reload_notified"] is True
        schedule_id = created["schedule_id"]

        listed = _payload(list_schedules({}))
        assert listed["success"] is True
        assert listed["schedules"][0]["id"] == schedule_id
        assert listed["schedules"][0]["channel_type"] == "slack"
        assert listed["schedules"][0]["channel_target"] == "C123"

        updated = _payload(await update_schedule({"schedule_id": schedule_id, "name": "Updated report"}))
        assert updated["success"] is True
        assert updated["reload_notified"] is True

        removed = _payload(await remove_schedule({"schedule_id": schedule_id}))
        assert removed["success"] is True
        assert removed["reload_notified"] is True

        after_remove = _payload(list_schedules({}))
        assert after_remove["schedules"] == []
        assert len(reload_calls) == 3

    asyncio.run(scenario())


def test_scheduler_tools_accept_telegram_channel_type(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KIRACLAW_SCHEDULE_FILE", str(tmp_path / "schedules.json"))
    monkeypatch.setattr("kiraclaw_agentd.scheduler_mcp_tools._notify_scheduler_reload", lambda: asyncio.sleep(0, result=(True, None)))

    async def scenario() -> None:
        created = _payload(
            await add_schedule(
                {
                    "name": "Telegram report",
                    "schedule_type": "date",
                    "schedule_value": (datetime.now(timezone.utc) + timedelta(minutes=5)).replace(microsecond=0).isoformat(),
                    "user_id": "U123",
                    "text": "Send the Telegram report",
                    "channel_type": "telegram",
                    "channel_target": "123456",
                }
            )
        )
        assert created["success"] is True

        listed = _payload(list_schedules({"channel_target": "123456"}))
        assert listed["success"] is True
        assert listed["schedules"][0]["channel_type"] == "telegram"
        assert listed["schedules"][0]["channel_target"] == "123456"
        assert created["reload_notified"] is True

    asyncio.run(scenario())


def test_scheduler_tools_accept_discord_channel_type(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KIRACLAW_SCHEDULE_FILE", str(tmp_path / "schedules.json"))
    monkeypatch.setattr("kiraclaw_agentd.scheduler_mcp_tools._notify_scheduler_reload", lambda: asyncio.sleep(0, result=(True, None)))

    async def scenario() -> None:
        created = _payload(
            await add_schedule(
                {
                    "name": "Discord report",
                    "schedule_type": "date",
                    "schedule_value": (datetime.now(timezone.utc) + timedelta(minutes=5)).replace(microsecond=0).isoformat(),
                    "user_id": "U123",
                    "text": "Send the Discord report",
                    "channel_type": "discord",
                    "channel_target": "987654321",
                }
            )
        )
        assert created["success"] is True

        listed = _payload(list_schedules({"channel_target": "987654321"}))
        assert listed["success"] is True
        assert listed["schedules"][0]["channel_type"] == "discord"
        assert listed["schedules"][0]["channel_target"] == "987654321"
        assert created["reload_notified"] is True

    asyncio.run(scenario())


def test_scheduler_tools_accept_desktop_channel_type_with_default_target(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KIRACLAW_SCHEDULE_FILE", str(tmp_path / "schedules.json"))
    monkeypatch.setattr("kiraclaw_agentd.scheduler_mcp_tools._notify_scheduler_reload", lambda: asyncio.sleep(0, result=(True, None)))

    async def scenario() -> None:
        created = _payload(
            await add_schedule(
                {
                    "name": "Desktop report",
                    "schedule_type": "date",
                    "schedule_value": (datetime.now(timezone.utc) + timedelta(minutes=5)).replace(microsecond=0).isoformat(),
                    "user_id": "U123",
                    "text": "Send the desktop report",
                    "channel_type": "desktop",
                }
            )
        )
        assert created["success"] is True

        listed = _payload(list_schedules({"channel_target": "desktop:local"}))
        assert listed["success"] is True
        assert listed["schedules"][0]["channel_type"] == "desktop"
        assert listed["schedules"][0]["channel_target"] == "desktop:local"
        assert created["reload_notified"] is True

    asyncio.run(scenario())


def test_scheduler_tools_return_warning_when_reload_notification_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KIRACLAW_SCHEDULE_FILE", str(tmp_path / "schedules.json"))

    async def fake_reload() -> tuple[bool, str | None]:
        return False, "connection refused"

    monkeypatch.setattr("kiraclaw_agentd.scheduler_mcp_tools._notify_scheduler_reload", fake_reload)

    async def scenario() -> None:
        created = _payload(
            await add_schedule(
                {
                    "name": "Delayed report",
                    "schedule_type": "date",
                    "schedule_value": (datetime.now(timezone.utc) + timedelta(minutes=5)).replace(microsecond=0).isoformat(),
                    "user_id": "U123",
                    "text": "Send later",
                    "channel_id": "C123",
                }
            )
        )
        assert created["success"] is True
        assert created["reload_notified"] is False
        assert "reload pending" in created["message"]

    asyncio.run(scenario())
