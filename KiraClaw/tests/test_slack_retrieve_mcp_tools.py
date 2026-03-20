from __future__ import annotations

import json

from kiraclaw_agentd.slack_retrieve_mcp_tools import build_slack_retrieve_tool_specs


class FakeSlackRetrieveClient:
    def conversations_list(self, **kwargs):
        return {
            "channels": [
                {
                    "id": "C123",
                    "name": "general",
                    "is_private": False,
                    "is_im": False,
                    "is_mpim": False,
                    "topic": {"value": "General discussion"},
                    "purpose": {"value": "Team-wide chatter"},
                },
                {
                    "id": "C999",
                    "name": "project-updates",
                    "is_private": True,
                    "is_im": False,
                    "is_mpim": False,
                    "topic": {"value": "Project updates"},
                    "purpose": {"value": "Status"},
                },
            ]
        }

    def users_list(self, **kwargs):
        return {
            "members": [
                {
                    "id": "U123",
                    "name": "jiho",
                    "profile": {
                        "display_name": "Jiho",
                        "real_name": "Jiho Jeon",
                    },
                    "is_bot": False,
                },
                {
                    "id": "U456",
                    "name": "sena",
                    "profile": {
                        "display_name": "세나",
                        "real_name": "Sena Bot",
                    },
                    "is_bot": True,
                },
            ]
        }

    def conversations_info(self, **kwargs):
        if kwargs["channel"] == "C123":
            return {"channel": {"id": "C123", "name": "general"}}
        raise AssertionError(f"unexpected channel lookup: {kwargs}")

    def conversations_history(self, **kwargs):
        return {
            "messages": [
                {
                    "ts": "111.222",
                    "thread_ts": "111.222",
                    "user": "U123",
                    "text": "hello from history",
                }
            ],
            "has_more": False,
        }

    def conversations_replies(self, **kwargs):
        return {
            "messages": [
                {
                    "ts": "111.222",
                    "thread_ts": "111.222",
                    "user": "U123",
                    "text": "thread root",
                },
                {
                    "ts": "111.333",
                    "thread_ts": "111.222",
                    "user": "U456",
                    "text": "thread reply",
                },
            ],
            "has_more": False,
        }

    def search_messages(self, **kwargs):
        return {
            "messages": {
                "matches": [
                    {
                        "channel": {"id": "C999", "name": "project-updates"},
                        "user": "U123",
                        "username": "jiho",
                        "ts": "222.333",
                        "text": "deployment finished",
                        "permalink": "https://slack.example/archives/C999/p222333",
                    }
                ]
            }
        }


def _tool_map():
    client = FakeSlackRetrieveClient()
    return {tool.name: tool for tool in build_slack_retrieve_tool_specs(client_factory=lambda: client)}


def _payload(result: dict) -> dict:
    return json.loads(result["content"][0]["text"])


def test_slack_retrieve_lists_channels_and_users() -> None:
    tools = _tool_map()

    channels = _payload(tools["slack_list_channels"].handler({"query": "project"}))
    users = _payload(tools["slack_list_users"].handler({"query": "jiho"}))

    assert channels["success"] is True
    assert channels["count"] == 1
    assert channels["channels"][0]["id"] == "C999"
    assert users["success"] is True
    assert users["count"] == 1
    assert users["users"][0]["id"] == "U123"


def test_slack_retrieve_reads_history_and_thread() -> None:
    tools = _tool_map()

    history = _payload(tools["slack_read_channel_history"].handler({"channel_ref": "#general", "limit": 10}))
    history_by_hash_id = _payload(tools["slack_read_channel_history"].handler({"channel_ref": "#C123", "limit": 10}))
    thread = _payload(tools["slack_read_thread"].handler({"channel_ref": "C123", "thread_ts": "111.222"}))

    assert history["success"] is True
    assert history["channel_id"] == "C123"
    assert history["messages"][0]["text"] == "hello from history"
    assert history_by_hash_id["success"] is True
    assert history_by_hash_id["channel_id"] == "C123"
    assert thread["success"] is True
    assert thread["thread_ts"] == "111.222"
    assert len(thread["messages"]) == 2


def test_slack_retrieve_searches_messages() -> None:
    tools = _tool_map()

    result = _payload(tools["slack_search_messages"].handler({"query": "deployment"}))

    assert result["success"] is True
    assert result["count"] == 1
    assert result["matches"][0]["channel_name"] == "project-updates"


def test_slack_retrieve_lists_recent_participants() -> None:
    tools = _tool_map()

    result = _payload(tools["slack_list_recent_participants"].handler({"channel_ref": "#C123", "limit": 30}))

    assert result["success"] is True
    assert result["channel_id"] == "C123"
    assert result["lookback_messages"] == 1
    assert result["count"] == 1
    assert result["participants"][0]["id"] == "U123"
