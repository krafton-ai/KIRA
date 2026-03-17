from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

from kiraclaw_agentd.scheduler_mcp_tools import add_schedule, list_schedules, remove_schedule, update_schedule


def _payload(result: dict) -> dict:
    return json.loads(result["content"][0]["text"])


def test_scheduler_tools_crud_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KIRACLAW_SCHEDULE_FILE", str(tmp_path / "schedules.json"))

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
        schedule_id = created["schedule_id"]

        listed = _payload(list_schedules({}))
        assert listed["success"] is True
        assert listed["schedules"][0]["id"] == schedule_id

        updated = _payload(await update_schedule({"schedule_id": schedule_id, "name": "Updated report"}))
        assert updated["success"] is True

        removed = _payload(await remove_schedule({"schedule_id": schedule_id}))
        assert removed["success"] is True

        after_remove = _payload(list_schedules({}))
        assert after_remove["schedules"] == []

    asyncio.run(scenario())
