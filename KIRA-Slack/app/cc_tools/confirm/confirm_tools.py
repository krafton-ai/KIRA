"""
Confirm Tools for Claude Code SDK
Tools for handling user confirmation requests
"""

import json
import uuid
from typing import Any, Dict

from claude_agent_sdk import create_sdk_mcp_server, tool
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from app.config.settings import get_settings
from app.cc_utils.confirm_db import add_confirm_request


def get_slack_client() -> AsyncWebClient:
    """Return Slack AsyncWebClient instance"""
    settings = get_settings()
    token = settings.SLACK_BOT_TOKEN
    if not token:
        raise ValueError("SLACK_BOT_TOKEN is not set in settings")
    return AsyncWebClient(token=token)


@tool(
    "request_confirmation",
    "Sends a confirmation message to the user and waits for response. Used when the bot was not explicitly called but there is relevant memory.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Slack channel ID to send message to"
            },
            "user_id": {
                "type": "string",
                "description": "User ID to receive confirmation"
            },
            "user_name": {
                "type": "string",
                "description": "User name to receive confirmation"
            },
            "confirm_message": {
                "type": "string",
                "description": "Confirmation message (must start with user name. e.g., 'John, I helped you before, would you like my help?')"
            },
            "original_request_text": {
                "type": "string",
                "description": "Complete command to execute on approval (must include full command starting with bot name. e.g., 'KIRA, summarize project status')"
            },
            "message_ts": {
                "type": "string",
                "description": "Original message timestamp (for thread creation, optional). Use state_data.current_message.message_ts"
            },
            "thread_ts": {
                "type": "string",
                "description": "Thread timestamp (optional). Use state_data.current_message.thread_ts"
            }
        },
        "required": ["channel_id", "user_id", "user_name", "confirm_message", "original_request_text"]
    }
)
async def confirm_request_confirmation(args: Dict[str, Any]) -> Dict[str, Any]:
    """Send confirm message to user and save to DB"""
    channel_id = args["channel_id"]
    user_id = args["user_id"]
    user_name = args["user_name"]
    confirm_message = args["confirm_message"]
    original_request_text = args["original_request_text"]

    # message_ts and thread_ts are optional parameters
    message_ts = args.get("message_ts")
    thread_ts = args.get("thread_ts")

    # Verify authorized user
    from app.cc_slack_handlers import is_authorized_user

    if not is_authorized_user(user_name):
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"User '{user_name}' is not an authorized user. Cannot send confirmation message."
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }

    try:
        # Generate unique confirm_id
        confirm_id = str(uuid.uuid4())

        # Determine thread_ts: thread_ts > message_ts > None (new message)
        final_thread_ts = thread_ts or message_ts

        # Save to DB (including thread_ts)
        success = add_confirm_request(
            confirm_id=confirm_id,
            channel_id=channel_id,
            user_id=user_id,
            user_name=user_name,
            confirm_message=confirm_message,
            original_request_text=original_request_text,
            thread_ts=final_thread_ts
        )

        if not success:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to save confirm request (duplicate confirm_id)"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

        # Send Slack message
        client = get_slack_client()
        message_params = {
            "channel": channel_id,
            "text": confirm_message
        }

        # Only add thread_ts if present (otherwise send as new message)
        if final_thread_ts:
            message_params["thread_ts"] = final_thread_ts

        response = await client.chat_postMessage(**message_params)

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "confirm_id": confirm_id,
                    "message": "Confirmation message has been sent.",
                    "slack_ts": response.data.get("ts"),
                    "thread_ts": final_thread_ts
                }, ensure_ascii=False, indent=2)
            }]
        }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Failed to send Slack message: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Confirm request failed: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


# Create MCP Server
confirm_tools = [
    confirm_request_confirmation,
]


def create_confirm_mcp_server():
    """Confirm MCP server for Claude Code SDK"""
    return create_sdk_mcp_server(
        name="confirm",
        version="1.0.0",
        tools=confirm_tools
    )
