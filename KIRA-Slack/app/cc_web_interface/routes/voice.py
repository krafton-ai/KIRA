"""
Voice Routes
Voice input WebSocket and related routes
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from slack_sdk.web.async_client import AsyncWebClient

from app.queueing_extended import enqueue_message
from app.cc_web_interface.utils import get_slack_user_id
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["voice"])


@router.websocket("/voice")
async def websocket_voice(websocket: WebSocket):
    """Voice input WebSocket endpoint"""
    await websocket.accept()

    settings = get_settings()
    slack_client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)

    try:
        while True:
            data = await websocket.receive_json()

            # Frontend sends voice_text type
            if data.get("type") == "voice_text":
                message = data.get("text", "").strip()
                user_info = data.get("user", {})

                if message and user_info:
                    # Look up Slack user_id by user email
                    user_email = user_info.get("email")
                    user_name = user_info.get("name", "Unknown")

                    if not user_email:
                        logger.warning(f"[VOICE] No email in user_info: {user_info}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "User email information is missing. Please log in again."
                        })
                        continue

                    # Look up Slack user_id by email
                    slack_user_id = await get_slack_user_id(user_email, slack_client)

                    if not slack_user_id:
                        logger.error(f"[VOICE] Failed to get Slack user ID for email: {user_email}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Could not find Slack user."
                        })
                        continue

                    # Get DM channel ID
                    try:
                        dm_response = await slack_client.conversations_open(users=[slack_user_id])
                        dm_channel_id = dm_response["channel"]["id"]
                    except Exception as e:
                        logger.error(f"[VOICE] Failed to get DM channel: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Could not open Slack DM channel."
                        })
                        continue

                    logger.info(f"[VOICE] Received from {user_name}({slack_user_id}): {message[:50]}...")

                    # Add to message queue (using actual DM channel)
                    await enqueue_message({
                        "text": message,
                        "channel": dm_channel_id,
                        "ts": "",
                        "user": slack_user_id,
                        "thread_ts": None,
                    })

                    await websocket.send_json({
                        "type": "processed",
                        "message": f"Processing '{message[:30]}...'"
                    })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()