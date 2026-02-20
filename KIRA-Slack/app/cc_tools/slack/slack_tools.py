"""
Slack Tools for Claude Code SDK
Tools for Claude to directly use the Slack API
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

import httpx
from claude_agent_sdk import create_sdk_mcp_server, tool
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from app.config.settings import get_settings


def get_slack_client() -> AsyncWebClient:
    """Return Slack AsyncWebClient instance"""
    settings = get_settings()
    token = settings.SLACK_BOT_TOKEN
    if not token:
        raise ValueError("SLACK_BOT_TOKEN is not set in settings")
    return AsyncWebClient(token=token)



@tool(
    "add_reaction",
    "Adds an emoji reaction to a message.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Channel ID where the message is located"
            },
            "timestamp": {
                "type": "string",
                "description": "Message timestamp (e.g., 1234567890.123456)"
            },
            "reaction": {
                "type": "string",
                "description": "Reaction emoji name (without colons, e.g., 'thumbsup', 'heart', 'smile')"
            }
        },
        "required": ["channel_id", "timestamp", "reaction"]
    }
)
async def slack_add_reaction(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add reaction to a message"""
    channel_id = args["channel_id"]
    timestamp = args["timestamp"]
    reaction = args["reaction"]

    try:
        client = get_slack_client()
        response = await client.reactions_add(
            channel=channel_id,
            timestamp=timestamp,
            name=reaction
        )

        if response and response.get("ok"):
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "message": f"Reaction '{reaction}' added successfully"
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to add reaction"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "answer_with_emoji",
    "Adds an emoji reaction to the original requester's message as a simple acknowledgment instead of a text response.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "state_data.current_message.channel_id"
            },
            "message_ts": {
                "type": "string",
                "description": "state_data.current_message.message_ts"
            },
            "reaction": {
                "type": "string",
                "description": "Emoji name to add (without colons). Default: 'white_check_mark' (✅)"
            }
        },
        "required": ["channel_id", "message_ts"]
    }
)
async def slack_answer_with_emoji(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add emoji reaction to the original requester's message"""
    channel_id = args["channel_id"]
    message_ts = args["message_ts"]
    reaction = args.get("reaction", "white_check_mark")

    try:
        client = get_slack_client()
        response = await client.reactions_add(
            channel=channel_id,
            timestamp=message_ts,
            name=reaction
        )

        if response and response.get("ok"):
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "message": f"Emoji reaction '{reaction}' added successfully",
                        "channel": channel_id,
                        "timestamp": message_ts
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to add reaction"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
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
                    "message": f"Error: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "answer",
    "Sends a text response to the original requester. Automatically determines the appropriate location (thread/channel) based on channel type. Can be called multiple times.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "state_data.current_message.channel_id"
            },
            "text": {
                "type": "string",
                "description": "Text message content to send"
            },
            "channel_type": {
                "type": "string",
                "description": "state_data.slack_data.channel.channel_type (public_channel, private_channel, dm, group_dm)"
            },
            "message_ts": {
                "type": "string",
                "description": "state_data.current_message.message_ts"
            },
            "thread_ts": {
                "type": "string",
                "description": "state_data.current_message.thread_ts (if available)"
            }
        },
        "required": ["channel_id", "text", "channel_type", "message_ts"]
    }
)
async def slack_answer(args: Dict[str, Any]) -> Dict[str, Any]:
    """Send text response to the original requester"""
    channel_id = args["channel_id"]
    text = args["text"]
    channel_type = args["channel_type"]
    message_ts = args["message_ts"]
    thread_ts = args.get("thread_ts")

    try:
        client = get_slack_client()

        # Calculate thread_ts based on channel_type
        if channel_type in ["public_channel", "private_channel", "group_dm"]:
            # Group channels: always reply in thread
            final_thread_ts = thread_ts or message_ts
        elif channel_type in ["dm"]:
            # DM/Group DM: use thread if exists, otherwise send as regular message
            final_thread_ts = thread_ts
        else:
            final_thread_ts = None

        # Send message
        post_params = {
            "channel": channel_id,
            "text": text
        }

        if final_thread_ts:
            post_params["thread_ts"] = final_thread_ts

        response = await client.chat_postMessage(**post_params)

        if response and response.get("ok"):
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "message": "Response sent successfully",
                        "channel": channel_id,
                        "ts": response.get("ts"),
                        "thread_ts": final_thread_ts
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            error_msg = response.get("error", "Unknown error") if response else "Unknown error"
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": f"Failed to send message: {error_msg}"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
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
                    "message": f"Error: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "forward_message",
    "Forwards a message to another person/channel. When sending the same content to multiple people, include all recipients in respondents and call only once. Duplicate calls are strictly prohibited!",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Slack channel ID to send message to (e.g., C12345) or user DM ID (e.g., D12345)"
            },
            "text": {
                "type": "string",
                "description": "Message content to send"
            },
            "request_answer": {
                "type": "boolean",
                "description": "Set to True if a response is needed. If False, only sends the message. (Default: False)"
            },
            "respondents": {
                "type": "array",
                "description": "List of people to receive responses from. Required when request_answer=True. When asking the same question to multiple people, include all users in this array and call only once. Duplicate calls prohibited! Each item must include user_id and name.",
                "items": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Respondent's Slack User ID (e.g., U1234567890)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Respondent's name"
                        }
                    },
                    "required": ["user_id", "name"]
                }
            },
            "requester_id": {
                "type": "string",
                "description": "Slack User ID of the person requesting the response. Required when request_answer=True. Get from state_data.current_message.user_id."
            },
            "requester_name": {
                "type": "string",
                "description": "Name of the person requesting the response. Required when request_answer=True. Get from state_data.current_message.user_name."
            }
        },
        "required": ["channel_id", "text"]
    }
)
async def slack_forward_message(args: Dict[str, Any]) -> Dict[str, Any]:
    """Forward message to another person + optional response waiting registration"""
    channel_id = args.get("channel_id")
    text = args["text"]
    request_answer = args.get("request_answer", False)
    respondents = args.get("respondents", [])
    requester_id = args.get("requester_id")
    requester_name = args.get("requester_name")

    try:
        client = get_slack_client()

        # When request_answer=True: send DM to each respondent
        if request_answer:
            if not respondents or not requester_id or not requester_name:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": True,
                            "message": "respondents, requester_id, and requester_name are required when request_answer=True."
                        }, ensure_ascii=False, indent=2)
                    }],
                    "error": True
                }

            # Generate a single request_id
            import uuid
            from app.cc_utils.waiting_answer_db import add_request

            request_id = str(uuid.uuid4())[:8]

            # Send DM to each respondent
            sent_channels = []
            for respondent in respondents:
                user_id = respondent.get("user_id")
                # Open DM channel
                dm_response = await client.conversations_open(users=user_id)
                dm_channel_id = dm_response["channel"]["id"]

                # Send message
                await client.chat_postMessage(
                    channel=dm_channel_id,
                    text=text
                )
                sent_channels.append(dm_channel_id)

            # Register in waiting_answer (all respondents under one request_id)
            count = add_request(
                request_id=request_id,
                channel_id=sent_channels[0] if sent_channels else "unknown",
                requester_id=requester_id,
                requester_name=requester_name,
                request_content=text,
                respondents=respondents
            )

            result = {
                "success": True,
                "message": f"Message sent to {len(respondents)} people and response waiting registered",
                "sent_to": [r.get("name") for r in respondents],
                "waiting_answer": {
                    "registered": True,
                    "request_id": request_id,
                    "respondent_count": count
                }
            }

        # When request_answer=False: just send message to channel_id
        else:
            if not channel_id:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": True,
                            "message": "channel_id is required when request_answer=False."
                        }, ensure_ascii=False, indent=2)
                    }],
                    "error": True
                }

            response = await client.chat_postMessage(
                channel=channel_id,
                text=text
            )

            result = {
                "success": True,
                "message": "Message sent successfully",
                "channel": response["channel"],
                "ts": response["ts"]
            }

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, indent=2)
            }]
        }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
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
                    "message": f"Error: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "reply_to_thread",
    "Replies to a Slack thread.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Channel ID where the thread is located"
            },
            "thread_ts": {
                "type": "string",
                "description": "Thread timestamp (e.g., 1234567890.123456)"
            },
            "text": {
                "type": "string",
                "description": "Reply content"
            }
        },
        "required": ["channel_id", "thread_ts", "text"]
    }
)
async def slack_reply_to_thread(args: Dict[str, Any]) -> Dict[str, Any]:
    """Reply to Slack thread"""
    channel_id = args["channel_id"]
    thread_ts = args["thread_ts"]
    text = args["text"]

    try:
        client = get_slack_client()
        response = await client.chat_postMessage(
            channel=channel_id,
            text=text,
            thread_ts=thread_ts
        )

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "message": "Thread reply sent successfully",
                    "channel": response["channel"],
                    "ts": response["ts"],
                    "thread_ts": response["thread_ts"]
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
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "upload_file",
    "Uploads a local file to the original requester. Automatically determines the appropriate location (thread/channel) based on channel type. Can be called multiple times.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "state_data.current_message.channel_id"
            },
            "file_path": {
                "type": "string",
                "description": "Absolute path of the local file to upload (e.g., FILESYSTEM_BASE_DIR/tmp/report.pdf)"
            },
            "channel_type": {
                "type": "string",
                "description": "state_data.slack_data.channel.channel_type (public_channel, private_channel, dm, group_dm)"
            },
            "message_ts": {
                "type": "string",
                "description": "state_data.current_message.message_ts"
            },
            "thread_ts": {
                "type": "string",
                "description": "state_data.current_message.thread_ts (if available)"
            },
            "initial_comment": {
                "type": "string",
                "description": "Message to send with the file (optional)"
            }
        },
        "required": ["channel_id", "file_path", "channel_type", "message_ts"]
    }
)
async def slack_upload_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """Slack file upload"""
    channel_id = args["channel_id"]
    file_path = args["file_path"]
    channel_type = args["channel_type"]
    message_ts = args["message_ts"]
    thread_ts = args.get("thread_ts")
    initial_comment = args.get("initial_comment")

    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": f"File does not exist: {file_path}"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

        client = get_slack_client()

        # Calculate thread_ts based on channel_type
        if channel_type in ["public_channel", "private_channel", "group_dm"]:
            # Group channels: always upload to thread
            final_thread_ts = thread_ts or message_ts
        elif channel_type in ["dm"]:
            # DM/Group DM: use thread if exists, otherwise send as regular message
            final_thread_ts = thread_ts
        else:
            final_thread_ts = None

        upload_params = {
            "channel": channel_id,
            "file": str(file_path_obj.absolute())
        }

        if final_thread_ts:
            upload_params["thread_ts"] = final_thread_ts

        if initial_comment:
            upload_params["initial_comment"] = initial_comment

        response = await client.files_upload_v2(**upload_params)

        if response and response.get("ok"):
            file_info = response.get("file", {})
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "message": "File uploaded successfully",
                        "file_id": file_info.get("id"),
                        "file_name": file_info.get("name"),
                        "permalink": file_info.get("permalink")
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            error_msg = response.get("error", "Unknown error") if response else "Unknown error"
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": f"File upload failed: {error_msg}"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
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
                    "message": f"Error: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "download_file_to_channel",
    "Downloads a Slack file to a channel-specific folder. Downloaded files are saved to FILESYSTEM_BASE_DIR/files/{channel_id}/.",
    {
        "type": "object",
        "properties": {
            "url_private": {
                "type": "string",
                "description": "Private URL of the Slack file"
            },
            "channel_id": {
                "type": "string",
                "description": "Slack channel ID"
            },
            "filename": {
                "type": "string",
                "description": "Filename to save as (optional, defaults to extracting from URL)"
            }
        },
        "required": ["url_private", "channel_id"]
    }
)
async def slack_download_file_to_channel(args: Dict[str, Any]) -> Dict[str, Any]:
    """Download Slack file to channel-specific folder"""
    url_private = args["url_private"]
    channel_id = args["channel_id"]
    filename = args.get("filename")

    try:
        # Extract filename from URL
        if not filename:
            url_parts = url_private.split("/")
            for part in reversed(url_parts):
                if "." in part and not part.startswith("."):
                    filename = part
                    break

            if not filename:
                filename = "downloaded_file"

        # Download file with Slack auth header
        settings = get_settings()
        headers = {"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"}
        chunk_size = 1_048_576  # 1MB chunks

        async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
            async with client.stream("GET", url_private, timeout=None) as resp:
                resp.raise_for_status()

                # Save to FILESYSTEM_BASE_DIR/files/{channel_id} directory
                base_dir = settings.FILESYSTEM_BASE_DIR or os.getcwd()
                channel_dir = Path(base_dir) / "files" / channel_id
                channel_dir.mkdir(parents=True, exist_ok=True)
                file_path = channel_dir / filename

                with open(file_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size):
                        if chunk:
                            f.write(chunk)

        # Check file size
        file_size = file_path.stat().st_size
        file_size_mb = round(file_size / (1024 * 1024), 2)

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "message": "File downloaded successfully",
                    "filename": filename,
                    "file_path": str(file_path),
                    "file_size_bytes": file_size,
                    "file_size_mb": file_size_mb
                }, ensure_ascii=False, indent=2)
            }]
        }

    except httpx.HTTPStatusError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"HTTP error: {e.response.status_code}"
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
                    "message": f"Error: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "transfer_file",
    "Transfers a local file or Slack file to another channel or user.",
    {
        "type": "object",
        "properties": {
            "channel_or_user_id": {
                "type": "string",
                "description": "Channel ID (starts with C) or DM ID (starts with D) to send the file to"
            },
            "file_url": {
                "type": "string",
                "description": "Local file path (file:// or absolute path), Slack url_private, or external file URL"
            },
            "filename": {
                "type": "string",
                "description": "Filename to transfer"
            },
            "thread_ts": {
                "type": "string",
                "description": "Thread timestamp (for uploading within a thread)"
            },
            "initial_comment": {
                "type": "string",
                "description": "Message to send with the file"
            }
        },
        "required": ["channel_or_user_id", "file_url", "filename"]
    }
)
async def slack_transfer_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """Transfer local file or Slack file"""
    channel_or_user_id = args["channel_or_user_id"]
    file_url = args["file_url"]
    filename = args["filename"]
    thread_ts = args.get("thread_ts")
    initial_comment = args.get("initial_comment")

    try:
        # Check if it's a local file path
        is_local_file = False
        local_file_path = None

        # Remove file:// protocol
        if file_url.startswith("file://"):
            local_file_path = Path(file_url.replace("file://", ""))
            is_local_file = True
        # If it's an absolute path (starts with /, ~/, ./, etc.)
        elif not file_url.startswith("http://") and not file_url.startswith("https://"):
            local_file_path = Path(file_url)
            is_local_file = True

        # If it's a local file
        if is_local_file:
            if not local_file_path.exists():
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": True,
                            "message": f"File does not exist: {local_file_path}"
                        }, ensure_ascii=False, indent=2)
                    }],
                    "error": True
                }

            # Direct upload
            client = get_slack_client()
            upload_params = {
                "channel": channel_or_user_id,
                "file": str(local_file_path.absolute())
            }

            if thread_ts:
                upload_params["thread_ts"] = thread_ts
            if initial_comment:
                upload_params["initial_comment"] = initial_comment

            response = await client.files_upload_v2(**upload_params)

        # If it's an HTTP/HTTPS URL (existing logic)
        else:
            settings = get_settings()
            headers = {"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"}

            async with httpx.AsyncClient(follow_redirects=True, headers=headers) as http_client:
                async with http_client.stream("GET", file_url, timeout=None) as resp:
                    resp.raise_for_status()

                    # Save to temp file
                    temp_file = Path("/tmp") / filename
                    with open(temp_file, "wb") as f:
                        async for chunk in resp.aiter_bytes(1_048_576):
                            if chunk:
                                f.write(chunk)

            # Upload file
            client = get_slack_client()
            upload_params = {
                "channel": channel_or_user_id,
                "file": str(temp_file.absolute())
            }

            if thread_ts:
                upload_params["thread_ts"] = thread_ts
            if initial_comment:
                upload_params["initial_comment"] = initial_comment

            response = await client.files_upload_v2(**upload_params)

            # Delete temp file
            temp_file.unlink()

        if response and response.get("ok"):
            file_info = response.get("file", {})
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "message": "File transferred successfully",
                        "file_id": file_info.get("id"),
                        "file_name": file_info.get("name"),
                        "permalink": file_info.get("permalink")
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            error_msg = response.get("error", "Unknown error") if response else "Unknown error"
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": f"File transfer failed: {error_msg}"
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
                    "message": f"Error: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "get_user_profile",
    "Retrieves Slack user profile information.",
    {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "Slack user ID (e.g., U1234567890)"
            }
        },
        "required": ["user_id"]
    }
)
async def slack_get_user_profile(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get Slack user profile"""
    user_id = args["user_id"]

    try:
        client = get_slack_client()
        response = await client.users_info(user=user_id)

        if response and response.get("ok"):
            user = response.get("user", {})
            profile = user.get("profile", {})

            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "user_id": user.get("id"),
                        "real_name": user.get("real_name"),
                        "display_name": profile.get("display_name"),
                        "email": profile.get("email"),
                        "is_bot": user.get("is_bot", False)
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to retrieve user information"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "get_thread_replies",
    "Retrieves all replies in a thread.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Channel ID where the thread is located"
            },
            "thread_ts": {
                "type": "string",
                "description": "Thread timestamp (e.g., 1234567890.123456)"
            }
        },
        "required": ["channel_id", "thread_ts"]
    }
)
async def slack_get_thread_replies(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get thread replies"""
    channel_id = args["channel_id"]
    thread_ts = args["thread_ts"]

    try:
        client = get_slack_client()
        response = await client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )

        if response and response.get("ok"):
            messages = response.get("messages", [])
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "message_count": len(messages),
                        "messages": messages
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to retrieve thread replies"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "get_channel_history",
    "Retrieves message history from a channel.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Channel ID to retrieve messages from"
            },
            "limit": {
                "type": "integer",
                "description": "Number of messages to retrieve (default: 10, max: 100)"
            },
            "oldest": {
                "type": "string",
                "description": "Only retrieve messages after this timestamp (e.g., 1234567890.123456)"
            },
            "latest": {
                "type": "string",
                "description": "Only retrieve messages before this timestamp (e.g., 1234567890.123456)"
            }
        },
        "required": ["channel_id"]
    }
)
async def slack_get_channel_history(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get channel history"""
    channel_id = args["channel_id"]
    limit = args.get("limit", 10)
    oldest = args.get("oldest")
    latest = args.get("latest")

    try:
        client = get_slack_client()

        params = {
            "channel": channel_id,
            "limit": limit
        }

        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest

        response = await client.conversations_history(**params)

        if response and response.get("ok"):
            messages = response.get("messages", [])
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "message_count": len(messages),
                        "messages": messages,
                        "has_more": response.get("has_more", False)
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to retrieve channel history"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "get_usergroup_members",
    "Retrieves the member list of a usergroup.",
    {
        "type": "object",
        "properties": {
            "usergroup_id": {
                "type": "string",
                "description": "Usergroup ID (e.g., S1234567890). ID extracted from tag format"
            }
        },
        "required": ["usergroup_id"]
    }
)
async def slack_get_usergroup_members(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get usergroup members"""
    usergroup_id = args["usergroup_id"]

    try:
        client = get_slack_client()
        response = await client.usergroups_users_list(usergroup=usergroup_id)

        if response and response.get("ok"):
            users = response.get("users", [])
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "usergroup_id": usergroup_id,
                        "user_count": len(users),
                        "users": users
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to retrieve usergroup members"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "get_permalink",
    "Retrieves the permalink for a specific message.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Channel ID where the message is located"
            },
            "message_ts": {
                "type": "string",
                "description": "Message timestamp (e.g., 1234567890.123456)"
            }
        },
        "required": ["channel_id", "message_ts"]
    }
)
async def slack_get_permalink(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get message permalink"""
    channel_id = args["channel_id"]
    message_ts = args["message_ts"]

    try:
        client = get_slack_client()
        response = await client.chat_getPermalink(
            channel=channel_id,
            message_ts=message_ts
        )

        if response and response.get("ok"):
            permalink = response.get("permalink")
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "channel_id": channel_id,
                        "message_ts": message_ts,
                        "permalink": permalink
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to retrieve permalink"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "get_dm_channel_id",
    "Retrieves the DM channel ID for a specific user.",
    {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "Slack user ID to send DM to (e.g., U1234567890)"
            }
        },
        "required": ["user_id"]
    }
)
async def slack_get_dm_channel_id(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get DM channel ID for a user"""
    user_id = args["user_id"]

    try:
        client = get_slack_client()
        response = await client.conversations_open(users=[user_id])

        if response and response.get("ok"):
            channel = response.get("channel", {})
            channel_id = channel.get("id")

            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "user_id": user_id,
                        "dm_channel_id": channel_id,
                        "message": f"DM channel ID for user {user_id}: {channel_id}"
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to retrieve DM channel ID"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "find_user_by_name",
    "Searches for a Slack user by name and returns their user_id.",
    {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "User name to search for (real_name or display_name)"
            }
        },
        "required": ["name"]
    }
)
async def slack_find_user_by_name(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search user by name"""
    search_name = args["name"].strip().lower()

    try:
        client = get_slack_client()
        response = await client.users_list()

        if response and response.get("ok"):
            members = response.get("members", [])
            matches = []

            for user in members:
                if user.get("deleted") or user.get("is_bot"):
                    continue

                real_name = user.get("real_name", "").lower()
                profile = user.get("profile", {})
                display_name = profile.get("display_name", "").lower()

                if search_name in real_name or search_name in display_name:
                    matches.append({
                        "user_id": user.get("id"),
                        "real_name": user.get("real_name"),
                        "display_name": profile.get("display_name"),
                        "email": profile.get("email")
                    })

            if matches:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "matches": matches,
                            "count": len(matches),
                            "message": f"Found {len(matches)} user(s)"
                        }, ensure_ascii=False, indent=2)
                    }]
                }
            else:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "matches": [],
                            "count": 0,
                            "message": f"No users found matching '{args['name']}'"
                        }, ensure_ascii=False, indent=2)
                    }]
                }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to retrieve user list"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "get_channel_info",
    "Retrieves channel information.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Slack channel ID (e.g., C1234567890)"
            }
        },
        "required": ["channel_id"]
    }
)
async def slack_get_channel_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get channel information"""
    channel_id = args["channel_id"]

    try:
        client = get_slack_client()
        response = await client.conversations_info(channel=channel_id)

        if response and response.get("ok"):
            channel = response.get("channel", {})

            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "channel_id": channel.get("id"),
                        "channel_name": channel.get("name"),
                        "is_channel": channel.get("is_channel", False),
                        "is_group": channel.get("is_group", False),
                        "is_im": channel.get("is_im", False),
                        "is_private": channel.get("is_private", False)
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to retrieve channel information"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "create_canvas",
    "Creates a new canvas in a channel.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Channel ID to create the canvas in (e.g., C1234567890)"
            },
            "title": {
                "type": "string",
                "description": "Canvas title"
            },
            "content": {
                "type": "string",
                "description": "Canvas content (Markdown format)"
            }
        },
        "required": ["channel_id", "title", "content"]
    }
)
async def slack_create_canvas(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create canvas in channel"""
    channel_id = args["channel_id"]
    title = args["title"]
    content = args["content"]

    try:
        client = get_slack_client()

        # Create canvas
        response = await client.canvases_create(
            title=title,
            document_content={
                "type": "markdown",
                "markdown": content
            }
        )

        if response and response.get("ok"):
            canvas_id = response.get("canvas_id")

            # Share canvas to channel
            share_response = await client.chat_postMessage(
                channel=channel_id,
                text=f"📄 {title}",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{title}*"
                        },
                        "accessory": {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Open Canvas"
                            },
                            "url": f"slack://canvas/{canvas_id}"
                        }
                    }
                ]
            )

            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "canvas_id": canvas_id,
                        "message": f"Canvas '{title}' has been created."
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to create canvas"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "list_channel_canvases",
    "Retrieves the list of canvases in a channel.",
    {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Channel ID to retrieve canvases from (e.g., C1234567890)"
            }
        },
        "required": ["channel_id"]
    }
)
async def slack_list_channel_canvases(args: Dict[str, Any]) -> Dict[str, Any]:
    """List channel canvases"""
    channel_id = args["channel_id"]

    try:
        client = get_slack_client()

        # Find canvases in channel message history
        response = await client.conversations_history(
            channel=channel_id,
            limit=100
        )

        if response and response.get("ok"):
            messages = response.get("messages", [])
            canvases = []

            for msg in messages:
                # Find messages with canvas attachments
                files = msg.get("files", [])
                for file in files:
                    if file.get("filetype") == "canvas":
                        canvases.append({
                            "canvas_id": file.get("id"),
                            "title": file.get("title", "Untitled"),
                            "created": file.get("created", 0),
                            "url": file.get("permalink", "")
                        })

            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "channel_id": channel_id,
                        "canvases": canvases,
                        "count": len(canvases)
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to retrieve channel history"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "get_canvas",
    "Retrieves the content of a canvas.",
    {
        "type": "object",
        "properties": {
            "canvas_id": {
                "type": "string",
                "description": "Canvas ID to retrieve"
            }
        },
        "required": ["canvas_id"]
    }
)
async def slack_get_canvas(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get canvas content"""
    canvas_id = args["canvas_id"]

    try:
        client = get_slack_client()
        response = await client.canvases_sections_lookup(canvas_id=canvas_id)

        if response and response.get("ok"):
            sections = response.get("sections", [])

            # Combine section contents to Markdown
            content_parts = []
            for section in sections:
                if section.get("section_type") == "any_header_block":
                    content_parts.append(f"# {section.get('text', '')}")
                elif section.get("section_type") == "markdown":
                    content_parts.append(section.get("markdown", ""))

            content = "\n\n".join(content_parts)

            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "canvas_id": canvas_id,
                        "content": content
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to retrieve canvas"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "edit_canvas",
    "Edits the content of a canvas.",
    {
        "type": "object",
        "properties": {
            "canvas_id": {
                "type": "string",
                "description": "Canvas ID to edit"
            },
            "content": {
                "type": "string",
                "description": "New canvas content (Markdown format)"
            }
        },
        "required": ["canvas_id", "content"]
    }
)
async def slack_edit_canvas(args: Dict[str, Any]) -> Dict[str, Any]:
    """Edit canvas content"""
    canvas_id = args["canvas_id"]
    content = args["content"]

    try:
        client = get_slack_client()

        # Edit canvas
        response = await client.canvases_edit(
            canvas_id=canvas_id,
            changes=[
                {
                    "operation": "replace",
                    "document_content": {
                        "type": "markdown",
                        "markdown": content
                    }
                }
            ]
        )

        if response and response.get("ok"):
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "canvas_id": canvas_id,
                        "message": "Canvas has been updated."
                    }, ensure_ascii=False, indent=2)
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": "Failed to edit canvas"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

    except SlackApiError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Slack API error: {e.response['error']}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


# MCP Server creation
slack_tools = [
    slack_add_reaction,
    slack_answer_with_emoji,
    slack_answer,
    slack_forward_message,
    slack_reply_to_thread,
    slack_upload_file,
    slack_download_file_to_channel,
    slack_transfer_file,
    slack_get_user_profile,
    slack_get_thread_replies,
    slack_get_channel_history,
    slack_get_usergroup_members,
    slack_get_permalink,
    slack_get_dm_channel_id,
    slack_find_user_by_name,
    slack_get_channel_info,
    slack_create_canvas,
    slack_list_channel_canvases,
    slack_get_canvas,
    slack_edit_canvas,
]


def create_slack_mcp_server():
    """Slack MCP server for Claude Code SDK"""
    return create_sdk_mcp_server(
        name="slack",
        version="1.0.0",
        tools=slack_tools
    )
