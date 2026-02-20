"""
Scheduler Tools for Claude Code SDK
Tools that allow Claude to directly manage schedules
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict

from claude_agent_sdk import create_sdk_mcp_server, tool

from app import scheduler

# Lock to prevent concurrent access to schedule file
_schedule_file_lock = asyncio.Lock()


@tool(
    "add_schedule",
    "Adds a new schedule. Supports cron or date type.",
    {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Unique name representing the schedule's purpose (e.g., 'Daily morning reminder', 'Weekly report')"
            },
            "schedule_type": {
                "type": "string",
                "enum": ["cron", "date"],
                "description": "Schedule type - 'cron' (recurring) or 'date' (one-time)"
            },
            "schedule_value": {
                "type": "string",
                "description": "cron type: cron expression (e.g., '0 9 * * *' = daily at 9am), date type: 'YYYY-MM-DD HH:MM:SS' format"
            },
            "user_id": {
                "type": "string",
                "description": "User ID to receive message when schedule executes"
            },
            "text": {
                "type": "string",
                "description": "Complete command that the AI employee will receive when schedule executes (must include full command starting with bot name. e.g., 'KIRA, say 1')"
            },
            "channel_id": {
                "type": "string",
                "description": "Channel ID where schedule will execute"
            },
            "is_enabled": {
                "type": "boolean",
                "description": "Whether schedule is enabled (default: true)"
            }
        },
        "required": ["name", "schedule_type", "schedule_value", "user_id", "text", "channel_id"]
    }
)
async def scheduler_add_schedule(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new schedule"""
    name = args["name"]
    schedule_type = args["schedule_type"]
    schedule_value = args["schedule_value"]
    user_id = args["user_id"]
    text = args["text"]
    channel_id = args["channel_id"]
    is_enabled = args.get("is_enabled", True)

    try:
        if schedule_type not in ["cron", "date"]:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Invalid schedule_type. Only 'cron' or 'date' can be used."
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

        # Validate date/cron format
        if schedule_type == "date":
            from datetime import datetime
            try:
                datetime.fromisoformat(schedule_value.replace('Z', '+00:00'))
            except (ValueError, AttributeError) as e:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": True,
                            "message": f"Invalid date format: {schedule_value}. Please use 'YYYY-MM-DD HH:MM:SS' format."
                        }, ensure_ascii=False, indent=2)
                    }],
                    "error": True
                }
        elif schedule_type == "cron":
            from apscheduler.triggers.cron import CronTrigger
            try:
                CronTrigger.from_crontab(schedule_value)
            except (ValueError, KeyError) as e:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": True,
                            "message": f"Invalid cron expression: {schedule_value}. Example: '0 9 * * *' (daily at 9am)"
                        }, ensure_ascii=False, indent=2)
                    }],
                    "error": True
                }

        # Use Lock to prevent concurrent access
        async with _schedule_file_lock:
            schedules = scheduler.read_schedules_from_file()

            # Check for duplicate names (warning only, not blocked)
            duplicate_names = [s.get("name") for s in schedules if s.get("name") == name and s.get("is_enabled")]
            if duplicate_names:
                logging.warning(f"[SCHEDULER_TOOLS] Duplicate schedule name detected: {name}")
            new_schedule = {
                "id": str(uuid.uuid4()),
                "name": name,
                "schedule_type": schedule_type,
                "schedule_value": schedule_value,
                "user": user_id,
                "text": text,
                "channel": channel_id,
                "is_enabled": is_enabled,
            }
            schedules.append(new_schedule)
            scheduler.write_schedules_to_file(schedules)
            await scheduler.reload_schedules_from_file()

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "message": f"Successfully added schedule: {name}",
                    "schedule_id": new_schedule["id"]
                }, ensure_ascii=False, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Failed to add schedule: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "remove_schedule",
    "Deletes a schedule using its ID.",
    {
        "type": "object",
        "properties": {
            "schedule_id": {
                "type": "string",
                "description": "ID of the schedule to delete"
            }
        },
        "required": ["schedule_id"]
    }
)
async def scheduler_remove_schedule(args: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a schedule"""
    schedule_id = args["schedule_id"]

    try:
        # Use Lock to prevent concurrent access
        async with _schedule_file_lock:
            schedules = scheduler.read_schedules_from_file()
            original_count = len(schedules)
            schedules = [s for s in schedules if s.get("id") != schedule_id]

            if len(schedules) == original_count:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": True,
                            "message": f"Cannot find schedule with ID {schedule_id}."
                        }, ensure_ascii=False, indent=2)
                    }],
                    "error": True
                }

            scheduler.write_schedules_to_file(schedules)
            await scheduler.reload_schedules_from_file()

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "message": f"Deleted schedule with ID {schedule_id}."
                }, ensure_ascii=False, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Failed to delete schedule: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "list_schedules",
    "Returns a list of saved active schedules. Past date-type schedules are automatically excluded. You can filter by channel_id to view only schedules for a specific channel.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Specify channel ID to view only schedules for that channel. If omitted, returns schedules for all channels."
            }
        }
    }
)
async def scheduler_list_schedules(args: Dict[str, Any]) -> Dict[str, Any]:
    """List schedules (excluding past schedules, with optional channel filtering)"""
    try:
        from datetime import datetime

        channel_id_filter = args.get("channel_id")
        schedules = scheduler.read_schedules_from_file()

        if not schedules:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "message": "No registered schedules.",
                        "schedules": []
                    }, ensure_ascii=False, indent=2)
                }]
            }

        schedule_list = []

        for s in schedules:
            # Filter by channel_id
            if channel_id_filter and s.get("channel") != channel_id_filter:
                continue

            # Exclude date-type schedules that have already passed
            if s.get("schedule_type") == "date":
                try:
                    run_date = datetime.fromisoformat(
                        s.get("schedule_value").replace('Z', '+00:00')
                    )
                    if run_date <= datetime.now(run_date.tzinfo):
                        continue  # Skip past schedules
                except (ValueError, AttributeError) as e:
                    logging.warning(f"Schedule ID {s.get('id')} - Invalid date format: {s.get('schedule_value')}, error: {e}")
                    continue  # Exclude on parse failure

            schedule_list.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "schedule_type": s.get("schedule_type"),
                "schedule_value": s.get("schedule_value"),
                "user": s.get("user"),
                "channel": s.get("channel"),
                "text": s.get("text"),
                "is_enabled": s.get("is_enabled")
            })

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "message": f"Registered schedules: {len(schedule_list)}",
                    "schedules": schedule_list
                }, ensure_ascii=False, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Failed to list schedules: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "update_schedule",
    "Updates an existing schedule.",
    {
        "type": "object",
        "properties": {
            "schedule_id": {
                "type": "string",
                "description": "ID of the schedule to update"
            },
            "name": {
                "type": "string",
                "description": "New name for the schedule (optional)"
            },
            "schedule_value": {
                "type": "string",
                "description": "New schedule value (optional)"
            },
            "text": {
                "type": "string",
                "description": "New message content (optional)"
            },
            "is_enabled": {
                "type": "boolean",
                "description": "Whether schedule is enabled (optional)"
            }
        },
        "required": ["schedule_id"]
    }
)
async def scheduler_update_schedule(args: Dict[str, Any]) -> Dict[str, Any]:
    """Update a schedule"""
    schedule_id = args["schedule_id"]

    try:
        schedules = scheduler.read_schedules_from_file()
        schedule_found = False

        for s in schedules:
            if s.get("id") == schedule_id:
                schedule_found = True
                # Only change fields being updated
                if "name" in args:
                    s["name"] = args["name"]
                if "schedule_value" in args:
                    s["schedule_value"] = args["schedule_value"]
                if "text" in args:
                    s["text"] = args["text"]
                if "is_enabled" in args:
                    s["is_enabled"] = args["is_enabled"]
                break

        if not schedule_found:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": f"Cannot find schedule with ID {schedule_id}."
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

        scheduler.write_schedules_to_file(schedules)
        await scheduler.reload_schedules_from_file()

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "message": f"Updated schedule with ID {schedule_id}."
                }, ensure_ascii=False, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Failed to update schedule: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


# Create MCP Server
scheduler_tools = [
    scheduler_add_schedule,
    scheduler_remove_schedule,
    scheduler_list_schedules,
    scheduler_update_schedule,
]


def create_scheduler_mcp_server():
    """Scheduler MCP server for Claude Code SDK"""
    return create_sdk_mcp_server(
        name="scheduler",
        version="1.0.0",
        tools=scheduler_tools
    )
