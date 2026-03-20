from __future__ import annotations

import os
import re
from typing import Any, Callable

from slack_sdk import WebClient

from kiraclaw_agentd.mcp_stdio import McpToolSpec, mcp_text_result


SlackClientFactory = Callable[[], Any]
_CHANNEL_ID_PATTERN = re.compile(r"^[CDG][A-Z0-9]+$")
_USER_ID_PATTERN = re.compile(r"^U[A-Z0-9]+$")


def _default_client_factory() -> SlackClientFactory:
    token = os.environ.get("KIRACLAW_SLACK_RETRIEVE_TOKEN", "").strip()
    return lambda: WebClient(token=token)


def _normalize_lookup_key(value: str) -> str:
    return re.sub(r"[\s._-]+", "", value.strip().lower())


def _lookup_variants(value: str) -> list[str]:
    base = value.strip()
    if not base:
        return []
    variants = {base, base.lstrip("@#")}
    trimmed = base.lstrip("@#").strip()
    for suffix in ("님", "씨", "선생님"):
        if trimmed.endswith(suffix):
            variants.add(trimmed[: -len(suffix)].strip())
    return [variant for variant in variants if variant.strip()]


def _extract_id(value: str) -> str | None:
    stripped = value.strip()
    channel_match = re.match(r"^<#([CDG][A-Z0-9]+)(?:\|[^>]+)?>$", stripped)
    if channel_match:
        return channel_match.group(1)
    user_match = re.match(r"^<@([U][A-Z0-9]+)>$", stripped)
    if user_match:
        return user_match.group(1)
    hash_channel_id_match = re.match(r"^#([CDG][A-Z0-9]+)$", stripped)
    if hash_channel_id_match:
        return hash_channel_id_match.group(1)
    if _CHANNEL_ID_PATTERN.fullmatch(stripped) or _USER_ID_PATTERN.fullmatch(stripped):
        return stripped
    return None


def _iter_conversations(client: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        response = client.conversations_list(
            types="public_channel,private_channel,mpim,im",
            limit=1000,
            cursor=cursor,
        )
        rows.extend(response.get("channels", []))
        cursor = ((response.get("response_metadata", {}) or {}).get("next_cursor")) or None
        if not cursor:
            return rows


def _iter_users(client: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        response = client.users_list(limit=1000, cursor=cursor)
        rows.extend(response.get("members", []))
        cursor = ((response.get("response_metadata", {}) or {}).get("next_cursor")) or None
        if not cursor:
            return rows


def _find_channel(client: Any, channel_ref: str) -> dict[str, Any] | None:
    extracted = _extract_id(channel_ref)
    if extracted and _CHANNEL_ID_PATTERN.fullmatch(extracted):
        response = client.conversations_info(channel=extracted)
        return response.get("channel")

    lookups = [_normalize_lookup_key(variant) for variant in _lookup_variants(channel_ref)]
    lookups = [lookup for lookup in lookups if lookup]
    if not lookups:
        return None
    for channel in _iter_conversations(client):
        name = str(channel.get("name", "")).strip()
        if name and _normalize_lookup_key(name) in lookups:
            return channel
    return None


def _resolve_channel_id(client: Any, channel_ref: str) -> str:
    channel = _find_channel(client, channel_ref)
    if not channel or not channel.get("id"):
        raise ValueError(f"Slack channel not found: {channel_ref}")
    return str(channel["id"])


def _format_message(message: dict[str, Any]) -> dict[str, Any]:
    user_profile = message.get("user_profile") or {}
    return {
        "ts": str(message.get("ts", "")),
        "thread_ts": str(message.get("thread_ts", "")),
        "user": str(message.get("user", "")),
        "username": str(message.get("username", "")),
        "display_name": str(user_profile.get("display_name") or user_profile.get("real_name") or ""),
        "text": str(message.get("text", "")),
        "subtype": str(message.get("subtype", "")),
    }


def _make_result(handler: Callable[[dict[str, Any], Any], dict[str, Any]], args: dict[str, Any], client_factory: SlackClientFactory) -> dict[str, Any]:
    try:
        client = client_factory()
        return mcp_text_result(handler(args, client))
    except Exception as exc:
        return mcp_text_result({"success": False, "error": str(exc)}, is_error=True)


def _list_channels(args: dict[str, Any], client: Any) -> dict[str, Any]:
    query = str(args.get("query", "")).strip().lower()
    limit = max(1, min(int(args.get("limit", 50)), 200))
    rows = []
    for channel in _iter_conversations(client):
        name = str(channel.get("name", ""))
        if query and query not in name.lower():
            continue
        rows.append(
            {
                "id": str(channel.get("id", "")),
                "name": name,
                "is_private": bool(channel.get("is_private")),
                "is_im": bool(channel.get("is_im")),
                "is_mpim": bool(channel.get("is_mpim")),
                "topic": str((channel.get("topic") or {}).get("value", "")),
                "purpose": str((channel.get("purpose") or {}).get("value", "")),
            }
        )
        if len(rows) >= limit:
            break
    return {"success": True, "channels": rows, "count": len(rows)}


def _list_users(args: dict[str, Any], client: Any) -> dict[str, Any]:
    query = str(args.get("query", "")).strip().lower()
    limit = max(1, min(int(args.get("limit", 50)), 200))
    rows = []
    for member in _iter_users(client):
        if member.get("deleted"):
            continue
        profile = member.get("profile") or {}
        display_name = str(profile.get("display_name") or profile.get("display_name_normalized") or "")
        real_name = str(profile.get("real_name") or profile.get("real_name_normalized") or "")
        candidates = [str(member.get("name", "")), display_name, real_name]
        if query and not any(query in candidate.lower() for candidate in candidates if candidate):
            continue
        rows.append(
            {
                "id": str(member.get("id", "")),
                "name": str(member.get("name", "")),
                "display_name": display_name,
                "real_name": real_name,
                "is_bot": bool(member.get("is_bot")),
            }
        )
        if len(rows) >= limit:
            break
    return {"success": True, "users": rows, "count": len(rows)}


def _read_channel_history(args: dict[str, Any], client: Any) -> dict[str, Any]:
    channel_ref = str(args["channel_ref"]).strip()
    channel_id = _resolve_channel_id(client, channel_ref)
    limit = max(1, min(int(args.get("limit", 20)), 100))
    response = client.conversations_history(
        channel=channel_id,
        limit=limit,
        oldest=str(args.get("oldest", "")).strip() or None,
        latest=str(args.get("latest", "")).strip() or None,
    )
    messages = [_format_message(message) for message in response.get("messages", [])]
    return {
        "success": True,
        "channel_id": channel_id,
        "messages": messages,
        "has_more": bool(response.get("has_more")),
    }


def _read_thread(args: dict[str, Any], client: Any) -> dict[str, Any]:
    channel_ref = str(args["channel_ref"]).strip()
    thread_ts = str(args["thread_ts"]).strip()
    channel_id = _resolve_channel_id(client, channel_ref)
    limit = max(1, min(int(args.get("limit", 50)), 100))
    response = client.conversations_replies(channel=channel_id, ts=thread_ts, limit=limit)
    messages = [_format_message(message) for message in response.get("messages", [])]
    return {
        "success": True,
        "channel_id": channel_id,
        "thread_ts": thread_ts,
        "messages": messages,
        "has_more": bool(response.get("has_more")),
    }


def _search_messages(args: dict[str, Any], client: Any) -> dict[str, Any]:
    query = str(args["query"]).strip()
    limit = max(1, min(int(args.get("limit", 20)), 50))
    response = client.search_messages(query=query, count=limit)
    matches = ((response.get("messages") or {}).get("matches")) or []
    rows = []
    for match in matches[:limit]:
        rows.append(
            {
                "channel_id": str(((match.get("channel") or {}).get("id")) or ""),
                "channel_name": str(((match.get("channel") or {}).get("name")) or ""),
                "user": str(match.get("user", "")),
                "username": str(match.get("username", "")),
                "ts": str(match.get("ts", "")),
                "text": str(match.get("text", "")),
                "permalink": str(match.get("permalink", "")),
            }
        )
    return {"success": True, "query": query, "matches": rows, "count": len(rows)}


def _list_recent_participants(args: dict[str, Any], client: Any) -> dict[str, Any]:
    channel_ref = str(args["channel_ref"]).strip()
    channel_id = _resolve_channel_id(client, channel_ref)
    limit = max(1, min(int(args.get("limit", 30)), 200))
    response = client.conversations_history(channel=channel_id, limit=limit)
    messages = response.get("messages", []) or []

    user_ids: list[str] = []
    for message in messages:
        user_id = str(message.get("user", "")).strip()
        if not user_id or user_id in user_ids:
            continue
        user_ids.append(user_id)

    users_by_id = {
        str(member.get("id", "")): member
        for member in _iter_users(client)
        if str(member.get("id", "")).strip()
    }

    participants = []
    for user_id in user_ids:
        member = users_by_id.get(user_id, {})
        profile = member.get("profile") or {}
        participants.append(
            {
                "id": user_id,
                "name": str(member.get("name", "")),
                "display_name": str(profile.get("display_name") or profile.get("display_name_normalized") or ""),
                "real_name": str(profile.get("real_name") or profile.get("real_name_normalized") or ""),
            }
        )

    return {
        "success": True,
        "channel_id": channel_id,
        "lookback_messages": len(messages),
        "participants": participants,
        "count": len(participants),
    }


def build_slack_retrieve_tool_specs(*, client_factory: SlackClientFactory | None = None) -> list[McpToolSpec]:
    factory = client_factory or _default_client_factory()

    def wrap(handler: Callable[[dict[str, Any], Any], dict[str, Any]]):
        return lambda args: _make_result(handler, args, factory)

    return [
        McpToolSpec(
            name="slack_list_channels",
            description="List readable Slack channels using the separate Slack Retrieve token. Use this for retrieval and discovery, not for delivery.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Optional case-insensitive channel name filter."},
                    "limit": {"type": "integer", "description": "Maximum number of channels to return. Default 50."},
                },
            },
            handler=wrap(_list_channels),
        ),
        McpToolSpec(
            name="slack_list_users",
            description="List Slack users visible to the separate Slack Retrieve token. Use this to understand workspace identities before retrieval.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Optional case-insensitive user filter."},
                    "limit": {"type": "integer", "description": "Maximum number of users to return. Default 50."},
                },
            },
            handler=wrap(_list_users),
        ),
        McpToolSpec(
            name="slack_read_channel_history",
            description="Read recent messages from a Slack channel using the retrieval token. Accepts channel ID, #channel-name, or <#CHANNEL|name>.",
            input_schema={
                "type": "object",
                "properties": {
                    "channel_ref": {"type": "string", "description": "Channel ID, #channel-name, or Slack channel mention token."},
                    "limit": {"type": "integer", "description": "Maximum messages to return. Default 20."},
                    "oldest": {"type": "string", "description": "Optional oldest Slack timestamp boundary.", "optional": True},
                    "latest": {"type": "string", "description": "Optional latest Slack timestamp boundary.", "optional": True},
                },
                "required": ["channel_ref"],
            },
            handler=wrap(_read_channel_history),
        ),
        McpToolSpec(
            name="slack_read_thread",
            description="Read a Slack thread using the retrieval token. Accepts channel ID or name plus thread timestamp.",
            input_schema={
                "type": "object",
                "properties": {
                    "channel_ref": {"type": "string", "description": "Channel ID, #channel-name, or Slack channel mention token."},
                    "thread_ts": {"type": "string", "description": "Slack thread timestamp."},
                    "limit": {"type": "integer", "description": "Maximum messages to return. Default 50."},
                },
                "required": ["channel_ref", "thread_ts"],
            },
            handler=wrap(_read_thread),
        ),
        McpToolSpec(
            name="slack_search_messages",
            description="Search Slack messages with the retrieval token. Use this for workspace-wide lookup instead of asking someone to resend context. For reliable search, configure a Slack user token with search scopes.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Slack search query string."},
                    "limit": {"type": "integer", "description": "Maximum number of search matches to return. Default 20."},
                },
                "required": ["query"],
            },
            handler=wrap(_search_messages),
        ),
        McpToolSpec(
            name="slack_list_recent_participants",
            description="List unique recent message participants from a Slack channel using the retrieval token. Use this when the user asks who has been active in a channel over the last N messages.",
            input_schema={
                "type": "object",
                "properties": {
                    "channel_ref": {"type": "string", "description": "Channel ID, #channel-name, #CHANNEL_ID, or Slack channel mention token."},
                    "limit": {"type": "integer", "description": "How many recent messages to inspect before deduplicating participants. Default 30."},
                },
                "required": ["channel_ref"],
            },
            handler=wrap(_list_recent_participants),
        ),
    ]
