"""
Slack API Helper Functions
Utility functions for querying channel info, user info, etc.
"""

from typing import Dict, Any, Optional, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

# Bot profile image cache
_bot_profile_image: Optional[str] = None


def get_slack_client() -> WebClient:
    """Return Slack WebClient instance"""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        raise ValueError("SLACK_BOT_TOKEN environment variable is not set")
    return WebClient(token=token)


def get_channel_info(channel_id: str) -> Optional[Dict[str, Any]]:
    """
    Get channel info

    Args:
        channel_id: Slack channel ID

    Returns:
        {
            "channel_id": str,
            "channel_name": str,
            "channel_type": str,  # "public_channel", "private_channel", "im", "mpim"
            "is_private": bool,
            "topic": str,
            "purpose": str,
            "member_count": int,
            "members": List[str]  # List of channel member IDs
        }
    """
    client = get_slack_client()

    try:
        # Get channel info
        response = client.conversations_info(channel=channel_id)
        channel = response["channel"]

        # Determine channel type
        if channel.get("is_im"):
            channel_type = "dm"
        elif channel.get("is_mpim"):
            channel_type = "group_dm"
        elif channel.get("is_private"):
            channel_type = "private_channel"
        else:
            channel_type = "public_channel"

        # Get channel members (not for DMs)
        members = []
        if not channel.get("is_im"):
            try:
                members_response = client.conversations_members(channel=channel_id)
                members = members_response["members"]
            except SlackApiError as e:
                print(f"Failed to get channel members: {e}")

        return {
            "channel_id": channel["id"],
            "channel_name": channel.get("name", "Direct Message"),
            "channel_type": channel_type,
            "is_private": channel.get("is_private", False),
            "topic": channel.get("topic", {}).get("value", ""),
            "purpose": channel.get("purpose", {}).get("value", ""),
            "member_count": channel.get("num_members", len(members)),
            "members": members
        }

    except SlackApiError as e:
        print(f"Error fetching channel info: {e}")
        return None


def get_bot_profile_image() -> str:
    """
    Get the Slack bot's profile image URL.

    Returns:
        Bot's profile image URL (512x512)
    """
    global _bot_profile_image

    # Return cached value if exists
    if _bot_profile_image:
        return _bot_profile_image

    client = get_slack_client()

    try:
        # Get bot info
        auth_response = client.auth_test()
        bot_user_id = auth_response.get('user_id')

        # Get bot profile image
        user_info = client.users_info(user=bot_user_id)
        _bot_profile_image = user_info.get('user', {}).get('profile', {}).get('image_512', '')

        print(f"[SLACK] Bot profile image loaded: {bot_user_id}")
        return _bot_profile_image
    except SlackApiError as e:
        print(f"[SLACK] Failed to get bot profile image: {e}")
        # Fallback image
        return "https://ca.slack-edge.com/E01DL1Z9D6Z-U09EV9ED4HL-68cc5ad19dd2-512"


def get_user_info(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user info

    Args:
        user_id: Slack user ID

    Returns:
        {
            "user_id": str,
            "real_name": str,
            "display_name": str,
            "email": str,
            "is_bot": bool,
            "timezone": str
        }
    """
    client = get_slack_client()

    try:
        response = client.users_info(user=user_id)
        user = response["user"]

        return {
            "user_id": user["id"],
            "real_name": user.get("real_name", ""),
            "display_name": user.get("profile", {}).get("display_name", ""),
            "email": user.get("profile", {}).get("email", ""),
            "is_bot": user.get("is_bot", False),
            "timezone": user.get("tz", "")
        }

    except SlackApiError as e:
        print(f"Error fetching user info: {e}")
        return None


def get_channel_members_info(channel_id: str) -> List[Dict[str, Any]]:
    """
    Get detailed info for channel members

    Args:
        channel_id: Slack channel ID

    Returns:
        List of user info dicts
    """
    channel_info = get_channel_info(channel_id)
    if not channel_info:
        return []

    members = channel_info.get("members", [])
    members_info = []

    for user_id in members:
        user_info = get_user_info(user_id)
        if user_info and not user_info["is_bot"]:  # Exclude bots
            members_info.append(user_info)

    return members_info


def get_thread_messages(channel_id: str, thread_ts: str) -> List[Dict[str, Any]]:
    """
    Get all messages in a thread

    Args:
        channel_id: Slack channel ID
        thread_ts: Thread timestamp

    Returns:
        List of message dicts
    """
    client = get_slack_client()

    try:
        response = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )
        return response["messages"]

    except SlackApiError as e:
        print(f"Error fetching thread messages: {e}")
        return []


def get_recent_messages(channel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent messages from a channel

    Args:
        channel_id: Slack channel ID
        limit: Number of messages to retrieve (default 100)

    Returns:
        List of message dicts (newest first)
    """
    client = get_slack_client()

    try:
        response = client.conversations_history(
            channel=channel_id,
            limit=limit
        )
        return response["messages"]

    except SlackApiError as e:
        print(f"Error fetching recent messages: {e}")
        return []


def format_message_for_context(message: Dict[str, Any]) -> str:
    """
    Format Slack message for context storage

    Args:
        message: Slack message dictionary

    Returns:
        Formatted message string (e.g., "[Username]: Message content")
    """
    # Get user info
    user_id = message.get("user")
    if user_id:
        user_info = get_user_info(user_id)
        user_name = user_info["real_name"] if user_info else user_id
    elif message.get("bot_id"):
        user_name = "Bot"
    else:
        user_name = "Unknown"

    text = message.get("text", "")

    return f"[{user_name}]: {text}"


def get_conversation_history_for_context(
    channel_id: str,
    limit: int = 10
) -> List[str]:
    """
    Generate conversation history for ChannelContext storage

    Args:
        channel_id: Slack channel ID
        limit: Number of messages to retrieve

    Returns:
        List of formatted conversation entries (oldest first)
    """
    messages = get_recent_messages(channel_id, limit)

    # Sort oldest first (messages are returned newest first)
    messages.reverse()

    formatted_messages = []
    for msg in messages:
        formatted = format_message_for_context(msg)
        formatted_messages.append(formatted)

    return formatted_messages


def get_slack_context_data(channel_id: str, message_limit: int = 10) -> Dict[str, Any]:
    """
    Gather all Slack data to provide to Orchestrator

    Args:
        channel_id: Slack channel ID
        message_limit: Number of recent messages to retrieve (default 10)

    Returns:
        {
            "channel": {
                "channel_id": str,
                "channel_name": str,
                "channel_type": str,
                "topic": str,
                "purpose": str,
                "member_count": int
            },
            "members": [
                {
                    "user_id": str,
                    "real_name": str,
                    "display_name": str,
                    "email": str
                },
                ...
            ],
            "recent_messages": [
                "[Username]: Message content",
                ...
            ]
        }
    """
    # Get channel info
    channel_info = get_channel_info(channel_id)
    if not channel_info:
        return {
            "channel": {
                "channel_id": channel_id,
                "channel_name": "Unknown",
                "channel_type": "unknown",
                "topic": "",
                "purpose": "",
                "member_count": 0
            },
            "members": [],
            "recent_messages": []
        }

    # Get member info (excluding bots)
    members_info = get_channel_members_info(channel_id)

    # Get recent conversation history
    conversation_history = get_conversation_history_for_context(channel_id, message_limit)

    return {
        "channel": {
            "channel_id": channel_info["channel_id"],
            "channel_name": channel_info["channel_name"],
            "channel_type": channel_info["channel_type"],
            "topic": channel_info["topic"],
            "purpose": channel_info["purpose"],
            "member_count": channel_info["member_count"]
        },
        "members": [
            {
                "user_id": m["user_id"],
                "real_name": m["real_name"],
                "display_name": m["display_name"],
                "email": m["email"]
            }
            for m in members_info
        ],
        "recent_messages": conversation_history
    }


