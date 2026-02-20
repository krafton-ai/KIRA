"""
Waiting Answer Tools for Claude Code SDK
Tools for updating and aggregating responses
Manages all queries via SQLite
"""

import json
from typing import Any, Dict

from claude_agent_sdk import create_sdk_mcp_server, tool

from app.cc_utils.waiting_answer_db import (
    update_response,
    get_request_by_id,
    get_all_responses_for_request,
    get_request_progress,
)


@tool(
    "update_request",
    "Updates response for a specific query. Called when a respondent answers. Returns progress info with response, so send notification to original requester when all_completed is true.",
    {
        "type": "object",
        "properties": {
            "request_id": {
                "type": "string",
                "description": "Query ID"
            },
            "user_id": {
                "type": "string",
                "description": "Respondent's Slack User ID"
            },
            "response": {
                "type": "string",
                "description": "Response content"
            }
        },
        "required": ["request_id", "user_id", "response"]
    }
)
async def waiting_answer_update_request(args: Dict[str, Any]) -> Dict[str, Any]:
    """Update specific query response in SQLite + return progress info"""
    request_id = args["request_id"]
    user_id = args["user_id"]
    response = args["response"]

    try:
        # Get query info before update
        request_info = get_request_by_id(request_id, user_id)

        if not request_info:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": f"Query ID '{request_id}' not found."
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

        # Update response
        success = update_response(request_id, user_id, response)

        if not success:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": f"Response update failed"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

        # Check progress
        progress = get_request_progress(request_id)
        all_completed = progress["total"] == progress["completed"]

        # Build result data
        result = {
            "success": True,
            "message": "Response has been updated.",
            "request_id": request_id,
            "progress": progress,
            "all_completed": all_completed,
            "requester_id": request_info["requester_id"],
            "channel_id": request_info["channel_id"],
            "request_content": request_info["request_content"]
        }

        # Include all responses if all completed
        if all_completed:
            result["all_responses"] = get_all_responses_for_request(request_id)

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Query update failed: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


# Create MCP Server
waiting_answer_tools = [
    waiting_answer_update_request,
]


def create_waiting_answer_mcp_server():
    """Waiting Answer MCP server for Claude Code SDK"""
    return create_sdk_mcp_server(
        name="waiting_answer",
        version="1.0.0",
        tools=waiting_answer_tools
    )
