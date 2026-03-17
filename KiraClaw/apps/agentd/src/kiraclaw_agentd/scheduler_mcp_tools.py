from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from apscheduler.triggers.cron import CronTrigger

from kiraclaw_agentd.mcp_stdio import McpToolSpec, mcp_text_result
from kiraclaw_agentd.schedule_store import read_schedules, write_schedules

_schedule_file_lock = asyncio.Lock()


def _schedule_file() -> Path:
    value = os.environ.get("KIRACLAW_SCHEDULE_FILE", "")
    if value:
        return Path(value).expanduser()
    return Path.cwd() / "schedule_data" / "schedules.json"


def _validate_schedule_value(schedule_type: str, schedule_value: str) -> str | None:
    if schedule_type == "date":
        try:
            datetime.fromisoformat(schedule_value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return (
                f"Invalid date format: {schedule_value}. "
                "Please use 'YYYY-MM-DD HH:MM:SS' or ISO format."
            )
        return None

    if schedule_type == "cron":
        try:
            CronTrigger.from_crontab(schedule_value)
        except (ValueError, KeyError):
            return (
                f"Invalid cron expression: {schedule_value}. "
                "Example: '0 9 * * *' (daily at 9am)"
            )
        return None

    return "Invalid schedule_type. Only 'cron' or 'date' can be used."


async def add_schedule(args: dict[str, Any]) -> dict[str, Any]:
    error = _validate_schedule_value(args["schedule_type"], args["schedule_value"])
    if error:
        return mcp_text_result({"success": False, "error": True, "message": error}, is_error=True)

    async with _schedule_file_lock:
        schedule_file = _schedule_file()
        schedules = read_schedules(schedule_file)
        new_schedule = {
            "id": str(uuid.uuid4()),
            "name": args["name"],
            "schedule_type": args["schedule_type"],
            "schedule_value": args["schedule_value"],
            "user": args["user_id"],
            "text": args["text"],
            "channel": args["channel_id"],
            "is_enabled": args.get("is_enabled", True),
        }
        schedules.append(new_schedule)
        write_schedules(schedule_file, schedules)

    return mcp_text_result(
        {
            "success": True,
            "message": f"Successfully added schedule: {new_schedule['name']}",
            "schedule_id": new_schedule["id"],
        }
    )


async def remove_schedule(args: dict[str, Any]) -> dict[str, Any]:
    async with _schedule_file_lock:
        schedule_file = _schedule_file()
        schedules = read_schedules(schedule_file)
        updated = [schedule for schedule in schedules if schedule.get("id") != args["schedule_id"]]
        if len(updated) == len(schedules):
            return mcp_text_result(
                {
                    "success": False,
                    "error": True,
                    "message": f"Cannot find schedule with ID {args['schedule_id']}.",
                },
                is_error=True,
            )

        write_schedules(schedule_file, updated)

    return mcp_text_result(
        {
            "success": True,
            "message": f"Deleted schedule with ID {args['schedule_id']}.",
        }
    )


def list_schedules(args: dict[str, Any]) -> dict[str, Any]:
    channel_id_filter = args.get("channel_id")
    schedules = read_schedules(_schedule_file())
    if not schedules:
        return mcp_text_result({"success": True, "message": "No registered schedules.", "schedules": []})

    visible: list[dict[str, Any]] = []
    for schedule in schedules:
        if channel_id_filter and schedule.get("channel") != channel_id_filter:
            continue

        if schedule.get("schedule_type") == "date":
            try:
                run_date = datetime.fromisoformat(schedule.get("schedule_value", "").replace("Z", "+00:00"))
                if run_date <= datetime.now(run_date.tzinfo):
                    continue
            except (ValueError, AttributeError):
                continue

        visible.append(
            {
                "id": schedule.get("id"),
                "name": schedule.get("name"),
                "schedule_type": schedule.get("schedule_type"),
                "schedule_value": schedule.get("schedule_value"),
                "user": schedule.get("user"),
                "channel": schedule.get("channel"),
                "text": schedule.get("text"),
                "is_enabled": schedule.get("is_enabled"),
            }
        )

    return mcp_text_result(
        {
            "success": True,
            "message": f"Registered schedules: {len(visible)}",
            "schedules": visible,
        }
    )


async def update_schedule(args: dict[str, Any]) -> dict[str, Any]:
    async with _schedule_file_lock:
        schedule_file = _schedule_file()
        schedules = read_schedules(schedule_file)
        schedule = next((row for row in schedules if row.get("id") == args["schedule_id"]), None)
        if schedule is None:
            return mcp_text_result(
                {
                    "success": False,
                    "error": True,
                    "message": f"Cannot find schedule with ID {args['schedule_id']}.",
                },
                is_error=True,
            )

        if "schedule_value" in args:
            error = _validate_schedule_value(schedule.get("schedule_type", "cron"), args["schedule_value"])
            if error:
                return mcp_text_result({"success": False, "error": True, "message": error}, is_error=True)

        for key, target in (
            ("name", "name"),
            ("schedule_value", "schedule_value"),
            ("text", "text"),
            ("is_enabled", "is_enabled"),
        ):
            if key in args:
                schedule[target] = args[key]

        write_schedules(schedule_file, schedules)

    return mcp_text_result(
        {
            "success": True,
            "message": f"Updated schedule with ID {args['schedule_id']}.",
        }
    )


def build_scheduler_tool_specs() -> list[McpToolSpec]:
    return [
        McpToolSpec(
            name="add_schedule",
            description="Adds a new schedule. Supports cron or date type.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unique name representing the schedule's purpose"},
                    "schedule_type": {
                        "type": "string",
                        "enum": ["cron", "date"],
                        "description": "Schedule type - 'cron' (recurring) or 'date' (one-time)",
                    },
                    "schedule_value": {
                        "type": "string",
                        "description": "cron type: cron expression, date type: 'YYYY-MM-DD HH:MM:SS' or ISO format",
                    },
                    "user_id": {"type": "string", "description": "User ID to receive message when schedule executes"},
                    "text": {
                        "type": "string",
                        "description": "Complete command that the AI employee will receive when schedule executes",
                    },
                    "channel_id": {"type": "string", "description": "Channel ID where schedule will execute"},
                    "is_enabled": {"type": "boolean", "description": "Whether schedule is enabled (default: true)"},
                },
                "required": ["name", "schedule_type", "schedule_value", "user_id", "text", "channel_id"],
            },
            handler=add_schedule,
        ),
        McpToolSpec(
            name="remove_schedule",
            description="Deletes a schedule using its ID.",
            input_schema={
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string", "description": "ID of the schedule to delete"},
                },
                "required": ["schedule_id"],
            },
            handler=remove_schedule,
        ),
        McpToolSpec(
            name="list_schedules",
            description="Returns a list of saved active schedules. Past date-type schedules are automatically excluded.",
            input_schema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Specify channel ID to view only schedules for that channel.",
                    }
                },
            },
            handler=list_schedules,
        ),
        McpToolSpec(
            name="update_schedule",
            description="Updates an existing schedule.",
            input_schema={
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string", "description": "ID of the schedule to update"},
                    "name": {"type": "string", "description": "New name for the schedule (optional)"},
                    "schedule_value": {"type": "string", "description": "New schedule value (optional)"},
                    "text": {"type": "string", "description": "New message content (optional)"},
                    "is_enabled": {"type": "boolean", "description": "Whether schedule is enabled (optional)"},
                },
                "required": ["schedule_id"],
            },
            handler=update_schedule,
        ),
    ]
