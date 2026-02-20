"""
Email Tasks Tools for Claude Code SDK
MCP tools for managing tasks extracted from emails
"""

import json
from typing import Any, Dict

from claude_agent_sdk import create_sdk_mcp_server, tool

from app.cc_utils.email_tasks_db import add_task


@tool(
    "add_email_task",
    "Adds a task extracted from an email. Use this tool when there are tasks to be done after analyzing an email.",
    {
        "type": "object",
        "properties": {
            "email_id": {
                "type": "string",
                "description": "Email ID"
            },
            "sender": {
                "type": "string",
                "description": "Sender (Name <email> format)"
            },
            "subject": {
                "type": "string",
                "description": "Email subject"
            },
            "task_description": {
                "type": "string",
                "description": "Task description (be specific)"
            },
            "priority": {
                "type": "string",
                "description": "Priority (low/medium/high)",
                "enum": ["low", "medium", "high"]
            },
            "user_id": {
                "type": "string",
                "description": "User ID to receive notification"
            },
            "user_name": {
                "type": "string",
                "description": "User name to receive notification (for authorization check)"
            },
            "text": {
                "type": "string",
                "description": "Notification message content"
            },
            "channel_id": {
                "type": "string",
                "description": "Channel ID to send notification to"
            }
        },
        "required": ["email_id", "sender", "subject", "task_description", "user_id", "user_name", "text", "channel_id"]
    }
)
async def email_tasks_add_task(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add task extracted from email"""
    email_id = args["email_id"]
    sender = args["sender"]
    subject = args["subject"]
    task_description = args["task_description"]
    priority = args.get("priority", "medium")
    user_id = args["user_id"]
    user_name = args["user_name"]
    text = args["text"]
    channel_id = args["channel_id"]

    # Verify authorized user
    from app.cc_slack_handlers import is_authorized_user

    if not is_authorized_user(user_name):
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"User '{user_name}' is not an authorized user. Cannot add task."
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }

    try:
        task_id = add_task(
            email_id=email_id,
            sender=sender,
            subject=subject,
            task_description=task_description,
            priority=priority,
            user_id=user_id,
            text=text,
            channel_id=channel_id
        )

        result = {
            "success": True,
            "task_id": task_id,
            "message": f"Task has been added (ID: {task_id})"
        }

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, indent=2)
            }]
        }
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(error_result, ensure_ascii=False, indent=2)
            }]
        }


# Create MCP server
tools_list = [
    email_tasks_add_task,
]


def create_email_tasks_mcp_server():
    """Create Email Tasks MCP server"""
    return create_sdk_mcp_server(
        name="email_tasks",
        version="1.0.0",
        tools=tools_list
    )
