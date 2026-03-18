from __future__ import annotations

import json
from typing import Any

from krim_sdk.tools import Tool

from kiraclaw_agentd.memory_retriever import MemoryRetriever
from kiraclaw_agentd.memory_saver import MemorySaver
from kiraclaw_agentd.memory_store import MemoryStore
from kiraclaw_agentd.settings import KiraClawSettings


def _build_result(success: bool, **payload: Any) -> str:
    return json.dumps({"success": success, **payload}, ensure_ascii=False, indent=2)


def _parse_tags(raw_tags: str | None) -> list[str]:
    if not raw_tags:
        return []
    return [part.strip() for part in str(raw_tags).split(",") if part.strip()]


def _normalize_metadata(
    defaults: dict[str, Any],
    *,
    user_id: str | None = None,
    user_name: str | None = None,
    channel_id: str | None = None,
) -> dict[str, Any]:
    metadata = dict(defaults)
    if user_id is not None:
        metadata["user"] = user_id
    if user_name is not None:
        metadata["user_name"] = user_name
    if channel_id is not None:
        metadata["channel"] = channel_id
    metadata.setdefault("source", "memory-tool")
    return metadata


class MemorySearchTool(Tool):
    name = "memory_search"
    description = (
        "Search long-term memory stored under Filesystem Base Dir/memories. "
        "Use this when the user explicitly asks to inspect, search, or review saved memory, "
        "or when you need additional memory context before answering an ongoing conversation."
    )
    parameters = {
        "query": {
            "type": "string",
            "description": "What to search for in long-term memory.",
        },
        "session_id": {
            "type": "string",
            "description": "Optional session scope to bias memory search toward the current conversation.",
            "optional": True,
        },
        "user_id": {
            "type": "string",
            "description": "Optional user ID to bias memory search toward one user.",
            "optional": True,
        },
        "user_name": {
            "type": "string",
            "description": "Optional user name to bias memory search toward one user.",
            "optional": True,
        },
        "channel_id": {
            "type": "string",
            "description": "Optional channel or chat ID to bias memory search toward one conversation.",
            "optional": True,
        },
    }

    def __init__(self, retriever: MemoryRetriever, tool_context: dict[str, Any] | None = None) -> None:
        self._retriever = retriever
        self._tool_context = dict(tool_context or {})

    def run(
        self,
        query: str,
        session_id: str | None = None,
        user_id: str | None = None,
        user_name: str | None = None,
        channel_id: str | None = None,
    ) -> str:
        session_value = str(session_id or self._tool_context.get("session_id") or "").strip()
        metadata = _normalize_metadata(
            self._tool_context,
            user_id=user_id,
            user_name=user_name,
            channel_id=channel_id,
        )
        entries = self._retriever.search(query, session_value, metadata)
        return _build_result(
            True,
            query=query,
            session_id=session_value,
            count=len(entries),
            entries=entries,
        )


class MemoryIndexSearchTool(Tool):
    name = "memory_index_search"
    description = (
        "Search the structured memory index under Filesystem Base Dir/memories/index.json. "
        "Use this to find relevant memory files before reading, editing, or deleting them."
    )
    parameters = {
        "query": {
            "type": "string",
            "description": "What to search for in the memory index.",
        },
        "session_id": {
            "type": "string",
            "description": "Optional session scope to bias the search toward the current conversation.",
            "optional": True,
        },
        "user_id": {
            "type": "string",
            "description": "Optional user ID to bias the search toward one user.",
            "optional": True,
        },
        "user_name": {
            "type": "string",
            "description": "Optional user name to bias the search toward one user.",
            "optional": True,
        },
        "channel_id": {
            "type": "string",
            "description": "Optional channel or chat ID to bias the search toward one conversation.",
            "optional": True,
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of index matches to return.",
            "optional": True,
        },
    }

    def __init__(self, retriever: MemoryRetriever, tool_context: dict[str, Any] | None = None) -> None:
        self._retriever = retriever
        self._tool_context = dict(tool_context or {})

    def run(
        self,
        query: str,
        session_id: str | None = None,
        user_id: str | None = None,
        user_name: str | None = None,
        channel_id: str | None = None,
        limit: int | None = None,
    ) -> str:
        session_value = str(session_id or self._tool_context.get("session_id") or "").strip()
        metadata = _normalize_metadata(
            self._tool_context,
            user_id=user_id,
            user_name=user_name,
            channel_id=channel_id,
        )
        rows = self._retriever.search_index(query, session_value, metadata, limit=max(1, int(limit or 8)))
        return _build_result(
            True,
            query=query,
            session_id=session_value,
            count=len(rows),
            entries=rows,
        )


class MemorySaveTool(Tool):
    name = "memory_save"
    description = (
        "Persist a durable fact or note into Filesystem Base Dir/memories. "
        "Use this when the user explicitly asks to remember, save, or record something, "
        "or when a turn reveals a durable fact, preference, project state, or follow-up worth keeping."
    )
    parameters = {
        "note": {
            "type": "string",
            "description": "The durable fact, summary, or note to save into long-term memory.",
        },
        "session_id": {
            "type": "string",
            "description": "Optional session scope to save this note under.",
            "optional": True,
        },
        "user_id": {
            "type": "string",
            "description": "Optional user ID to associate with this note.",
            "optional": True,
        },
        "user_name": {
            "type": "string",
            "description": "Optional user name to associate with this note.",
            "optional": True,
        },
        "channel_id": {
            "type": "string",
            "description": "Optional channel or chat ID to associate with this note.",
            "optional": True,
        },
    }

    def __init__(self, saver: MemorySaver, tool_context: dict[str, Any] | None = None) -> None:
        self._saver = saver
        self._tool_context = dict(tool_context or {})

    def run(
        self,
        note: str,
        session_id: str | None = None,
        user_id: str | None = None,
        user_name: str | None = None,
        channel_id: str | None = None,
    ) -> str:
        session_value = str(session_id or self._tool_context.get("session_id") or "manual:memory").strip()
        metadata = _normalize_metadata(
            self._tool_context,
            user_id=user_id,
            user_name=user_name,
            channel_id=channel_id,
        )
        saved_paths = self._saver.save_note(session_value, note, metadata)
        return _build_result(
            True,
            session_id=session_value,
            saved_paths=saved_paths,
            count=len(saved_paths),
        )


class MemoryIndexSaveTool(Tool):
    name = "memory_index_save"
    description = (
        "Update the structured memory index after you create, edit, move, or delete a memory file. "
        "Use this to keep Filesystem Base Dir/memories/index.json in sync with actual memory files."
    )
    parameters = {
        "path": {
            "type": "string",
            "description": "Absolute or memories-relative path to the memory .md file.",
        },
        "summary": {
            "type": "string",
            "description": "Short summary for the memory index entry.",
        },
        "title": {
            "type": "string",
            "description": "Optional index title. Defaults to a title derived from the file path.",
            "optional": True,
        },
        "category": {
            "type": "string",
            "description": "Optional category. Defaults to the first path segment under memories.",
            "optional": True,
        },
        "tags": {
            "type": "string",
            "description": "Optional comma-separated tags for the index entry.",
            "optional": True,
        },
        "session_id": {
            "type": "string",
            "description": "Optional session scope to associate with this entry.",
            "optional": True,
        },
        "user_id": {
            "type": "string",
            "description": "Optional user ID to associate with this entry.",
            "optional": True,
        },
        "user_name": {
            "type": "string",
            "description": "Optional user name to associate with this entry.",
            "optional": True,
        },
        "channel_id": {
            "type": "string",
            "description": "Optional channel or chat ID to associate with this entry.",
            "optional": True,
        },
    }

    def __init__(self, saver: MemorySaver, tool_context: dict[str, Any] | None = None) -> None:
        self._saver = saver
        self._tool_context = dict(tool_context or {})

    def run(
        self,
        path: str,
        summary: str,
        title: str | None = None,
        category: str | None = None,
        tags: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        user_name: str | None = None,
        channel_id: str | None = None,
    ) -> str:
        metadata = _normalize_metadata(
            self._tool_context,
            user_id=user_id,
            user_name=user_name,
            channel_id=channel_id,
        )
        metadata["session_id"] = str(session_id or self._tool_context.get("session_id") or "").strip()
        entry = self._saver.save_index_entry(
            path=path,
            title=title,
            category=category,
            summary=summary,
            tags=_parse_tags(tags),
            metadata=metadata,
        )
        return _build_result(True, entry=entry)


def build_memory_tools(
    settings: KiraClawSettings,
    *,
    tool_context: dict[str, Any] | None = None,
) -> list[Tool]:
    if not settings.memory_enabled:
        return []

    store = MemoryStore(settings.memory_dir, settings.memory_index_file, settings.agent_name)
    store.ensure_structure()
    retriever = MemoryRetriever(store)
    saver = MemorySaver(store)
    return [
        MemoryIndexSearchTool(retriever, tool_context),
        MemoryIndexSaveTool(saver, tool_context),
        MemorySearchTool(retriever, tool_context),
        MemorySaveTool(saver, tool_context),
    ]
