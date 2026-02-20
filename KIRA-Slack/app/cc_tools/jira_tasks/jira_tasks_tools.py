"""
Jira Tasks Tools for Claude Code SDK
MCP tools for managing tasks extracted from Jira
"""

import json
from typing import Any, Dict

from claude_agent_sdk import create_sdk_mcp_server, tool

from app.cc_utils.jira_tasks_db import add_task


@tool(
    "add_jira_task",
    "Adds a task extracted from a Jira ticket. Use this tool when there are important tickets or tickets that need attention.",
    {
        "type": "object",
        "properties": {
            "issue_key": {
                "type": "string",
                "description": "Jira issue key (e.g., PROJ-123)",
            },
            "issue_url": {"type": "string", "description": "Jira issue URL"},
            "summary": {"type": "string", "description": "Issue title"},
            "status": {
                "type": "string",
                "description": "Issue status (e.g., In Progress, Blocked, To Do)",
            },
            "priority": {
                "type": "string",
                "description": "Priority (low/medium/high)",
                "enum": ["low", "medium", "high"],
            },
            "task_description": {
                "type": "string",
                "description": "Task description (be specific)",
            },
            "user_id": {"type": "string", "description": "User ID to receive notification"},
            "user_name": {
                "type": "string",
                "description": "User name to receive notification (for authorization check)",
            },
            "text": {"type": "string", "description": "Notification message content"},
            "channel_id": {"type": "string", "description": "Channel ID to send notification to"},
        },
        "required": [
            "issue_key",
            "issue_url",
            "summary",
            "status",
            "priority",
            "task_description",
            "user_id",
            "user_name",
            "text",
            "channel_id",
        ],
    },
)
async def jira_tasks_add_task(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add task extracted from Jira"""
    issue_key = args["issue_key"]
    issue_url = args["issue_url"]
    summary = args["summary"]
    status = args["status"]
    priority = args["priority"]
    task_description = args["task_description"]
    user_id = args["user_id"]
    user_name = args["user_name"]
    text = args["text"]
    channel_id = args["channel_id"]

    # Verify authorized user
    from app.cc_slack_handlers import is_authorized_user

    if not is_authorized_user(user_name):
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"User '{user_name}' is not an authorized user. Cannot add task.",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }

    try:
        task_id = add_task(
            issue_key=issue_key,
            issue_url=issue_url,
            summary=summary,
            status=status,
            priority=priority,
            task_description=task_description,
            user_id=user_id,
            text=text,
            channel_id=channel_id,
        )

        result = {
            "success": True,
            "task_id": task_id,
            "issue_key": issue_key,
            "message": f"Task has been added (ID: {task_id}, Issue: {issue_key})",
        }

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2),
                }
            ]
        }
    except Exception as e:
        error_result = {"success": False, "error": str(e)}
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(error_result, ensure_ascii=False, indent=2),
                }
            ]
        }


# Create MCP server
tools_list = [
    jira_tasks_add_task,
]


def create_jira_tasks_mcp_server():
    """Create Jira Tasks MCP server"""
    return create_sdk_mcp_server(name="jira_tasks", version="1.0.0", tools=tools_list)
