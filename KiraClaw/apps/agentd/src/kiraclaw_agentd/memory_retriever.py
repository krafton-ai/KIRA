from __future__ import annotations

from typing import Any

from kiraclaw_agentd.memory_store import MemoryStore


class MemoryRetriever:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def build_context(
        self,
        prompt: str,
        session_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        return self.store.retrieve_context(prompt, session_id, metadata)

    def search(
        self,
        query: str,
        session_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self.store.search(query, session_id, metadata)

    def search_index(
        self,
        query: str,
        session_id: str,
        metadata: dict[str, Any] | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        return self.store.search_index(query, session_id, metadata, limit=limit)
