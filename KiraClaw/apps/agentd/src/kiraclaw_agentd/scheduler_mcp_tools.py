from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp
from apscheduler.triggers.cron import CronTrigger

from kiraclaw_agentd.delivery_targets import (
    SUPPORTED_DELIVERY_CHANNEL_TYPES,
    SUPPORTED_DELIVERY_CHANNEL_TYPE_SET,
    normalize_delivery_channel,
)
from kiraclaw_agentd.mcp_stdio import McpToolSpec, mcp_text_result
from kiraclaw_agentd.schedule_store import read_schedules, write_schedules

_schedule_file_lock = asyncio.Lock()
_scheduler_reload_timeout = aiohttp.ClientTimeout(total=2.0)


def _local_timezone():
    return datetime.now().astimezone().tzinfo


def _local_timezone_label() -> str:
    tzinfo = _local_timezone()
    return str(tzinfo) if tzinfo is not None else "local time"


def _format_schedule_confirmation(schedule_type: str, schedule_value: str) -> str | None:
    local_tz = _local_timezone()
    if local_tz is None:
        return None

    if schedule_type == "date":
        run_date = datetime.fromisoformat(schedule_value.replace("Z", "+00:00"))
        if run_date.tzinfo is None:
            run_date = run_date.replace(tzinfo=local_tz)
        local_run_date = run_date.astimezone(local_tz)
        return f"Runs at {local_run_date.strftime('%Y-%m-%d %H:%M:%S %Z')}."

    if schedule_type == "cron":
        trigger = CronTrigger.from_crontab(schedule_value, timezone=local_tz)
        next_run = trigger.get_next_fire_time(None, datetime.now(local_tz))
        if next_run is None:
            return f"Cron runs in {_local_timezone_label()}: {schedule_value}."
        return (
            f"Cron runs in {_local_timezone_label()}: {schedule_value} "
            f"(next: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')})."
        )

    return None


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


def _scheduler_reload_url() -> str:
    host = os.environ.get("KIRACLAW_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = os.environ.get("KIRACLAW_PORT", "8787").strip() or "8787"
    return f"http://{host}:{port}/v1/admin/reload-schedules"


async def _notify_scheduler_reload() -> tuple[bool, str | None]:
    try:
        async with aiohttp.ClientSession(timeout=_scheduler_reload_timeout) as session:
            async with session.post(_scheduler_reload_url()) as response:
                if response.status >= 400:
                    body = await response.text()
                    return False, f"Scheduler reload failed with HTTP {response.status}: {body.strip()}"
                return True, None
    except Exception as exc:
        return False, str(exc)


async def add_schedule(args: dict[str, Any]) -> dict[str, Any]:
    error = _validate_schedule_value(args["schedule_type"], args["schedule_value"])
    if error:
        return mcp_text_result({"success": False, "error": True, "message": error}, is_error=True)

    channel_type, channel_target = normalize_delivery_channel(
        args.get("channel_type"),
        args.get("channel_target") or args.get("channel_id"),
    )
    if not channel_target:
        return mcp_text_result(
            {"success": False, "error": True, "message": "channel_target is required."},
            is_error=True,
        )
    if channel_type not in {"", *SUPPORTED_DELIVERY_CHANNEL_TYPE_SET}:
        return mcp_text_result(
            {
                "success": False,
                "error": True,
                "message": "channel_type must be 'slack', 'telegram', 'discord', or 'desktop'.",
            },
            is_error=True,
        )

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
            "channel_type": channel_type or "slack",
            "channel_target": channel_target,
            "is_enabled": args.get("is_enabled", True),
        }
        schedules.append(new_schedule)
        write_schedules(schedule_file, schedules)

    reload_notified, reload_error = await _notify_scheduler_reload()
    message = f"Successfully added schedule: {new_schedule['name']}"
    if not reload_notified and reload_error:
        message = f"{message} (reload pending: {reload_error})"
    confirmation = _format_schedule_confirmation(new_schedule["schedule_type"], new_schedule["schedule_value"])
    if confirmation:
        message = f"{message} {confirmation}"

    return mcp_text_result(
        {
            "success": True,
            "message": message,
            "schedule_id": new_schedule["id"],
            "reload_notified": reload_notified,
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

    reload_notified, reload_error = await _notify_scheduler_reload()
    message = f"Deleted schedule with ID {args['schedule_id']}."
    if not reload_notified and reload_error:
        message = f"{message} (reload pending: {reload_error})"

    return mcp_text_result(
        {
            "success": True,
            "message": message,
            "reload_notified": reload_notified,
        }
    )


def list_schedules(args: dict[str, Any]) -> dict[str, Any]:
    channel_target_filter = args.get("channel_target") or args.get("channel_id")
    schedules = read_schedules(_schedule_file())
    if not schedules:
        return mcp_text_result({"success": True, "message": "No registered schedules.", "schedules": []})

    visible: list[dict[str, Any]] = []
    for schedule in schedules:
        if channel_target_filter and schedule.get("channel_target") != channel_target_filter:
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
                "channel_type": schedule.get("channel_type"),
                "channel_target": schedule.get("channel_target"),
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

    reload_notified, reload_error = await _notify_scheduler_reload()
    message = f"Updated schedule with ID {args['schedule_id']}."
    if not reload_notified and reload_error:
        message = f"{message} (reload pending: {reload_error})"
    confirmation = _format_schedule_confirmation(schedule.get("schedule_type", ""), schedule.get("schedule_value", ""))
    if confirmation:
        message = f"{message} {confirmation}"

    return mcp_text_result(
        {
            "success": True,
            "message": message,
            "reload_notified": reload_notified,
        }
    )


def build_scheduler_tool_specs() -> list[McpToolSpec]:
    timezone_label = _local_timezone_label()
    return [
        McpToolSpec(
            name="add_schedule",
            description=(
                "Adds a new schedule. Supports cron or date type. "
                f"Interpret requested times in {timezone_label}, not UTC. "
                "For cron, store local wall-clock hours. For one-time dates, prefer timezone-aware ISO with the local offset."
            ),
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
                        "description": (
                            "cron type: cron expression in local daemon time. "
                            "date type: 'YYYY-MM-DD HH:MM:SS' or ISO format, preferably timezone-aware with the local offset."
                        ),
                    },
                    "user_id": {"type": "string", "description": "User ID to receive message when schedule executes"},
                    "text": {
                        "type": "string",
                        "description": "Complete command that the AI employee will receive when schedule executes",
                    },
                    "channel_type": {
                        "type": "string",
                        "enum": list(SUPPORTED_DELIVERY_CHANNEL_TYPES),
                        "description": "Delivery channel type. Use 'desktop' to send the result back into Talk. Defaults to 'slack' if omitted.",
                    },
                    "channel_target": {
                        "type": "string",
                        "description": "Delivery target ID. Slack uses channel ID, Telegram uses chat ID. Leave it empty for desktop to use the default Talk session.",
                    },
                    "channel_id": {
                        "type": "string",
                        "description": "Legacy Slack channel ID alias for channel_target.",
                    },
                    "is_enabled": {"type": "boolean", "description": "Whether schedule is enabled (default: true)"},
                },
                "required": ["name", "schedule_type", "schedule_value", "user_id", "text"],
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
                    "channel_target": {
                        "type": "string",
                        "description": "Specify delivery target to view only schedules for that target.",
                    },
                    "channel_id": {
                        "type": "string",
                        "description": "Legacy Slack channel ID alias for channel_target.",
                    }
                },
            },
            handler=list_schedules,
        ),
        McpToolSpec(
            name="update_schedule",
            description=(
                "Updates an existing schedule. Keep schedule times in local daemon time unless the user explicitly asked for another timezone."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string", "description": "ID of the schedule to update"},
                    "name": {"type": "string", "description": "New name for the schedule (optional)"},
                    "schedule_value": {
                        "type": "string",
                        "description": (
                            "New schedule value in local daemon time. "
                            "Do not silently convert local intended hours into UTC."
                        ),
                    },
                    "text": {"type": "string", "description": "New message content (optional)"},
                    "is_enabled": {"type": "boolean", "description": "Whether schedule is enabled (optional)"},
                },
                "required": ["schedule_id"],
            },
            handler=update_schedule,
        ),
    ]
